"""
Unit tests for AIUniverseProvider Intelligence Adapter.
"""

from typing import List
from pydantic import BaseModel
import pytest
from app.providers.ai_universe import (
    AIUniverseProvider,
    AIUniverseResponse,
    ReasoningMode,
)


@pytest.mark.asyncio
async def test_ai_universe_provider_fast_mode():
    provider = AIUniverseProvider(default_mode=ReasoningMode.FAST)
    resp = await provider.generate("Synthesize an optimized binary search function")

    assert resp.content is not None
    assert "Fast Reasoning Output" in resp.content
    assert resp.raw_response["reasoning_mode"] == "fast"
    assert resp.raw_response["confidence"] >= 0.9
    assert resp.raw_response["provenance_count"] == 1


@pytest.mark.asyncio
async def test_ai_universe_provider_review_mode():
    provider = AIUniverseProvider(default_mode=ReasoningMode.REVIEW)
    resp = await provider.generate("Design distributed cache invalidation strategy")

    assert "Peer-Reviewed Output" in resp.content
    assert resp.raw_response["reasoning_mode"] == "review"
    assert resp.raw_response["provenance_count"] >= 2
    assert "ai_universe_payload" in resp.raw_response

    payload = resp.raw_response["ai_universe_payload"]
    roles = [p["agent_role"] for p in payload["provenance"]]
    assert "ArchitectPersona" in roles
    assert "SeniorDevPersona" in roles


@pytest.mark.asyncio
async def test_ai_universe_provider_debate_mode_with_dissent():
    provider = AIUniverseProvider(default_mode=ReasoningMode.DEBATE)
    resp = await provider.generate("Choose between Event Sourcing vs CQRS with RDBMS")

    assert "Adversarial Debate Synthesis" in resp.content
    assert resp.raw_response["reasoning_mode"] == "debate"
    assert resp.raw_response["provenance_count"] >= 3
    assert resp.raw_response["dissent_count"] >= 1

    payload = resp.raw_response["ai_universe_payload"]
    assert len(payload["important_dissent"]) >= 1
    assert "Dissent Note" in payload["important_dissent"][0]


@pytest.mark.asyncio
async def test_ai_universe_streaming_and_structured_generation():
    provider = AIUniverseProvider()

    # 1. Test streaming
    tokens = []
    async for tok in provider.stream("Stream this reasoning prompt"):
        tokens.append(tok)
    assert len(tokens) >= 3

    # 2. Test structured generation
    class ModuleSchema(BaseModel):
        module_name: str
        functions: List[str]
        complexity: str

    mock_json_provider = AIUniverseProvider()
    # Override simulate for structured test
    orig_simulate = mock_json_provider._simulate_reasoning

    async def mock_sim(prompt, system_prompt, mode):
        res = await orig_simulate(prompt, system_prompt, mode)
        res.synthesis = '{"module_name": "auth_service", "functions": ["login", "signup"], "complexity": "medium"}'
        return res

    mock_json_provider._simulate_reasoning = mock_sim

    obj = await mock_json_provider.generate_structured("Generate auth module spec", ModuleSchema)
    assert isinstance(obj, ModuleSchema)
    assert obj.module_name == "auth_service"
    assert "login" in obj.functions
