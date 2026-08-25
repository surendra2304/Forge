"""
Specialist Engineering Agent Roles for Project FORGE.
Implements 10 distinct specialist classes with dynamic LLM prompting, file extraction,
and sandboxed execution tool interactions.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.logging import get_logger
from app.providers.base import BaseModelProvider

logger = get_logger("agents.roles")


class PlannerRole(BaseAgent):
    """Specialist responsible for requirements analysis and task graph decomposition."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="planner",
            display_name="Planner & Requirement Decomposer",
            system_prompt=(
                "You are the Lead Project Planner. Your job is to decompose high-level goals into "
                "a clean, dependency-ordered TaskGraph with clear verification gates and milestones. "
                "Provide detailed, actionable breakdowns of functional and non-functional requirements."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", node_title)
        workspace_summary = self.get_workspace_summary(task_id, engine)
        prompt = (
            f"Task: {node_title}\n"
            f"Project Objective: {goal}\n"
            f"{workspace_summary}\n"
            f"Context: {context}\n\n"
            f"Please analyze the scope, formulate concrete requirements, and outline implementation milestones."
        )
        response = await self.prompt_model(prompt)
        return {
            "status": "success",
            "analysis": response.content,
            "agent": self.role_name,
        }


class ArchitectRole(BaseAgent):
    """Specialist responsible for system architecture, schemas, and API design."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="architect",
            display_name="Software Architect",
            system_prompt=(
                "You are the Principal Software Architect. Design clean, decoupled, high-performance module "
                "structures, interface specifications, and database schemas. "
                "Structure files using markdown headers like:\n"
                "### File: docs/ARCHITECTURE_SPEC.md\n```markdown\n<architecture spec>\n```\n"
                "Provide complete, comprehensive technical architecture specifications."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "Engineering Project")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        # Consult AI Universe peer debate for complex architectural decisions
        consensus_info = ""
        try:
            from app.integrations.ai_universe_client import get_ai_universe_client
            ai_client = get_ai_universe_client()
            ai_res = await ai_client.consult_with_verification(
                question=f"Architectural tradeoffs, schemas, and module structure for: {goal}. Stage: {node_title}",
                min_confidence=0.70,
                use_debate=True,
            )
            if ai_res:
                consensus_info = f"\nExternal Multi-Agent Consensus (Run ID: {ai_res.run_id}):\n{ai_res.answer}\n"
                if hasattr(engine, "store") and engine.store:
                    await engine.store.record_event(
                        task_id=task_id,
                        event_type="ai_universe.consulted",
                        payload={"run_id": ai_res.run_id, "confidence": ai_res.confidence, "stage": "architecture"},
                    )
        except Exception:
            pass

        prompt = (
            f"Objective: {goal}\n"
            f"Stage: {node_title}\n"
            f"{workspace_summary}\n"
            f"{consensus_info}\n"
            f"Please synthesize the complete Architecture Specification for this project. "
            f"Define system modules, interfaces, schema definitions, and file layout.\n"
            f"Format the primary specification document as:\n"
            f"### File: docs/ARCHITECTURE_SPEC.md\n"
            f"```markdown\n"
            f"# Architecture Specification: {goal}\n"
            f"...\n"
            f"```"
        )
        response = await self.prompt_model(prompt)

        # Apply extracted files (e.g. docs/ARCHITECTURE_SPEC.md)
        written = self.apply_extracted_files(
            task_id=task_id,
            response_text=response.content,
            engine=engine,
            default_filename="docs/ARCHITECTURE_SPEC.md",
        )

        # Ensure docs/ARCHITECTURE_SPEC.md is created even if direct provider is used
        if "docs/ARCHITECTURE_SPEC.md" not in written:
            engine.fs.create_file(
                task_id=task_id,
                relative_path="docs/ARCHITECTURE_SPEC.md",
                content=response.content,
                role=self.role_name,
            )
            written.append("docs/ARCHITECTURE_SPEC.md")

        return {
            "status": "success",
            "spec_file": "docs/ARCHITECTURE_SPEC.md",
            "files_written": written,
            "agent": self.role_name,
        }


class DeveloperRole(BaseAgent):
    """General Software Engineer implementing core business logic and algorithms."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="developer",
            display_name="General Software Engineer",
            system_prompt=(
                "You are an Expert Software Engineer. Author production-quality, tested, maintainable code "
                "following modern idiomatic patterns with no placeholders. "
                "Format each source file output using markdown headers:\n"
                "### File: relative/path/to/file.ext\n```<language>\n<complete source code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "")
        workspace_summary = self.get_workspace_summary(task_id, engine)
        existing_code_summary = ""

        if "existing_files" in context:
            existing_code_summary = "\nExisting files content:\n" + "\n---\n".join(
                [f"File: {p}\n```\n{c}\n```" for p, c in context["existing_files"].items()]
            )

        prompt = (
            f"Objective: {goal}\n"
            f"Task: {node_title}\n"
            f"{workspace_summary}\n"
            f"{existing_code_summary}\n\n"
            f"Please implement the required code for this task. "
            f"Ensure all files are complete with full implementations and no placeholders. "
            f"Delimit each file clearly with:\n"
            f"### File: path/to/file.py\n```python\n<code>\n```"
        )
        response = await self.prompt_model(prompt)

        written = self.apply_extracted_files(
            task_id=task_id,
            response_text=response.content,
            engine=engine,
        )

        return {
            "status": "success",
            "files_written": written,
            "implementation_output": response.content,
            "agent": self.role_name,
        }


class FrontendEngineerRole(BaseAgent):
    """Specialist in UI components, client-side frameworks, accessibility, and styling."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="frontend",
            display_name="Frontend Engineer",
            system_prompt=(
                "You are a Senior Frontend Engineer. Build responsive, accessible, modular UI components, "
                "state management layers, and client-side integrations. "
                "Delimit each file clearly with:\n"
                "### File: path/to/file.ext\n```<language>\n<complete code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        prompt = (
            f"Objective: {goal}\n"
            f"Frontend Task: {node_title}\n"
            f"{workspace_summary}\n\n"
            f"Implement frontend user interfaces, styling, and interactive client components. "
            f"Output clean, modular code delimited by '### File: path/to/file.ext'."
        )
        response = await self.prompt_model(prompt)

        written = self.apply_extracted_files(
            task_id=task_id,
            response_text=response.content,
            engine=engine,
        )

        return {
            "status": "success",
            "files_written": written,
            "frontend_result": response.content,
            "agent": self.role_name,
        }


class BackendEngineerRole(BaseAgent):
    """Specialist in REST/GraphQL APIs, microservices, databases, and async queues."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="backend",
            display_name="Backend Engineer",
            system_prompt=(
                "You are a Senior Backend Engineer. Build resilient REST APIs, data access layers, "
                "transaction boundaries, and background job processors. "
                "Delimit each file clearly with:\n"
                "### File: path/to/file.py\n```python\n<complete code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        prompt = (
            f"Objective: {goal}\n"
            f"Backend Task: {node_title}\n"
            f"{workspace_summary}\n\n"
            f"Implement robust backend services, data models, routes, and controllers. "
            f"Output complete implementations with error handling, delimited with '### File: path/to/file.py'."
        )
        response = await self.prompt_model(prompt)

        written = self.apply_extracted_files(
            task_id=task_id,
            response_text=response.content,
            engine=engine,
        )

        return {
            "status": "success",
            "files_written": written,
            "backend_result": response.content,
            "agent": self.role_name,
        }


class TesterRole(BaseAgent):
    """Specialist in unit tests, integration tests, fuzzing, and coverage analysis."""
    __test__ = False

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="tester",
            display_name="Verification & QA Engineer",
            system_prompt=(
                "You are a QA & Verification Engineer. Write exhaustive unit and integration tests, "
                "assert edge cases, and verify system behavior under adverse inputs. "
                "Format test files as:\n"
                "### File: tests/test_feature.py\n```python\n<test code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        # Check existing test files
        test_files = engine.fs.search_files(task_id=task_id, pattern="test_*.py", role=self.role_name)

        # If no tests exist and this is a test generation step, prompt for test synthesis
        if not test_files and "verify" not in node_title.lower():
            prompt = (
                f"Objective: {goal}\n"
                f"QA Task: {node_title}\n"
                f"{workspace_summary}\n\n"
                f"Write comprehensive pytest unit tests for the existing application.\n"
                f"Format tests as:\n### File: test_main.py\n```python\n...\n```"
            )
            response = await self.prompt_model(prompt)
            self.apply_extracted_files(task_id, response.content, engine, default_filename="test_main.py")

        # Execute test runner
        cmd_res = await engine.terminal.run_command(task_id=task_id, command="pytest -v", role=self.role_name)

        return {
            "status": "success" if cmd_res.exit_code == 0 else "failed",
            "exit_code": cmd_res.exit_code,
            "stdout": cmd_res.stdout,
            "stderr": cmd_res.stderr,
            "agent": self.role_name,
        }


class DebuggerRole(BaseAgent):
    """Specialist in root-cause error diagnosis and stack trace analysis."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="debugger",
            display_name="Debugger & Diagnostics Specialist",
            system_prompt=(
                "You are an Expert Debugger. Analyze stack traces, runtime logs, and test failures to isolate "
                "root causes and produce minimal, verified code fixes. "
                "Delimit repaired files with:\n"
                "### File: path/to/file.py\n```python\n<fixed code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        error_context = context.get("error", "No explicit error provided")
        terminal_logs = context.get("terminal_logs", "No terminal logs.")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        # Consult AI Universe peer debate for complex root-cause diagnosis
        consensus_info = ""
        try:
            from app.integrations.ai_universe_client import get_ai_universe_client
            ai_client = get_ai_universe_client()
            ai_res = await ai_client.consult_with_verification(
                question=f"Diagnose root cause and bug fix for: {error_context}. Diagnostic Scope: {node_title}",
                min_confidence=0.70,
                use_debate=True,
            )
            if ai_res:
                consensus_info = f"\nExternal Multi-Agent Consensus (Run ID: {ai_res.run_id}):\n{ai_res.answer}\n"
                if hasattr(engine, "store") and engine.store:
                    await engine.store.record_event(
                        task_id=task_id,
                        event_type="ai_universe.consulted",
                        payload={"run_id": ai_res.run_id, "confidence": ai_res.confidence, "stage": "debugging"},
                    )
        except Exception:
            pass

        prompt = (
            f"Diagnostic Scope: {node_title}\n"
            f"Error Information:\n{error_context}\n\n"
            f"Recent Terminal Logs:\n{terminal_logs}\n\n"
            f"{workspace_summary}\n"
            f"{consensus_info}\n"
            f"Please perform root-cause failure analysis and provide the exact code fixes required. "
            f"Delimit any fixed files with '### File: path/to/file.py'."
        )
        response = await self.prompt_model(prompt)

        # Apply any fix files extracted from the debugger's response
        fixed_files = self.apply_extracted_files(task_id, response.content, engine)

        return {
            "status": "success",
            "diagnosis": response.content,
            "fixed_files": fixed_files,
            "agent": self.role_name,
        }


class SecurityReviewerRole(BaseAgent):
    """Specialist in vulnerability assessment, secret detection, and automated security remediation."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="security_reviewer",
            display_name="Security Auditor",
            system_prompt=(
                "You are a Principal Security Auditor & DevSecOps Engineer. "
                "Inspect source code for vulnerabilities (hardcoded API keys, SQL injection, "
                "insecure eval/exec calls, path traversal). Author secure, remediated code "
                "replacing hardcoded secrets with environment variables (os.environ, process.env).\n"
                "Format fixes as:\n### File: <file_path>\n```<lang>\n<code>\n```"
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        from app.verification.checkers import SecurityChecker

        # 1. Run automated SecurityChecker
        checker = SecurityChecker()
        evidence = await checker.run_check(task_id, engine)
        workspace_summary = self.get_workspace_summary(task_id, engine)

        files_written = []
        if not evidence.passed and evidence.issues:
            logger.info(f"SecurityReviewer found {len(evidence.issues)} security violations. Formulating remediation patch...")

            # Read contents of failing files
            violating_files = {issue["file"] for issue in evidence.issues if "file" in issue}
            file_excerpts = {}
            for vf in violating_files:
                try:
                    content = engine.fs.read_file(task_id, vf, role=self.role_name)
                    if content:
                        file_excerpts[vf] = content
                except Exception:
                    pass

            prompt = (
                f"Security Remediation: {node_title}\n"
                f"{workspace_summary}\n\n"
                f"Security Violations Detected:\n{evidence.issues}\n\n"
                f"Vulnerable File Contents:\n"
                + "\n".join([f"--- {fn} ---\n{fc}\n" for fn, fc in file_excerpts.items()])
                + "\nFix all security vulnerabilities and secret leaks. "
                "Replace hardcoded credentials with environment variable reads (e.g. os.getenv, process.env). "
                "Provide complete, secure drop-in replacement files.\n\n"
                "Format fixes as:\n### File: path/to/file.ext\n```<lang>\n<code>\n```"
            )
            response = await self.prompt_model(prompt)
            files_written = self.apply_extracted_files(task_id, response.content, engine)

            # Re-verify post-fix
            evidence = await checker.run_check(task_id, engine)
        else:
            prompt = (
                f"Security Audit: {node_title}\n"
                f"{workspace_summary}\n"
                f"Context: {context}\n\n"
                f"Conduct a security review and confirm compliance with OWASP Top 10 and secret hygiene."
            )
            response = await self.prompt_model(prompt)

        return {
            "status": "success" if evidence.passed else "failed",
            "security_passed": evidence.passed,
            "violations_detected": len(evidence.issues),
            "files_remediated": files_written,
            "security_findings": response.content if "response" in locals() else "Security checks passed.",
            "agent": self.role_name,
        }


class CodeReviewerRole(BaseAgent):
    """Specialist in code style, clean architecture, DRY principles, and maintainability."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="code_reviewer",
            display_name="Code Reviewer",
            system_prompt=(
                "You are a Senior Code Reviewer. Audit diffs for readability, performance bottlenecks, "
                "naming consistency, and documentation accuracy."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        diff_text = context.get("recent_diffs")
        if not diff_text:
            diff_text = await engine.git.diff(task_id=task_id, role=self.role_name)

        workspace_summary = self.get_workspace_summary(task_id, engine)

        prompt = (
            f"Code Review: {node_title}\n"
            f"{workspace_summary}\n\n"
            f"Code Diff to Review:\n{diff_text}\n\n"
            f"Audit the diff for quality, maintainability, idiomatic style, and test coverage."
        )
        response = await self.prompt_model(prompt)

        return {
            "status": "success",
            "review_comments": response.content,
            "agent": self.role_name,
        }


class ReleaseEngineerRole(BaseAgent):
    """Specialist in packaging, version tagging, build verification, and deployment manifests."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="release_engineer",
            display_name="Release Engineer",
            system_prompt=(
                "You are a Release & Build Engineer. Validate package builds, create git tags, "
                "and generate release artifacts."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        from app.execution.delivery import DeliveryPackager
        packager = DeliveryPackager(engine=engine, wm=engine.wm)
        goal = context.get("goal", "Autonomous Engineering Project")
        reqs = context.get("requirements", [])
        report_data = await packager.package_delivery(
            task_id=task_id,
            goal=goal,
            requirements=reqs,
            tag_name="v1.0-forge-delivery",
        )

        pr_info = None
        push_to_gh = context.get("push_to_github") or False
        gh_token = context.get("github_token") or (hasattr(engine, "github") and engine.github.settings.github_token)
        gh_repo = context.get("github_repo") or (hasattr(engine, "github") and engine.github.settings.github_repo)

        if push_to_gh or gh_token or gh_repo:
            branch_name = f"forge/feature-{task_id[:8]}"
            logger.info(f"[Task {task_id}] ReleaseEngineer executing GitHub PR flow on branch '{branch_name}'...")

            # 1. Create and checkout feature branch
            await engine.github.create_branch(task_id, branch_name=branch_name, role=self.role_name)

            # 2. Commit all project files
            await engine.github.commit_files(
                task_id=task_id,
                commit_message=f"feat(forge): {goal[:72]}\n\nAutomated delivery by FORGE Autonomous Engine.",
                role=self.role_name,
            )

            # 3. Push branch to remote
            await engine.github.push_branch(
                task_id=task_id,
                branch_name=branch_name,
                repo=gh_repo,
                token=gh_token,
                role=self.role_name,
            )

            # 4. Open Pull Request with COMPLETION_REPORT.md as body
            completion_md = ""
            paths = engine.wm.get_workspace_paths(task_id)
            if paths and (paths.artifacts / "COMPLETION_REPORT.md").exists():
                completion_md = (paths.artifacts / "COMPLETION_REPORT.md").read_text(encoding="utf-8")
            else:
                completion_md = f"# FORGE Automated Delivery\n\n**Goal**: {goal}\n"

            pr_result = await engine.github.create_pull_request(
                repo=gh_repo,
                title=f"[FORGE] {goal}",
                body=completion_md,
                head_branch=branch_name,
                token=gh_token,
            )
            pr_info = pr_result.model_dump(mode="json")
            logger.info(f"[Task {task_id}] Pull Request created: {pr_result.html_url}")

        res = {
            "status": "success",
            "release_tag": report_data.release_tag,
            "completion_report": report_data.model_dump(mode="json"),
            "agent": self.role_name,
        }
        if pr_info:
            res["pull_request"] = pr_info
            res["pull_request_url"] = pr_info["html_url"]
        return res


class CodebaseAnalyzerRole(BaseAgent):
    """Specialist in codebase onboarding, directory structure mapping, dependency inspection, and project context synthesis."""

    def __init__(self, provider: BaseModelProvider | None = None):
        super().__init__(
            role_name="codebase_analyzer",
            display_name="Codebase Analyzer & Onboarding Specialist",
            system_prompt=(
                "You are an expert Software Architect and Codebase Analyst. "
                "Analyze existing codebase structure, identify the technology stack, framework conventions, "
                "data models, key modules, entry points, and test suites. "
                "Generate a clear, structured Project Context Summary."
            ),
            provider=provider,
        )

    async def execute_step(self, task_id: str, node_title: str, context: dict[str, Any], engine) -> dict[str, Any]:
        goal = context.get("goal", "Analyze existing codebase")
        workspace_summary = self.get_workspace_summary(task_id, engine)

        # 1. Inspect manifest files
        manifests = {}
        candidate_manifests = [
            "package.json", "requirements.txt", "pyproject.toml", "Pipfile", "setup.py",
            "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Gemfile", "composer.json",
            "Dockerfile", "docker-compose.yml", "Makefile",
        ]
        for manifest in candidate_manifests:
            try:
                content = engine.fs.read_file(task_id, manifest, role=self.role_name)
                if content:
                    manifests[manifest] = content[:1000]
            except Exception:
                pass

        # 2. Inspect documentation and entrypoints
        key_files = {}
        for kf in ["README.md", "main.py", "app.py", "src/main.py", "src/index.ts", "src/index.js", "index.html"]:
            try:
                content = engine.fs.read_file(task_id, kf, role=self.role_name)
                if content:
                    key_files[kf] = content[:1500]
            except Exception:
                pass

        # 3. Detect tech stack
        detected_stack = []
        if "package.json" in manifests:
            detected_stack.append("Node.js / JavaScript / TypeScript")
        if any(m in manifests for m in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]):
            detected_stack.append("Python")
        if "go.mod" in manifests:
            detected_stack.append("Go")
        if "Cargo.toml" in manifests:
            detected_stack.append("Rust")
        if not detected_stack:
            detected_stack.append("Generic / Polyglot")

        prompt = (
            f"Task: {node_title}\n"
            f"Engineering Goal: {goal}\n\n"
            f"{workspace_summary}\n\n"
            f"Detected Manifests: {list(manifests.keys())}\n"
            f"Detected Stacks: {', '.join(detected_stack)}\n\n"
            f"Key File Excerpts:\n"
            + "\n".join([f"--- {fn} ---\n{fc}\n" for fn, fc in key_files.items()])
            + "\nSynthesize a comprehensive Project Context Summary document explaining:\n"
            "- Core Architecture & Tech Stack\n"
            "- Directory Layout & Key Modules\n"
            "- Existing Entrypoints & APIs\n"
            "- Existing Test Suite & Verification Commands\n"
            "- Recommendations for implementing: " + goal + "\n\n"
            "Format the output as:\n"
            "### File: docs/PROJECT_CONTEXT_SUMMARY.md\n```markdown\n# Project Context Summary\n...\n```"
        )

        response = await self.prompt_model(prompt)
        written = self.apply_extracted_files(
            task_id=task_id,
            response_text=response.content,
            engine=engine,
            default_filename="docs/PROJECT_CONTEXT_SUMMARY.md",
        )

        return {
            "status": "success",
            "files_written": written,
            "detected_manifests": list(manifests.keys()),
            "detected_stack": detected_stack,
            "context_summary_file": "docs/PROJECT_CONTEXT_SUMMARY.md",
            "agent": self.role_name,
        }
