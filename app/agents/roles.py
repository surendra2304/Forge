"""
Specialist Engineering Agent Roles for Project FORGE.
Implements 10 distinct specialist classes with role-specific system prompts, constraints, and tool behaviors.
"""

from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent
from app.core.logging import get_logger
from app.providers.base import BaseModelProvider

logger = get_logger("agents.roles")


class PlannerRole(BaseAgent):
    """Specialist responsible for requirements analysis and task graph decomposition."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="planner",
            display_name="Planner & Requirement Decomposer",
            system_prompt=(
                "You are the Lead Project Planner. Your job is to decompose high-level goals into "
                "a clean, dependency-ordered TaskGraph with clear verification gates and milestones."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        response = await self.prompt_model(f"Decompose task: {node_title}\nContext: {context}")
        return {"status": "success", "analysis": response.content, "agent": self.role_name}


class ArchitectRole(BaseAgent):
    """Specialist responsible for system architecture, schemas, and API design."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="architect",
            display_name="Software Architect",
            system_prompt=(
                "You are the Principal Software Architect. Design clean, decoupled, high-performance module "
                "structures, interface specifications, and database schemas."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        response = await self.prompt_model(f"Architect specification for: {node_title}\nContext: {context}")
        # Save architecture spec to workspace
        engine.fs.create_file(
            task_id=task_id,
            relative_path="docs/ARCHITECTURE_SPEC.md",
            content=response.content,
            role=self.role_name,
        )
        return {"status": "success", "spec_file": "docs/ARCHITECTURE_SPEC.md", "agent": self.role_name}


class DeveloperRole(BaseAgent):
    """General Software Engineer implementing core business logic and algorithms."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="developer",
            display_name="General Software Engineer",
            system_prompt=(
                "You are an Expert Software Engineer. Author production-quality, tested, maintainable code "
                "following modern idiomatic patterns."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        response = await self.prompt_model(f"Implement: {node_title}\nContext: {context}")
        return {"status": "success", "implementation_output": response.content, "agent": self.role_name}


class FrontendEngineerRole(BaseAgent):
    """Specialist in UI components, client-side frameworks, accessibility, and styling."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="frontend",
            display_name="Frontend Engineer",
            system_prompt=(
                "You are a Senior Frontend Engineer. Build responsive, accessible, modular UI components, "
                "state management layers, and client-side integrations."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        response = await self.prompt_model(f"Synthesize frontend component for: {node_title}\nContext: {context}")
        return {"status": "success", "frontend_result": response.content, "agent": self.role_name}


class BackendEngineerRole(BaseAgent):
    """Specialist in REST/GraphQL APIs, microservices, databases, and async queues."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="backend",
            display_name="Backend Engineer",
            system_prompt=(
                "You are a Senior Backend Engineer. Build resilient REST APIs, data access layers, "
                "transaction boundaries, and background job processors."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        response = await self.prompt_model(f"Implement backend services for: {node_title}\nContext: {context}")
        return {"status": "success", "backend_result": response.content, "agent": self.role_name}


class TesterRole(BaseAgent):
    """Specialist in unit tests, integration tests, fuzzing, and coverage analysis."""
    __test__ = False

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="tester",
            display_name="Verification & QA Engineer",
            system_prompt=(
                "You are a QA & Verification Engineer. Write exhaustive unit and integration tests, "
                "assert edge cases, and verify system behavior under adverse inputs."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        # Execute test runner command if tests exist
        cmd_res = await engine.terminal.run_command(task_id=task_id, command="pytest -v", role=self.role_name)
        return {
            "status": "success" if cmd_res.exit_code == 0 else "failed",
            "exit_code": cmd_res.exit_code,
            "stdout": cmd_res.stdout,
            "agent": self.role_name,
        }


class DebuggerRole(BaseAgent):
    """Specialist in root-cause error diagnosis and stack trace analysis."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="debugger",
            display_name="Debugger & Diagnostics Specialist",
            system_prompt=(
                "You are an Expert Debugger. Analyze stack traces, runtime logs, and test failures to isolate "
                "root causes and suggest minimal, verified fixes."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        error_context = context.get("error", "No explicit error provided")
        response = await self.prompt_model(f"Diagnose failure in {node_title}:\nError: {error_context}")
        return {"status": "success", "diagnosis": response.content, "agent": self.role_name}


class SecurityReviewerRole(BaseAgent):
    """Specialist in vulnerability assessment, secret detection, and permissions gating."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="security_reviewer",
            display_name="Security Auditor",
            system_prompt=(
                "You are a Principal Security Auditor. Inspect source code for vulnerabilities (SQL injection, "
                "path traversal, secret leakage, command injection) and enforce compliance."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        files = engine.fs.search_files(task_id=task_id, pattern="*.py", role=self.role_name)
        response = await self.prompt_model(f"Audit security for files: {files}\nScope: {node_title}")
        return {"status": "success", "security_findings": response.content, "agent": self.role_name}


class CodeReviewerRole(BaseAgent):
    """Specialist in code style, clean architecture, DRY principles, and maintainability."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="code_reviewer",
            display_name="Code Reviewer",
            system_prompt=(
                "You are a Senior Code Reviewer. Audit diffs for readability, performance bottlenecks, "
                "naming consistency, and documentation accuracy."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        diff_text = await engine.git.diff(task_id=task_id, role=self.role_name)
        response = await self.prompt_model(f"Review code diff:\n{diff_text}")
        return {"status": "success", "review_comments": response.content, "agent": self.role_name}


class ReleaseEngineerRole(BaseAgent):
    """Specialist in packaging, version tagging, build verification, and deployment manifests."""

    def __init__(self, provider: Optional[BaseModelProvider] = None):
        super().__init__(
            role_name="release_engineer",
            display_name="Release Engineer",
            system_prompt=(
                "You are a Release & Build Engineer. Validate package builds, create git tags, "
                "and generate release artifacts."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: Dict[str, Any], engine) -> Dict[str, Any]:
        git_status = await engine.git.status(task_id=task_id, role=self.role_name)
        tag_name = await engine.git.checkpoint(task_id=task_id, checkpoint_name="release", role=self.role_name)
        return {"status": "success", "tag": tag_name, "clean": git_status.clean, "agent": self.role_name}
