"""
Verification Evidence and Report Models for Project FORGE.
Enforces the core principle: 'Evidence over model confidence'.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CheckCategory(str, Enum):
    BUILD = "build"
    LINT = "lint"
    TYPECHECK = "typecheck"
    TEST = "test"
    RUNTIME = "runtime"
    SECURITY = "security"
    FEATURE = "feature"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ACCESSIBILITY = "accessibility"


class VerificationEvidence(BaseModel):
    """Objective, verifiable artifact of a single verification check."""
    check_name: str = Field(..., description="Identifier for this check")
    category: CheckCategory = Field(..., description="Check category")
    command: str | None = Field(default=None, description="Command executed if applicable")
    exit_code: int = Field(default=0, description="Process exit code")
    passed: bool = Field(default=True, description="Whether the check passed objectively")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    artifacts_inspected: list[str] = Field(default_factory=list, description="Files verified")
    issues: list[dict[str, Any]] = Field(default_factory=list, description="Extracted error items or warnings")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VerificationReport(BaseModel):
    """Consolidated verification battery report for a task."""
    task_id: str
    all_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    evidence: list[VerificationEvidence] = Field(default_factory=list)
    baseline_comparison: dict[str, Any] | None = Field(default=None, description="Pre/post baseline regression comparison")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def failure_reasons(self) -> list[str]:
        """Extract high-level summaries of failed checks."""
        reasons = []
        for ev in self.evidence:
            if not ev.passed:
                msg = f"[{ev.category.value.upper()}] {ev.check_name}: exit={ev.exit_code}"
                if ev.stderr:
                    msg += f" - {ev.stderr.strip()[:120]}"
                reasons.append(msg)
        return reasons
