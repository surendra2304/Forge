"""
Structured Event Emitter & Secret Redactor for Project FORGE.
Provides standardized telemetry and audit events for FRIDAY and AI Universe dashboards.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.memory.state_store import StateStore

logger = get_logger("core.events")


class SecretRedactor:
    """Recursively redacts sensitive keys, tokens, and credentials from telemetry payloads."""

    SENSITIVE_KEYS = {
        "key",
        "secret",
        "password",
        "token",
        "auth",
        "authorization",
        "bearer",
        "credential",
        "credentials",
    }

    TOKEN_PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),          # OpenAI / Anthropic-like keys
        re.compile(r"ghp_[a-zA-Z0-9]{20,}"),             # GitHub tokens
        re.compile(r"AIza[0-9A-Za-z\-_]{35}"),           # Google API keys
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+", re.I), # Bearer tokens
    ]

    @classmethod
    def redact_string(cls, value: str) -> str:
        """Scan string for regex token patterns and mask them."""
        redacted = value
        for pat in cls.TOKEN_PATTERNS:
            redacted = pat.sub("[REDACTED_TOKEN]", redacted)
        return redacted

    @classmethod
    def redact(cls, data: Any) -> Any:
        """Recursively redact dictionary or list payloads."""
        if isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                if any(s in k.lower() for s in cls.SENSITIVE_KEYS):
                    clean_dict[k] = "[REDACTED_SECRET]"
                else:
                    clean_dict[k] = cls.redact(v)
            return clean_dict
        elif isinstance(data, list):
            return [cls.redact(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_string(data)
        return data


class StructuredAuditEvent(BaseModel):
    """Rich structured telemetry event adhering to FORGE Master Observability Spec."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    stage: str = "Execution"
    agent_id: str = "orchestrator"
    provider_model: str = "direct-model"
    action: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    checkpoint_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventEmitter:
    """Emits redacted, structured telemetry events to the SQLite StateStore."""

    def __init__(self, store: Optional[StateStore] = None):
        self.store = store

    async def emit(
        self,
        task_id: str,
        action: str,
        stage: str = "Execution",
        agent_id: str = "orchestrator",
        provider_model: str = "direct-model",
        inputs: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        checkpoint_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> StructuredAuditEvent:
        """Create, redact, log, and persist a structured audit event."""
        clean_inputs = SecretRedactor.redact(inputs or {})
        clean_result = SecretRedactor.redact(result or {}) if result is not None else None

        event = StructuredAuditEvent(
            task_id=task_id,
            run_id=run_id or str(uuid4()),
            stage=stage,
            agent_id=agent_id,
            provider_model=provider_model,
            action=action,
            inputs=clean_inputs,
            result=clean_result,
            duration_ms=round(duration_ms, 2),
            checkpoint_id=checkpoint_id,
        )

        logger.info(f"[Timeline Event] task={task_id} action={action} stage={stage} agent={agent_id}")

        if self.store:
            # Store in state store
            await self.store.record_event(
                task_id=task_id,
                event_type=action,
                payload=event.model_dump(mode="json"),
            )

        return event


event_emitter = EventEmitter()
