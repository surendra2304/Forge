"""
Verification Evidence and Report Models for Project FORGE.
Enforces the core principle: 'Evidence over model confidence'.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckCategory(str, Enum):
    BUILD = "build"
    LINT = "lint"
    TYPECHECK = "typecheck"
    TEST = "test"
    RUNTIME = "runtime"
    SECURITY = "security"


class VerificationEvidence(BaseModel):
    """Objective, verifiable artifact of a single verification check."""
    check_name: str = Field(..., description="Identifier for this check")
    category: CheckCategory = Field(..., description="Check category")
    command: Optional[str] = Field(default=None, description="Command executed if applicable")
    exit_code: int = Field(default=0, description="Process exit code")
    passed: bool = Field(default=True, description="Whether the check passed objectively")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    stdout: str = Field(default="", description="Captured stdout")
    stderr: str = Field(default="", description="Captured stderr")
    artifacts_inspected: List[str] = Field(default_factory=list, description="Files verified")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted error items or warnings")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationReport(BaseModel):
    """Consolidated verification battery report for a task."""
    task_id: str
    all_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    evidence: List[VerificationEvidence] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def failure_reasons(self) -> List[str]:
        """Extract high-level summaries of failed checks."""
        reasons = []
        for ev in self.evidence:
            if not ev.passed:
                msg = f"[{ev.category.value.upper()}] {ev.check_name}: exit={ev.exit_code}"
                if ev.stderr:
                    msg += f" - {ev.stderr.strip()[:120]}"
                reasons.append(msg)
        return reasons
