"""Consumer-agnostic webhook delivery with bounded retries and safe diagnostics."""

from __future__ import annotations

import asyncio
import ipaddress
import math
import random
import socket
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger("api.webhooks")

_DEFAULT_TIMEOUT_SECONDS = 3.0
_BASE_RETRY_DELAY_SECONDS = 0.2
_MAX_RETRY_DELAY_SECONDS = 5.0
_MAX_RETRY_AFTER_SECONDS = 10.0
_MAX_ATTEMPTS = 8
_TRANSIENT_STATUS_CODES = {408, 425, 429}


class GenericWebhookPayload(BaseModel):
    """Standardized webhook payload emitted to optional task-provided webhook URLs."""

    event: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    task_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    source: str = "forge"


def _validated_webhook_target(webhook_url: str) -> tuple[str, int] | None:
    """Return an HTTP(S) host/port, rejecting URL credentials and malformed authorities."""
    try:
        parsed = urlsplit(webhook_url)
        # Accessing .port validates malformed port strings and bracketed IPv6 forms.
        explicit_port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    default_port = 443 if parsed.scheme.lower() == "https" else 80
    port = explicit_port if explicit_port is not None else default_port
    if not 1 <= port <= 65535:
        return None
    return parsed.hostname, port


def _is_public_address(address: str) -> bool:
    """Allow globally routable IPs only; exclude private, shared, loopback and special-use ranges."""
    try:
        parsed = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    return parsed.is_global and not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


async def _lookup_webhook_addresses(host: str, port: int) -> list[tuple]:
    """Resolve a webhook host through the current event loop's resolver."""
    return await asyncio.get_running_loop().getaddrinfo(
        host, port, type=socket.SOCK_STREAM
    )


async def _resolve_public_webhook_target(host: str, port: int) -> bool:
    """Reject callback targets whose literal or DNS-resolved addresses are not public.

    All DNS answers must be public; a mixed public/private answer is rejected rather than
    trusting the resolver's first result. This is a defense-in-depth check. It is not a
    complete DNS-rebinding defense because HTTPX performs its own connection-time lookup.
    """
    if host.lower().rstrip(".") == "localhost" or host.lower().endswith(".localhost"):
        return False
    if host.lower().endswith(".local"):
        return False

    try:
        ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        try:
            records = await _lookup_webhook_addresses(host, port)
        except (OSError, UnicodeError, ValueError):
            return False
        addresses = {record[4][0] for record in records if record and record[4]}
        if not addresses:
            return False
        return all(_is_public_address(address) for address in addresses)
    else:
        return _is_public_address(host)


def _retry_after_seconds(value: str | None) -> float | None:
    """Parse Retry-After seconds or an HTTP date, capping server-directed waits."""
    if not value:
        return None
    try:
        seconds = float(value)
    except (OverflowError, ValueError):
        seconds = math.nan
    if math.isfinite(seconds) and seconds >= 0:
        return min(seconds, _MAX_RETRY_AFTER_SECONDS)

    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=UTC)
    delay = (retry_at - datetime.now(UTC)).total_seconds()
    return min(max(delay, 0.0), _MAX_RETRY_AFTER_SECONDS)


def _retry_delay(attempt: int, retry_after: float | None = None) -> float:
    """Return capped exponential backoff with bounded positive jitter."""
    if retry_after is not None:
        return min(retry_after, _MAX_RETRY_AFTER_SECONDS)
    base = min(
        _BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)),
        _MAX_RETRY_DELAY_SECONDS,
    )
    return base + random.uniform(0.0, base * 0.25)


class WebhookDispatcher:
    """Dispatch lifecycle notifications without blocking task completion on receiver outages.

    `max_retries` is the maximum number of delivery attempts (kept as the public
    parameter name for compatibility). Only transient HTTP responses and transport
    errors are retried; permanent client errors fail fast.
    """

    @classmethod
    async def dispatch_event(
        cls,
        webhook_url: str | None,
        task_id: str,
        event: str,
        data: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> bool:
        """Send an event and return whether the receiver accepted it."""
        if (
            isinstance(max_retries, bool)
            or not isinstance(max_retries, int)
            or not 1 <= max_retries <= _MAX_ATTEMPTS
        ):
            raise ValueError(f"max_retries must be an integer between 1 and {_MAX_ATTEMPTS}")

        if not webhook_url:
            return False
        target = _validated_webhook_target(webhook_url)
        if target is None:
            return False
        host, port = target
        try:
            target_is_public = await _resolve_public_webhook_target(host, port)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "Webhook target validation failed host=%s error_type=%s",
                host,
                type(exc).__name__,
            )
            return False
        if not target_is_public:
            logger.warning("Webhook target rejected host=%s: target is not globally routable", host)
            return False

        payload = GenericWebhookPayload(
            event=event,
            task_id=task_id,
            data=data or {},
        ).model_dump(mode="json")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Project-FORGE-Webhook/1.0",
        }

        try:
            async with httpx.AsyncClient(
                timeout=_DEFAULT_TIMEOUT_SECONDS,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                for attempt in range(1, max_retries + 1):
                    retry_after: float | None = None
                    try:
                        response = await client.post(webhook_url, json=payload, headers=headers)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        # Do not log exception text: HTTP client errors can include
                        # credentials, query tokens, paths or other URL data.
                        logger.debug(
                            "Webhook transport failed host=%s event=%s task=%s "
                            "attempt=%s/%s error_type=%s",
                            host,
                            event,
                            task_id,
                            attempt,
                            max_retries,
                            type(exc).__name__,
                        )
                    else:
                        if 200 <= response.status_code < 300:
                            logger.info(
                                "Webhook accepted host=%s event=%s task=%s status=%s",
                                host,
                                event,
                                task_id,
                                response.status_code,
                            )
                            return True

                        retryable = (
                            response.status_code in _TRANSIENT_STATUS_CODES
                            or response.status_code >= 500
                        )
                        if not retryable:
                            logger.warning(
                                "Webhook rejected host=%s event=%s task=%s status=%s; "
                                "not retrying permanent response",
                                host,
                                event,
                                task_id,
                                response.status_code,
                            )
                            return False

                        retry_after = _retry_after_seconds(
                            response.headers.get("Retry-After")
                        )
                        logger.warning(
                            "Webhook transient response host=%s event=%s task=%s "
                            "status=%s attempt=%s/%s",
                            host,
                            event,
                            task_id,
                            response.status_code,
                            attempt,
                            max_retries,
                        )

                    if attempt < max_retries:
                        await asyncio.sleep(_retry_delay(attempt, retry_after))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # The caller's build pipeline must not fail because the webhook client
            # itself could not be initialized or closed. Log only the exception type.
            logger.warning(
                "Webhook delivery aborted host=%s event=%s task=%s error_type=%s",
                host,
                event,
                task_id,
                type(exc).__name__,
            )
            return False

        logger.warning(
            "Webhook delivery exhausted host=%s event=%s task=%s attempts=%s",
            host,
            event,
            task_id,
            max_retries,
        )
        return False


webhook_dispatcher = WebhookDispatcher()
