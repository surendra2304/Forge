"""
Base Agent Definition for Project FORGE.
An agent is a role/state package, strictly decoupled from the underlying interchangeable LLM provider.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.execution.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    ToolPermission,
)
from app.providers.base import BaseModelProvider, ProviderResponse
from app.providers.direct import DirectProvider

logger = get_logger("agents.base")


class AgentState(BaseModel):
    """Encapsulates persistent working memory and scratchpad for an agent role."""
    role_name: str
    current_node_id: str | None = None
    scratchpad: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, str]] = Field(default_factory=list)
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
        provider: BaseModelProvider | None = None,
        permissions: set[ToolPermission] | None = None,
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

    async def prompt_model(self, prompt: str, system_override: str | None = None, temperature: float = 0.2) -> ProviderResponse:
        """Query the underlying interchangeable model provider with agent persona context."""
        sys_prompt = system_override or self.system_prompt
        response = await self.provider.generate(prompt=prompt, system_prompt=sys_prompt, temperature=temperature)
        self.state.tokens_consumed += response.usage.total_tokens
        self.state.budget_consumed += response.usage.estimated_cost_usd
        self.state.history.append({"prompt": prompt[:200], "response": response.content[:200]})
        return response

    def apply_extracted_files(
        self,
        task_id: str,
        response_text: str,
        engine,
        default_filename: str | None = None,
    ) -> list[str]:
        """
        Extract code blocks and files from LLM response text and write them to the workspace sandbox.
        """
        from app.agents.parser import LLMResponseParser

        extracted = LLMResponseParser.extract_files(response_text, default_filename=default_filename)
        written_paths: list[str] = []

        for file_item in extracted:
            try:
                rel_path = engine.fs.create_file(
                    task_id=task_id,
                    relative_path=file_item.relative_path,
                    content=file_item.content,
                    role=self.role_name,
                )
                written_paths.append(rel_path)
                logger.info(f"Agent '{self.role_name}' applied file '{rel_path}' to workspace in task {task_id}")
            except Exception as e:
                logger.error(f"Failed to write extracted file '{file_item.relative_path}' for agent '{self.role_name}': {e}")

        return written_paths

    def get_workspace_summary(self, task_id: str, engine, max_files: int = 30) -> str:
        """Summarize existing files in workspace project sandbox."""
        try:
            files = engine.fs.search_files(task_id=task_id, pattern="*", role=self.role_name)
            if not files:
                return "Workspace is empty."
            return "Current workspace files:\n" + "\n".join([f"- {f}" for f in files[:max_files]])
        except Exception:
            return "Workspace files could not be listed."

    @abstractmethod
    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        """Execute a unit of work within the task graph."""
