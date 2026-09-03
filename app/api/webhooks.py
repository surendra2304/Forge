"""
Generic Consumer-Agnostic Webhook Subsystem for Project FORGE.
Dispatches progress and lifecycle notifications only when a task provides an optional webhook_url.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger("api.webhooks")


class GenericWebhookPayload(BaseModel):
    """Standardized webhook payload emitted to optional task-provided webhook URLs."""

    event: str  # task_started, stage_completed, verification_result, task_completed, task_failed
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    task_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    source: str = "forge"


class WebhookDispatcher:
    """Dispatches webhook events to caller-specified URLs with retry and exponential backoff."""

    @classmethod
    async def dispatch_event(
        cls,
        webhook_url: str | None,
        task_id: str,
        event: str,
        data: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> bool:
        """
        Send event payload to webhook_url if provided.
        Fails gracefully without interrupting task synthesis or build pipelines.
        """
        if not webhook_url or not webhook_url.startswith(("http://", "https://")):
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

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(webhook_url, json=payload, headers=headers)
                    if resp.status_code in [200, 201, 202, 204]:
                        logger.info(
                            f"Webhook event '{event}' dispatched successfully to {webhook_url} (task={task_id})"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Webhook to {webhook_url} returned status {resp.status_code} (attempt {attempt}/{max_retries})"
                        )
            except Exception as e:
                logger.debug(f"Webhook dispatch failed (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))

        logger.warning(
            f"Could not deliver webhook event '{event}' for task '{task_id}' to {webhook_url} after {max_retries} attempts."
        )
        return False


webhook_dispatcher = WebhookDispatcher()
