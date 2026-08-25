"""
Failure Classifier for Project FORGE Recovery Subsystem.
Analyzes failed verification evidence, stack traces, and test output to classify root causes.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.verification.evidence import VerificationEvidence


class FailureClass(str, Enum):
    SYNTAX_ERROR = "syntax_error"
    DEPENDENCY_MISSING = "dependency_missing"
    LOGIC_BUG = "logic_bug"
    INTEGRATION_ERROR = "integration_error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    ENVIRONMENT_ERROR = "environment_error"
    UNKNOWN = "unknown"


class FailureDiagnosis(BaseModel):
    failure_class: FailureClass
    failing_file: Optional[str] = None
    failing_line: Optional[int] = None
    error_message: str
    stack_trace: Optional[str] = None
    suggested_strategy: str
    raw_evidence_summary: str = ""


class FailureClassifier:
    """Classifies verification errors into actionable failure classes and extracts stack frames."""

    def classify(self, evidence: VerificationEvidence) -> FailureDiagnosis:
        text = f"{evidence.stderr}\n{evidence.stdout}"

        # 1. Syntax Error check
        if "SyntaxError:" in text or "IndentationError:" in text or "TabError:" in text:
            file_match = re.search(r'File "([^"]+)", line (\d+)', text)
            msg_match = re.search(r'(SyntaxError|IndentationError|TabError): (.*)', text)
            return FailureDiagnosis(
                failure_class=FailureClass.SYNTAX_ERROR,
                failing_file=file_match.group(1) if file_match else None,
                failing_line=int(file_match.group(2)) if file_match else None,
                error_message=msg_match.group(0) if msg_match else "Syntax error detected",
                stack_trace=text,
                suggested_strategy="Inspect syntax error line and fix grammar, indentation, or unclosed delimiters.",
                raw_evidence_summary=text[:300],
            )

        # 2. Dependency Missing / Import Error
        if "ModuleNotFoundError:" in text or "ImportError:" in text or "No module named" in text:
            msg_match = re.search(r'(ModuleNotFoundError|ImportError): (.*)', text)
            return FailureDiagnosis(
                failure_class=FailureClass.DEPENDENCY_MISSING,
                error_message=msg_match.group(0) if msg_match else "Missing dependency or module",
                stack_trace=text,
                suggested_strategy="Add missing module or correct import path in project source.",
                raw_evidence_summary=text[:300],
            )

        # 3. Timeout Error
        if evidence.duration_ms > 30000 or "timed out" in text.lower() or "TimeoutError" in text:
            return FailureDiagnosis(
                failure_class=FailureClass.TIMEOUT,
                error_message="Execution timed out",
                stack_trace=text,
                suggested_strategy="Optimize slow loop or increase timeout boundary.",
                raw_evidence_summary=text[:300],
            )

        # 4. Permission Error
        if "PermissionError:" in text or "Access is denied" in text or "Security Violation" in text:
            return FailureDiagnosis(
                failure_class=FailureClass.PERMISSION_DENIED,
                error_message="Permission denied or sandbox violation",
                stack_trace=text,
                suggested_strategy="Verify file permissions and sandbox path constraints.",
                raw_evidence_summary=text[:300],
            )

        # 5. Logic Bug / Test Failure
        if "AssertionError" in text or "FAILED (" in text or "FAILED tests" in text or "FAILED" in text:
            file_match = re.search(r'([\w/\\._-]+\.py):(\d+): in ', text)
            return FailureDiagnosis(
                failure_class=FailureClass.LOGIC_BUG,
                failing_file=file_match.group(1) if file_match else None,
                failing_line=int(file_match.group(2)) if file_match else None,
                error_message="Assertion or logic check failure in test run",
                stack_trace=text,
                suggested_strategy="Adjust logic to satisfy expected assertion or fix boundary condition.",
                raw_evidence_summary=text[:300],
            )

        # Default fallback
        return FailureDiagnosis(
            failure_class=FailureClass.UNKNOWN,
            error_message=text[:120] if text.strip() else "Unknown verification failure",
            stack_trace=text,
            suggested_strategy="Perform deep diagnostic inspection using Debugger agent.",
            raw_evidence_summary=text[:300],
        )


failure_classifier = FailureClassifier()
