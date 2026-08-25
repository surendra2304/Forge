"""
Agent Capability Registry for Project FORGE.
Defines available engineering agent personas, their capabilities, tool assignments, and responsibilities.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    name: str = Field(..., description="Agent role name")
    display_name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Scope of responsibility")
    category: str = Field(..., description="Functional specialization")
    supported_tasks: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    max_context_tokens: int = Field(default=128000)
    version: str = Field(default="1.0.0")


class AgentRegistry:
    """Registry maintaining active agent roles and their capabilities."""

    def __init__(self):
        self._agents: Dict[str, AgentCapability] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        self.register(
            AgentCapability(
                name="planner",
                display_name="Software Architect & Planner",
                description="Decomposes high-level engineering goals into dependency-ordered TaskGraphs.",
                category="Planning",
                supported_tasks=["goal_decomposition", "dependency_graph_synthesis", "spec_generation"],
                available_tools=["dag_builder", "spec_writer", "file_lister"],
            )
        )
        self.register(
            AgentCapability(
                name="coder",
                display_name="Software Engineer",
                description="Authors clean, modular, idiomatic code and implementations inside the isolated sandbox.",
                category="Execution",
                supported_tasks=["code_generation", "refactoring", "module_synthesis", "dependency_management"],
                available_tools=["file_editor", "terminal_runner", "syntax_validator"],
            )
        )
        self.register(
            AgentCapability(
                name="tester",
                display_name="Verification & QA Engineer",
                description="Generates and runs unit tests, integration tests, fuzzing, and static verification.",
                category="Verification",
                supported_tasks=["unit_testing", "integration_testing", "coverage_analysis", "boundary_verification"],
                available_tools=["pytest_runner", "linter", "coverage_checker"],
            )
        )
        self.register(
            AgentCapability(
                name="reviewer",
                display_name="Security & Architecture Auditor",
                description="Audits generated code for security vulnerabilities, path traversal, and anti-patterns.",
                category="Security",
                supported_tasks=["security_audit", "secret_leak_detection", "code_review"],
                available_tools=["static_analyzer", "secret_scanner", "diff_reviewer"],
            )
        )
        self.register(
            AgentCapability(
                name="recovery",
                display_name="Self-Healing & Recovery Specialist",
                description="Performs root-cause analysis on build/runtime errors and formulates bounded repair patches.",
                category="Recovery",
                supported_tasks=["error_diagnosis", "stack_trace_analysis", "patch_synthesis", "rollback_execution"],
                available_tools=["debugger", "patch_applicator", "checkpoint_restorer"],
            )
        )

    def register(self, capability: AgentCapability) -> None:
        self._agents[capability.name] = capability

    def get(self, name: str) -> AgentCapability:
        return self._agents.get(name)

    def list_all(self) -> List[AgentCapability]:
        return list(self._agents.values())


agent_registry = AgentRegistry()
