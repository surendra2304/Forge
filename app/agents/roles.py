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

        # Query IntelX for technical research on unfamiliar or complex architectures
        research_info = ""
        try:
            from app.integrations.intelx_client import get_intelx_client
            from app.monitoring.production_monitor import production_monitor
            intelx_client = get_intelx_client()
            unfamiliar = intelx_client.detect_unfamiliar_technologies(goal)
            if unfamiliar:
                research_res = []
                for tech in unfamiliar:
                    res = await intelx_client.research_technology(tech, goal_context=goal)
                    research_res.append(res)
                    production_monitor.record_intelx_query()
                production_monitor.record_research_informed_build()
                research_info = "\n" + intelx_client.format_research_context_for_prompt(research_res) + "\n"
                if hasattr(engine, "store") and engine.store:
                    await engine.store.record_event(
                        task_id=task_id,
                        event_type="intelx.research_applied",
                        payload={"technologies": unfamiliar, "stage": "architect"},
                    )
        except Exception:
            pass

        # Consult Futuris for build success prediction, duration forecasting, and capacity check
        futuris_info = ""
        try:
            from app.integrations.futuris_client import get_futuris_client
            from app.monitoring.production_monitor import production_monitor
            futuris_client = get_futuris_client()
            assessment = futuris_client.get_full_assessment(goal=goal)
            production_monitor.record_futuris_consultation()
            production_monitor.record_prediction_informed_selection()
            if assessment.capacity_check.should_queue:
                production_monitor.record_capacity_queue_decision()

            futuris_info = (
                f"\nFuturis Predictive Intelligence (Assessment: {assessment.prediction_id}):\n"
                f"• Optimal Template: {assessment.best_template.template_name} (Predicted Success: {assessment.best_template.predicted_pass_probability * 100:.1f}%)\n"
                f"• Expected Duration: {assessment.duration_forecast.estimated_duration_seconds}s (p50={assessment.duration_forecast.p50_seconds}s, p90={assessment.duration_forecast.p90_seconds}s)\n"
                f"• Scheduling: {assessment.capacity_check.scheduling_tier} (Exhaustion Probability: {assessment.capacity_check.exhaustion_probability * 100:.1f}%)\n"
            )

            if hasattr(engine, "store") and engine.store:
                await engine.store.record_event(
                    task_id=task_id,
                    event_type="futuris.assessed",
                    payload={
                        "prediction_id": assessment.prediction_id,
                        "best_template": assessment.best_template.template_name,
                        "predicted_pass_prob": assessment.best_template.predicted_pass_probability,
                        "estimated_duration_seconds": assessment.duration_forecast.estimated_duration_seconds,
                        "scheduling_tier": assessment.capacity_check.scheduling_tier,
                    },
                )
        except Exception:
            pass

        prompt = (
            f"Objective: {goal}\n"
            f"Stage: {node_title}\n"
            f"{workspace_summary}\n"
            f"{consensus_info}\n"
            f"{research_info}\n"
            f"{futuris_info}\n"
            f"Please synthesize the complete Architecture Specification and File Manifest for this project. "
            f"Define system modules, interfaces, schema definitions, and file layout.\n\n"
            f"Format your output as:\n"
            f"### File: docs/ARCHITECTURE_SPEC.md\n"
            f"```markdown\n"
            f"# Architecture Specification: {goal}\n"
            f"...\n"
            f"```\n\n"
            f"### File: docs/FILE_MANIFEST.json\n"
            f"```json\n"
            f"[\n"
            f"  \"index.html\",\n"
            f"  \"style.css\",\n"
            f"  \"app.js\"\n"
            f"]\n"
            f"```"
        )
        response = await self.prompt_model(prompt)

        # Apply extracted files (e.g. docs/ARCHITECTURE_SPEC.md, docs/FILE_MANIFEST.json)
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

        # Parse or generate File Manifest
        manifest_files: list[str] = []
        if "docs/FILE_MANIFEST.json" in written:
            try:
                import json
                raw_json = engine.fs.read_file(task_id, "docs/FILE_MANIFEST.json", role=self.role_name)
                parsed = json.loads(raw_json)
                if isinstance(parsed, list):
                    manifest_files = [str(x) for x in parsed if x]
                elif isinstance(parsed, dict) and "files" in parsed:
                    manifest_files = [str(x) for x in parsed["files"] if x]
            except Exception:
                pass

        if not manifest_files:
            goal_lower = goal.lower()
            if any(k in goal_lower for k in ["full-stack", "fullstack", "dashboard"]):
                manifest_files = ["main.py", "test_main.py", "index.html", "style.css", "app.js", "requirements.txt", "README.md"]
            elif any(k in goal_lower for k in ["website", "landing page", "web page", "html", "portfolio", "css", "calculator website", "static"]):
                manifest_files = ["index.html", "style.css", "app.js"]
            elif any(k in goal_lower for k in ["fastapi", "rest api", "backend", "database", "sqlite", "service"]) or any(k in goal_lower for k in ["cli", "python tool", "command-line", "script"]):
                manifest_files = ["main.py", "test_main.py", "README.md"]
            else:
                manifest_files = ["main.py", "README.md"]

            import json
            engine.fs.create_file(
                task_id=task_id,
                relative_path="docs/FILE_MANIFEST.json",
                content=json.dumps(manifest_files, indent=2),
                role=self.role_name,
            )
            if "docs/FILE_MANIFEST.json" not in written:
                written.append("docs/FILE_MANIFEST.json")

        return {
            "status": "success",
            "spec_file": "docs/ARCHITECTURE_SPEC.md",
            "manifest_file": "docs/FILE_MANIFEST.json",
            "file_manifest": manifest_files,
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

        # 1. Retrieve File Manifest (from context, docs/FILE_MANIFEST.json, or project goal)
        file_manifest = context.get("file_manifest")
        if not file_manifest:
            try:
                import json
                raw_json = engine.fs.read_file(task_id, "docs/FILE_MANIFEST.json", role=self.role_name)
                parsed = json.loads(raw_json)
                if isinstance(parsed, list):
                    file_manifest = [str(x) for x in parsed if x]
                elif isinstance(parsed, dict) and "files" in parsed:
                    file_manifest = [str(x) for x in parsed["files"] if x]
            except Exception:
                pass

        if not file_manifest:
            goal_lower = goal.lower()
            if any(k in goal_lower for k in ["website", "landing page", "web page", "html", "portfolio", "css", "calculator website", "static"]):
                file_manifest = ["index.html", "style.css", "app.js"]
            elif any(k in goal_lower for k in ["full-stack", "fullstack"]):
                file_manifest = ["main.py", "index.html", "style.css", "app.js"]
            else:
                file_manifest = ["main.py"]

        written: list[str] = []
        fallback_files: list[str] = []
        last_run_id = None

        # Fetch IntelX technical research for unfamiliar technologies
        research_context_str = ""
        try:
            from app.integrations.intelx_client import get_intelx_client
            from app.monitoring.production_monitor import production_monitor
            intelx_client = get_intelx_client()
            unfamiliar = intelx_client.detect_unfamiliar_technologies(goal or node_title)
            if unfamiliar:
                res_list = []
                for tech in unfamiliar:
                    res = await intelx_client.research_technology(tech, goal_context=goal or node_title)
                    res_list.append(res)
                    production_monitor.record_intelx_query()
                production_monitor.record_research_informed_build()
                research_context_str = intelx_client.format_research_context_for_prompt(res_list)
        except Exception:
            pass

        # 2. Iterate through each file in File Manifest and synthesize code
        for filename in file_manifest:
            if not filename or not isinstance(filename, str):
                continue

            ai_code = None
            try:
                from app.integrations.ai_universe_client import get_ai_universe_client
                ai_client = get_ai_universe_client()
                ask_prompt = (
                    f"Write the complete code for {filename} based on the overall architecture: {goal or node_title}.\n"
                    f"{research_context_str}\n\n"
                    f"Security requirements: Input validation on all user inputs, parameterized SQL (never string concatenation), "
                    f"clean error handling without stack trace leaks, secure default configurations, authentication checks on protected endpoints, "
                    f"and CSRF / secure headers where applicable. Return ONLY the raw code."
                )
                ai_res = await ai_client.ask(question=ask_prompt, mode="auto")

                if ai_res and ai_res.confidence >= 0.70 and ai_res.answer and ai_res.answer.strip():
                    ai_code = ai_res.answer
                    last_run_id = ai_res.run_id
                    if hasattr(engine, "store") and engine.store:
                        await engine.store.record_event(
                            task_id=task_id,
                            event_type="ai_universe.code_generated",
                            payload={"file": filename, "run_id": ai_res.run_id, "confidence": ai_res.confidence, "stage": "developer"},
                        )
                elif ai_res and ai_res.confidence < 0.70:
                    logger.warning(
                        f"AI Universe code generation for '{filename}' confidence ({ai_res.confidence:.2f}) below threshold 0.70. Falling back to local model."
                    )
            except Exception as e:
                logger.warning(f"AI Universe code generation call for '{filename}' failed ({e}). Falling back to local model.")

            if ai_code:
                # Extract structured file blocks or save directly to filename
                extracted = self.apply_extracted_files(
                    task_id=task_id,
                    response_text=ai_code,
                    engine=engine,
                    default_filename=filename,
                )
                if extracted:
                    for p in extracted:
                        if p not in written:
                            written.append(p)
                else:
                    clean_code = ai_code.strip()
                    if clean_code.startswith("```"):
                        lines = clean_code.splitlines()
                        if lines and lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        clean_code = "\n".join(lines)

                    engine.fs.create_file(
                        task_id=task_id,
                        relative_path=filename,
                        content=clean_code,
                        role=self.role_name,
                    )
                    if filename not in written:
                        written.append(filename)
            else:
                # Fallback to local LLM / DirectProvider (stub generator)
                fallback_files.append(filename)
                prompt = (
                    f"Objective: {goal}\n"
                    f"Task: {node_title}\n"
                    f"Implement complete code for file: {filename}\n"
                    f"{workspace_summary}\n"
                    f"{existing_code_summary}\n\n"
                    f"Please implement the complete code for '{filename}'.\n"
                    f"Delimit each file clearly with:\n"
                    f"### File: {filename}\n```\n<code>\n```"
                )
                response = await self.prompt_model(prompt)
                extracted = self.apply_extracted_files(
                    task_id=task_id,
                    response_text=response.content,
                    engine=engine,
                    default_filename=filename,
                )
                for p in extracted:
                    if p not in written:
                        written.append(p)

        # Flag fallback_stub in workspace state
        if fallback_files:
            import json as py_json
            fallback_meta = {"fallback_stub": True, "fallback_files": fallback_files}
            paths = engine.wm.get_workspace_paths(task_id) or engine.wm.create_workspace(task_id)
            (paths.state / "FALLBACK_STUB.json").write_text(py_json.dumps(fallback_meta, indent=2), encoding="utf-8")
            if hasattr(engine, "store") and engine.store:
                try:
                    await engine.store.record_event(
                        task_id=task_id,
                        event_type="task.fallback_stub",
                        payload=fallback_meta,
                    )
                except Exception:
                    pass

        ret: dict[str, Any] = {
            "status": "success",
            "files_written": written,
            "implementation_output": f"Generated files: {written}",
            "agent": self.role_name,
            "fallback_stub": bool(fallback_files),
            "fallback_files": fallback_files,
        }
        if last_run_id is not None:
            ret["ai_universe_run_id"] = last_run_id
        return ret


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
