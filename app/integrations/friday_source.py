"""
FRIDAY Task Source & Webhook Integration for Project FORGE.
Enables deep integration with Project FRIDAY (orchestrator/manager):
- Custom logging correlation tags ([FRIDAY-TASK: <id>])
- Asynchronous webhook event publishing with exponential backoff
- Context retrieval for FRIDAY operators
"""

import asyncio
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("integrations.friday_source")


class FridayTaskContext(BaseModel):
    """Contextual metadata describing relationship between FORGE task and FRIDAY commands."""
    task_id: str
    goal: str
    source: str = "friday"
    priority: str = "normal"
    tags: List[str] = Field(default_factory=list)
    correlation_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    status: str = "PENDING"
    command_intent: str = "software_synthesis"
    last_notified_at: Optional[datetime] = None


class FridayWebhookPayload(BaseModel):
    """Structured telemetry event payload dispatched to FRIDAY webhook endpoint."""
    event_type: str  # task_started, stage_completed, verification_result, task_completed, task_failed
    task_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)


class FridaySourceManager:
    """Manages FRIDAY task identification, enhanced logging, and resilient webhook dispatching."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.settings: Settings = get_settings()
        self.base_url = (base_url or getattr(self.settings, "friday_base_url", "http://localhost:9000")).rstrip("/")
        self.api_key = api_key or getattr(self.settings, "friday_api_key", self.settings.ai_universe_api_key)

    def is_friday_task(self, task_metadata: Dict[str, Any]) -> bool:
        """Check if task originated from FRIDAY manager."""
        return task_metadata.get("source", "").lower() == "friday"

    def format_log_message(self, task_id: str, message: str) -> str:
        """Format log entry with FRIDAY correlation prefix."""
        return f"[FRIDAY-TASK: {task_id}] {message}"

    async def notify_event(
        self,
        task_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        Send asynchronous webhook notification to FRIDAY with exponential backoff.
        Fails gracefully without breaking task execution.
        """
        url = f"{self.base_url}/api/forge/events"
        payload = FridayWebhookPayload(
            event_type=event_type,
            task_id=task_id,
            data=data or {},
        ).model_dump(mode="json")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-FRIDAY-API-Key"] = self.api_key

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code in [200, 201, 202, 204]:
                        logger.info(self.format_log_message(task_id, f"Webhook event '{event_type}' delivered to FRIDAY (status={resp.status_code})"))
                        return True
                    else:
                        logger.warning(self.format_log_message(task_id, f"FRIDAY webhook returned status {resp.status_code} (attempt {attempt}/{max_retries})"))
            except Exception as e:
                logger.debug(self.format_log_message(task_id, f"FRIDAY webhook dispatch failed (attempt {attempt}/{max_retries}): {e}"))

            if attempt < max_retries:
                # Exponential backoff: 0.2s, 0.4s, 0.8s
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))

        logger.warning(self.format_log_message(task_id, f"Could not deliver webhook event '{event_type}' to FRIDAY after {max_retries} attempts (non-blocking)."))
        return False


friday_source_manager = FridaySourceManager()
