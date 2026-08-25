"""
Agent Capability Registry and Factory for Project FORGE.
Registers and instantiates specialist engineering roles with decoupled model providers.
"""

from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.roles import (
    ArchitectRole,
    BackendEngineerRole,
    CodeReviewerRole,
    DebuggerRole,
    DeveloperRole,
    FrontendEngineerRole,
    PlannerRole,
    ReleaseEngineerRole,
    SecurityReviewerRole,
    TesterRole,
)
from app.providers.base import BaseModelProvider


class AgentCapability(BaseModel):
    name: str = Field(..., description="Agent role identifier")
    display_name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Scope of responsibility")
    category: str = Field(..., description="Functional specialization")
    supported_tasks: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    max_context_tokens: int = Field(default=128000)
    version: str = Field(default="1.0.0")


class AgentRegistry:
    """Registry managing capability metadata and factory instantiation of specialist agents."""

    def __init__(self):
        self._capabilities: Dict[str, AgentCapability] = {}
        self._role_classes: Dict[str, Type[BaseAgent]] = {}
        self._register_default_roles()

    def _register_default_roles(self) -> None:
        roles_meta = [
            (
                "planner",
                PlannerRole,
                AgentCapability(
                    name="planner",
                    display_name="Planner & Requirement Decomposer",
                    description="Decomposes goals into a hierarchical task tree and executable DAG.",
                    category="Planning",
                    supported_tasks=["goal_decomposition", "dependency_graph_synthesis", "spec_generation"],
                    available_tools=["fs:read", "git:read"],
                ),
            ),
            (
                "architect",
                ArchitectRole,
                AgentCapability(
                    name="architect",
                    display_name="Software Architect",
                    description="Designs system architecture, module boundaries, and interfaces.",
                    category="Architecture",
                    supported_tasks=["system_design", "api_specification", "schema_design"],
                    available_tools=["fs:read", "fs:write", "git:read"],
                ),
            ),
            (
                "developer",
                DeveloperRole,
                AgentCapability(
                    name="developer",
                    display_name="General Software Engineer",
                    description="Authors clean, tested implementation code across modules.",
                    category="Implementation",
                    supported_tasks=["code_generation", "refactoring", "module_synthesis"],
                    available_tools=["fs:read", "fs:write", "fs:delete", "terminal:exec", "git:read", "git:write"],
                ),
            ),
            (
                "frontend",
                FrontendEngineerRole,
                AgentCapability(
                    name="frontend",
                    display_name="Frontend Engineer",
                    description="Builds interactive UI components, styles, and client state.",
                    category="Implementation",
                    supported_tasks=["ui_components", "state_management", "client_integration"],
                    available_tools=["fs:read", "fs:write", "fs:delete", "terminal:exec", "git:read", "git:write"],
                ),
            ),
            (
                "backend",
                BackendEngineerRole,
                AgentCapability(
                    name="backend",
                    display_name="Backend Engineer",
                    description="Implements REST APIs, data layers, queues, and server logic.",
                    category="Implementation",
                    supported_tasks=["rest_apis", "database_models", "background_workers"],
                    available_tools=["fs:read", "fs:write", "fs:delete", "terminal:exec", "git:read", "git:write"],
                ),
            ),
            (
                "tester",
                TesterRole,
                AgentCapability(
                    name="tester",
                    display_name="Verification & QA Engineer",
                    description="Authors and executes unit, integration, and fuzzing tests.",
                    category="Verification",
                    supported_tasks=["unit_testing", "integration_testing", "coverage_analysis"],
                    available_tools=["fs:read", "fs:write", "terminal:exec", "git:read"],
                ),
            ),
            (
                "debugger",
                DebuggerRole,
                AgentCapability(
                    name="debugger",
                    display_name="Debugger & Diagnostics Specialist",
                    description="Performs root-cause analysis on logs, tracebacks, and test failures.",
                    category="Diagnostics",
                    supported_tasks=["error_diagnosis", "stack_trace_analysis", "patch_formulation"],
                    available_tools=["fs:read", "fs:write", "terminal:exec", "git:read"],
                ),
            ),
            (
                "security_reviewer",
                SecurityReviewerRole,
                AgentCapability(
                    name="security_reviewer",
                    display_name="Security Auditor",
                    description="Inspects source code for security vulnerabilities and secret leakage.",
                    category="Security",
                    supported_tasks=["security_audit", "secret_scanning", "vulnerability_scan"],
                    available_tools=["fs:read", "terminal:exec", "git:read"],
                ),
            ),
            (
                "code_reviewer",
                CodeReviewerRole,
                AgentCapability(
                    name="code_reviewer",
                    display_name="Code Reviewer",
                    description="Reviews diffs for quality, idiomatic design, and maintainability.",
                    category="Quality",
                    supported_tasks=["code_review", "style_compliance", "refactoring_review"],
                    available_tools=["fs:read", "git:read"],
                ),
            ),
            (
                "release_engineer",
                ReleaseEngineerRole,
                AgentCapability(
                    name="release_engineer",
                    display_name="Release Engineer",
                    description="Validates packages, creates release checkpoints, and prepares artifacts.",
                    category="Release",
                    supported_tasks=["packaging", "tagging", "release_verification"],
                    available_tools=["fs:read", "fs:write", "terminal:exec", "git:read", "git:write"],
                ),
            ),
        ]

        for name, cls_type, cap in roles_meta:
            self._role_classes[name] = cls_type
            self._capabilities[name] = cap

    def get_capability(self, role_name: str) -> Optional[AgentCapability]:
        """Retrieve capability descriptor for an agent role."""
        return self._capabilities.get(role_name.lower())

    def list_all(self) -> List[AgentCapability]:
        """List all registered agent role capabilities."""
        return list(self._capabilities.values())

    def create_agent(self, role_name: str, provider: Optional[BaseModelProvider] = None) -> BaseAgent:
        """Instantiate a specialist agent role class with a given or default model provider."""
        cls_type = self._role_classes.get(role_name.lower())
        if not cls_type:
            # Fallback to DeveloperRole for unrecognized role identifiers
            cls_type = DeveloperRole
        return cls_type(provider=provider)


agent_registry = AgentRegistry()
