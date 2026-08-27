"""
Continuous Template Evolution & A/B Testing Engine for Project FORGE.
Tracks template efficacy, computes success scores from verification outcomes,
and evaluates template variants via A/B testing.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger("improvement.template_evolution")


class TemplateVariant(BaseModel):
    """A template component variant under evaluation."""
    name: str
    archetype: str  # website, cli, api, script
    code_pattern: str
    success_count: int = 0
    failure_count: int = 0
    total_evaluations: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_evaluations == 0:
            return 100.0
        return round((self.success_count / self.total_evaluations) * 100.0, 1)


class TemplateEvolutionEngine:
    """Manages template success tracking, pattern scoring, and variant promotion."""

    def __init__(self):
        self.variants: Dict[str, TemplateVariant] = {}
        self._initialize_default_variants()

    def _initialize_default_variants(self):
        """Seed initial template variants for A/B tracking."""
        self.register_variant(
            name="css_flexbox_base",
            archetype="website",
            code_pattern="display: flex; justify-content: space-between;",
        )
        self.register_variant(
            name="css_grid_base",
            archetype="website",
            code_pattern="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));",
        )
        self.register_variant(
            name="fastapi_in_memory_crud",
            archetype="api",
            code_pattern="ITEMS_DB: Dict[int, Item] = {}",
        )
        self.register_variant(
            name="fastapi_sqlite_crud",
            archetype="api",
            code_pattern="CREATE TABLE IF NOT EXISTS items",
        )

    def register_variant(self, name: str, archetype: str, code_pattern: str) -> TemplateVariant:
        """Register a new template pattern variant."""
        var = TemplateVariant(
            name=name,
            archetype=archetype,
            code_pattern=code_pattern,
        )
        self.variants[name] = var
        return var

    def record_outcome(self, variant_name: str, passed_verification: bool):
        """Record verification outcome for a template variant."""
        var = self.variants.get(variant_name)
        if not var:
            return
        var.total_evaluations += 1
        if passed_verification:
            var.success_count += 1
        else:
            var.failure_count += 1
        logger.debug(f"Template variant '{variant_name}' updated: {var.success_rate}% success ({var.total_evaluations} runs)")

    def get_winning_variant(self, archetype: str) -> Optional[TemplateVariant]:
        """Select the highest scoring template variant for an archetype."""
        candidates = [v for v in self.variants.values() if v.archetype == archetype]
        if not candidates:
            return None
        evaluated = [v for v in candidates if v.total_evaluations > 0]
        if evaluated:
            return max(evaluated, key=lambda v: (v.success_rate, v.total_evaluations))
        return candidates[0]

    def evaluate_ab_variants(self, variant_a: str, variant_b: str) -> Dict[str, Any]:
        """Compare two template variants side-by-side."""
        va = self.variants.get(variant_a)
        vb = self.variants.get(variant_b)
        if not va or not vb:
            return {"error": "One or both variants not found"}

        winner = va.name if va.success_rate >= vb.success_rate else vb.name
        return {
            "variant_a": {"name": va.name, "success_rate": va.success_rate, "runs": va.total_evaluations},
            "variant_b": {"name": vb.name, "success_rate": vb.success_rate, "runs": vb.total_evaluations},
            "promoted_winner": winner,
        }


template_evolution_engine = TemplateEvolutionEngine()
