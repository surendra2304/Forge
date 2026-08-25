"""
Task Analyzer for Project FORGE.
Evaluates high-level goals and requirements to extract technical domain, language stack, and complexity.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.providers.base import BaseModelProvider
from app.providers.direct import DirectProvider

logger = get_logger("core.analyzer")


class TaskAnalysisResult(BaseModel):
    goal_summary: str
    detected_domain: str = "Software Engineering"
    primary_language: str = "Python"
    estimated_complexity: str = "medium"  # low, medium, high, critical
    recommended_mode: str = "autonomous"
    key_constraints: List[str] = Field(default_factory=list)
    suggested_milestones: List[str] = Field(default_factory=list)


class TaskAnalyzer:
    """Intakes goals and requirements to produce a structured TaskAnalysisResult."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        self.provider = provider or DirectProvider(model_name="direct-analyzer")

    async def analyze(self, goal: str, requirements: Optional[List[str]] = None) -> TaskAnalysisResult:
        """Perform static and heuristic analysis on input goal and requirements."""
        req_list = requirements or []
        logger.info(f"Analyzing task goal: '{goal[:80]}...' with {len(req_list)} explicit requirements")

        # Detect primary language
        text = f"{goal} {' '.join(req_list)}".lower()
        primary_lang = "Python"
        if "typescript" in text or "react" in text or "next.js" in text:
            primary_lang = "TypeScript"
        elif "javascript" in text or "node" in text:
            primary_lang = "JavaScript"
        elif "rust" in text or "cargo" in text:
            primary_lang = "Rust"
        elif "golang" in text or "go " in text:
            primary_lang = "Go"

        complexity = "medium"
        if len(req_list) > 5 or "distributed" in text or "microservice" in text:
            complexity = "high"
        elif len(req_list) <= 1 and len(goal.split()) < 10:
            complexity = "low"

        return TaskAnalysisResult(
            goal_summary=goal.strip(),
            detected_domain="Full-Stack Engineering" if "frontend" in text and "backend" in text else "Software Engineering",
            primary_language=primary_lang,
            estimated_complexity=complexity,
            key_constraints=req_list,
            suggested_milestones=[
                "Requirements Specification",
                "Architecture Design",
                "Implementation",
                "Verification Gate",
                "Security Review Gate",
                "Release Package",
            ],
        )


task_analyzer = TaskAnalyzer()
