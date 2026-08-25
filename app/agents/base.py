"""
Base Agent Definition for Project FORGE.
An agent is a role/state package, strictly decoupled from the underlying interchangeable LLM provider.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.execution.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    PermissionManager,
    ToolPermission,
    permission_manager,
)
from app.providers.base import BaseModelProvider, ProviderResponse
from app.providers.direct import DirectProvider

logger = get_logger("agents.base")


class AgentState(BaseModel):
    """Encapsulates persistent working memory and scratchpad for an agent role."""
    role_name: str
    current_node_id: Optional[str] = None
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, str]] = Field(default_factory=list)
    tokens_consumed: int = 0
    budget_consumed: float = 0.0


class BaseAgent(ABC):
    """
    Abstract base for all specialized FORGE engineering agents.
    Represents role responsibilities, assigned permissions, and state memory,
    with an interchangeable model provider.
    """

    def __init__(
        self,
        role_name: str,
        display_name: str,
        system_prompt: str,
        provider: Optional[BaseModelProvider] = None,
        permissions: Optional[Set[ToolPermission]] = None,
    ):
        self.role_name = role_name
        self.display_name = display_name
        self.system_prompt = system_prompt
        # Interchangeable model provider (DirectProvider, OpenAI, Claude, Gemini, etc.)
        self.provider = provider or DirectProvider(model_name=f"direct-{role_name}")
        self.permissions = permissions or DEFAULT_ROLE_PERMISSIONS.get(role_name.lower(), set())
        self.state = AgentState(role_name=role_name)

    def set_provider(self, provider: BaseModelProvider) -> None:
        """Dynamically swap the underlying model provider at runtime."""
        self.provider = provider
        logger.info(f"Swapped provider on agent '{self.role_name}' to {provider.model_name}")

    async def prompt_model(self, prompt: str, system_override: Optional[str] = None, temperature: float = 0.2) -> ProviderResponse:
        """Query the underlying interchangeable model provider with agent persona context."""
        sys_prompt = system_override or self.system_prompt
        response = await self.provider.generate(prompt=prompt, system_prompt=sys_prompt, temperature=temperature)
        self.state.tokens_consumed += response.usage.total_tokens
        self.state.budget_consumed += response.usage.estimated_cost_usd
        self.state.history.append({"prompt": prompt[:200], "response": response.content[:200]})
        return response

    @abstractmethod
    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        """Execute a unit of work within the task graph."""
        pass
