"""
Abstract BaseModelProvider Interface for FORGE.
Defines the required contract for all LLM / Inference Providers.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class UsageEstimate(BaseModel):
    prompt_tokens: int = Field(default=0, description="Estimated or actual input tokens")
    completion_tokens: int = Field(default=0, description="Estimated or actual output tokens")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated USD cost")


class ProviderCapabilities(BaseModel):
    provider_name: str
    supported_models: List[str]
    supports_streaming: bool = True
    supports_structured_output: bool = True
    supports_function_calling: bool = True
    supports_multimodal: bool = False
    context_window_size: int = 128000
    max_output_tokens: int = 4096


class ProviderHealthStatus(BaseModel):
    healthy: bool
    provider_name: str
    message: str = "Provider operational"
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    content: str
    model: str
    finish_reason: str = "stop"
    usage: UsageEstimate = Field(default_factory=UsageEstimate)
    raw_response: Optional[Dict[str, Any]] = None


class BaseModelProvider(ABC):
    """Abstract base class for all FORGE model providers."""

    def __init__(self, model_name: Optional[str] = None, **kwargs):
        self.model_name = model_name or "default-model"
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate a complete text completion."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream chunks of generated text tokens."""
        pass

    @abstractmethod
    async def structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        **kwargs,
    ) -> T:
        """Generate validated structured output parsed into a Pydantic model."""
        pass

    @abstractmethod
    def estimate_usage(self, prompt: str, output: Optional[str] = None) -> UsageEstimate:
        """Estimate token usage and cost for prompt and optional output."""
        pass

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities, features, and context constraints."""
        pass

    @abstractmethod
    async def health(self) -> ProviderHealthStatus:
        """Check provider operational status and connectivity."""
        pass
