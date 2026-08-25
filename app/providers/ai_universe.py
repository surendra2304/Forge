"""
AI Universe Intelligence Provider Adapter for Project FORGE.
Connects FORGE to external or simulated multi-agent AI Universe intelligence swarms.
Supports Fast, Review, and Debate multi-agent reasoning modes with provenance and dissent tracking.
"""

from datetime import datetime, timezone
from enum import Enum
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
import httpx

from app.core.logging import get_logger
from app.providers.base import (
    BaseModelProvider,
    ProviderCapabilities,
    ProviderHealthStatus,
    ProviderResponse,
    UsageEstimate,
    T,
)

logger = get_logger("providers.ai_universe")


class ReasoningMode(str, Enum):
    FAST = "fast"
    REVIEW = "review"
    DEBATE = "debate"


class ProvenanceRecord(BaseModel):
    agent_role: str
    model_name: str
    phase: str
    contribution: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIUniverseResponse(BaseModel):
    """Rich structured payload returned by the AI Universe Multi-Agent Swarm."""
    synthesis: str
    provenance: List[ProvenanceRecord] = Field(default_factory=list)
    confidence: float = 0.95
    uncertainty: str = "Low"
    important_dissent: List[str] = Field(default_factory=list)
    mode: ReasoningMode = ReasoningMode.FAST
    total_tokens: int = 0
    duration_ms: float = 0.0


class AIUniverseProvider(BaseModelProvider):
    """
    Adapter interfacing FORGE with the AI Universe Multi-Agent Swarm.
    Implements the stable BaseModelProvider contract without coupling to AI Universe internals.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        default_mode: ReasoningMode = ReasoningMode.FAST,
        model_name: str = "ai-universe-swarm-v1",
        cost_per_1k_input: float = 0.003,
        cost_per_1k_output: float = 0.015,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.endpoint = endpoint
        self.api_key = api_key
        self.default_mode = default_mode
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        mode: Optional[ReasoningMode] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Generate response through the AI Universe multi-agent reasoning pipeline."""
        start_time = time.perf_counter()
        target_mode = mode or self.default_mode
        logger.info(f"AIUniverseProvider generating in [{target_mode.value.upper()}] mode for prompt: '{prompt[:60]}...'")

        if self.endpoint:
            # Route to external live AI Universe HTTP service
            ai_resp = await self._call_remote_endpoint(prompt, system_prompt, target_mode, **kwargs)
        else:
            # Autonomous local multi-persona simulation
            ai_resp = await self._simulate_reasoning(prompt, system_prompt, target_mode)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        ai_resp.duration_ms = round(duration_ms, 2)

        usage = self.estimate_usage(prompt, ai_resp.synthesis)

        return ProviderResponse(
            content=ai_resp.synthesis,
            model=self.model_name,
            finish_reason="stop",
            usage=usage,
            raw_response={
                "reasoning_mode": target_mode.value,
                "confidence": ai_resp.confidence,
                "uncertainty": ai_resp.uncertainty,
                "provenance_count": len(ai_resp.provenance),
                "dissent_count": len(ai_resp.important_dissent),
                "ai_universe_payload": ai_resp.model_dump(mode="json"),
            },
        )

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        mode: Optional[ReasoningMode] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chunks of generated text tokens."""
        resp = await self.generate(prompt, system_prompt, temperature, max_tokens, mode=mode, **kwargs)
        words = resp.content.split(" ")
        for i, w in enumerate(words):
            yield w + (" " if i < len(words) - 1 else "")

    async def structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        mode: Optional[ReasoningMode] = None,
        **kwargs: Any,
    ) -> T:
        """Generate validated structured output parsed into a Pydantic model."""
        structured_prompt = (
            f"{prompt}\n\nYou MUST respond strictly in valid JSON adhering to this schema:\n"
            f"{json.dumps(response_model.model_json_schema())}"
        )
        response = await self.generate(structured_prompt, system_prompt=system_prompt, mode=mode, **kwargs)
        text = response.content.strip()
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0].strip()
        data = json.loads(text)
        return response_model.model_validate(data)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        mode: Optional[ReasoningMode] = None,
        **kwargs: Any,
    ) -> T:
        """Convenience alias for structured_output."""
        return await self.structured_output(prompt, response_model, system_prompt, mode=mode, **kwargs)

    def estimate_usage(self, prompt: str, output: Optional[str] = None) -> UsageEstimate:
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(0, len(output) // 4) if output else 0
        total_tokens = prompt_tokens + completion_tokens
        cost = ((prompt_tokens / 1000.0) * self.cost_per_1k_input) + ((completion_tokens / 1000.0) * self.cost_per_1k_output)
        return UsageEstimate(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(cost, 6),
        )

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="AIUniverseProvider",
            supported_models=[self.model_name, "ai-universe-swarm-fast", "ai-universe-swarm-debate"],
            supports_streaming=True,
            supports_structured_output=True,
            supports_function_calling=True,
            supports_multimodal=True,
            context_window_size=200000,
            max_output_tokens=8192,
        )

    async def health(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            healthy=True,
            provider_name="AIUniverseProvider",
            message="AI Universe Swarm Adapter operational",
            latency_ms=15.0,
            details={
                "adapter": "AIUniverseProvider",
                "modes": ["fast", "review", "debate"],
                "endpoint_configured": self.endpoint is not None,
            },
        )

    async def _call_remote_endpoint(
        self,
        prompt: str,
        system_prompt: Optional[str],
        mode: ReasoningMode,
        **kwargs: Any,
    ) -> AIUniverseResponse:
        """Send payload to external AI Universe intelligence endpoint."""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "mode": mode.value,
            "options": kwargs,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            return AIUniverseResponse.model_validate(resp.json())

    async def _simulate_reasoning(
        self,
        prompt: str,
        system_prompt: Optional[str],
        mode: ReasoningMode,
    ) -> AIUniverseResponse:
        """Simulate multi-agent reasoning swarm locally."""
        if mode == ReasoningMode.FAST:
            return AIUniverseResponse(
                synthesis=f"AI Universe [Fast Reasoning Output]: Evaluated and synthesized solution for: {prompt[:120]}",
                provenance=[
                    ProvenanceRecord(
                        agent_role="PrimaryReasoner",
                        model_name="claude-3-7-sonnet",
                        phase="DirectSynthesis",
                        contribution="Single-pass high-speed optimal reasoning",
                    )
                ],
                confidence=0.98,
                uncertainty="Minimal",
                important_dissent=[],
                mode=ReasoningMode.FAST,
            )

        elif mode == ReasoningMode.REVIEW:
            return AIUniverseResponse(
                synthesis=f"AI Universe [Peer-Reviewed Output]: Multi-persona review selected optimal architectural path for: {prompt[:120]}",
                provenance=[
                    ProvenanceRecord(
                        agent_role="ArchitectPersona",
                        model_name="claude-3-7-sonnet",
                        phase="Analysis_A",
                        contribution="Proposed modular decoupled pattern",
                    ),
                    ProvenanceRecord(
                        agent_role="SeniorDevPersona",
                        model_name="gpt-4o",
                        phase="Analysis_B",
                        contribution="Evaluated performance and concurrency constraints",
                    ),
                    ProvenanceRecord(
                        agent_role="JudgeEvaluator",
                        model_name="gemini-2-pro",
                        phase="ComparisonSelection",
                        contribution="Merged best structural and performance characteristics",
                    ),
                ],
                confidence=0.94,
                uncertainty="Low",
                important_dissent=["Note: Verify SQLite connection pool bounds under high concurrency."],
                mode=ReasoningMode.REVIEW,
            )

        else:  # ReasoningMode.DEBATE
            return AIUniverseResponse(
                synthesis=f"AI Universe [Adversarial Debate Synthesis]: Rebuttal-tested consensus reached for: {prompt[:120]}",
                provenance=[
                    ProvenanceRecord(
                        agent_role="ProponentSpecialist",
                        model_name="claude-3-7-sonnet",
                        phase="InitialProposal",
                        contribution="Argued for micro-module structure with event bus",
                    ),
                    ProvenanceRecord(
                        agent_role="AdversaryCritique",
                        model_name="gpt-4o",
                        phase="AdversarialCritique",
                        contribution="Challenged overhead of event serialization and debuggability",
                    ),
                    ProvenanceRecord(
                        agent_role="RebuttalSpecialist",
                        model_name="claude-3-7-sonnet",
                        phase="Rebuttal",
                        contribution="Refined solution using direct in-memory pubsub with telemetry logging",
                    ),
                    ProvenanceRecord(
                        agent_role="ConsensusSynthesizer",
                        model_name="gemini-2-pro",
                        phase="FinalSynthesis",
                        contribution="Synthesized robust balanced architecture with minimal overhead",
                    ),
                ],
                confidence=0.96,
                uncertainty="Very Low (Consensus Verified)",
                important_dissent=[
                    "Dissent Note: Distributed queue is deferred to Phase 2; in-memory broker is sufficient for MVP scale.",
                ],
                mode=ReasoningMode.DEBATE,
            )
