"""
Unit tests for ForgeWebStudio 3D Website and Web App Engine.
Validates Lovable/Bolt/Durable standards, 3D WebGL graphics, zero placeholders,
and aesthetic verification.
"""

from pathlib import Path

import pytest

from app.agents.language_builders import Web3DBuilder
from app.templates.web_studio.domain_synthesizer import DomainSynthesizer
from app.templates.web_studio.generator import ForgeWebStudio
from app.templates.web_studio.three_d_engine import Web3DEngine
from app.verification.quality_analyzer import CodeQualityAnalyzer


def test_domain_synthesizer_classification():
    portfolio_bp = DomainSynthesizer.analyze_goal("Build a personal 3D creative developer portfolio")
    assert portfolio_bp.domain_type == "portfolio"
    assert portfolio_bp.showcase_items
    assert len(portfolio_bp.showcase_items) >= 2

    saas_bp = DomainSynthesizer.analyze_goal("Create a modern AI SaaS analytics platform")
    assert saas_bp.domain_type == "saas"
    assert saas_bp.showcase_items

    ecom_bp = DomainSynthesizer.analyze_goal("Build a luxury minimalist e-commerce fashion store")
    assert ecom_bp.domain_type == "ecommerce"

    dash_bp = DomainSynthesizer.analyze_goal("Build a real-time IoT sensor telemetry dashboard")
    assert dash_bp.domain_type == "dashboard"

    creative_bp = DomainSynthesizer.analyze_goal("Futuristic 3D generative particle visualizer app")
    assert creative_bp.domain_type == "creative"


def test_web_studio_complete_synthesis():
    goal = "Futuristic Cyberpunk 3D Portfolio for Senior Creative Technologist"
    files = ForgeWebStudio.synthesize_website(goal, ["Three.js interactive scene", "Dark mode"])

    assert "index.html" in files
    assert "style.css" in files
    assert "app.js" in files
    assert "README.md" in files

    html = files["index.html"]
    css = files["style.css"]
    js = files["app.js"]

    # 1. HTML Assertions
    assert "<!DOCTYPE html>" in html
    assert "<canvas" in html
    assert 'id="webstudio-3d-canvas"' in html or 'id="forge-3d-canvas"' in html
    assert 'class="bento-grid"' in html
    assert 'id="theme-toggle"' in html
    assert "three.min.js" in html
    assert "fonts.googleapis.com" in html

    # 2. CSS Assertions
    assert ":root" in css
    assert "backdrop-filter" in css
    assert "--glass-blur" in css or "blur(" in css
    assert "--bg-primary" in css or "--bg-base" in css
    assert "--accent-primary" in css or "--primary" in css
    assert ".bento-grid" in css
    assert ".tilt-card" in css

    # 3. JS Assertions
    assert "THREE.Scene" in js or "initThreeJSScene" in js
    assert "addEventListener" in js
    assert "perspectiveTilt" in js or "tilt-card" in js or "rotateX" in js

    # 4. Zero Placeholders Guarantee
    for forbidden in ["lorem ipsum", "project alpha", "project beta", "john doe", "untitled project"]:
        assert forbidden not in html.lower(), f"Forbidden placeholder found in HTML: {forbidden}"
        assert forbidden not in js.lower(), f"Forbidden placeholder found in JS: {forbidden}"


def test_three_d_engine_generation():
    engine_js = Web3DEngine.generate_engine_js()
    assert "THREE.PerspectiveCamera" in engine_js
    assert "renderer.render" in engine_js
    assert "initHighSpeedParticleCanvas" in engine_js or "Particle" in engine_js
    assert "requestAnimationFrame" in engine_js

    tilt_js = Web3DEngine.generate_card_tilt_js()
    assert "tilt-card" in tilt_js
    assert "perspective" in tilt_js or "transform" in tilt_js


def test_web_3d_builder_scaffolding(tmp_path: Path):
    builder = Web3DBuilder()
    manifest = builder.file_manifest("Build a 3D AI startup website")
    assert "index.html" in manifest.files_to_generate
    assert "style.css" in manifest.files_to_generate
    assert "app.js" in manifest.files_to_generate

    created = builder.scaffold_project("Build a 3D AI startup website", tmp_path)
    assert len(created) == 4
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "style.css").exists()
    assert (tmp_path / "app.js").exists()
    assert (tmp_path / "README.md").exists()

    # Verify quality analyzer passes on generated files
    analyzer = CodeQualityAnalyzer(tmp_path)
    aesthetic_check = analyzer.analyze_web_aesthetic_and_interactivity()
    assert aesthetic_check is not None
    assert aesthetic_check.status == "pass"
    assert aesthetic_check.evidence["canvas_detected"] is True
    assert aesthetic_check.evidence["glassmorphic_tokens"] is True
    assert len(aesthetic_check.evidence["failures"]) == 0


def test_quality_analyzer_detects_placeholders(tmp_path: Path):
    bad_html = "<html><body><h1>Project Alpha</h1><p>Lorem ipsum dolor sit amet</p></body></html>"
    (tmp_path / "index.html").write_text(bad_html, encoding="utf-8")
    (tmp_path / "style.css").write_text("body { color: red; }", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('hi');", encoding="utf-8")

    analyzer = CodeQualityAnalyzer(tmp_path)
    check = analyzer.analyze_web_aesthetic_and_interactivity()
    assert check is not None
    assert check.status == "fail"
    assert any("placeholder" in f.lower() for f in check.evidence["failures"])


@pytest.mark.asyncio
async def test_aesthetic_and_interactive_checker(tmp_path: Path):
    from app.core.config import Settings
    from app.core.workspace import WorkspaceManager
    from app.execution.engine import ExecutionEngine
    from app.verification.checkers import AestheticAndInteractiveChecker

    settings = Settings()
    settings.workspaces_dir = tmp_path / "workspaces"
    wm = WorkspaceManager(settings=settings)
    engine = ExecutionEngine(wm=wm)
    task_id = "test_aesthetic_task"

    # Synthesize complete 3D website in workspace
    files = ForgeWebStudio.synthesize_website("Futuristic 3D Portfolio")
    for p, content in files.items():
        wm.write_project_file(task_id, p, content)

    checker = AestheticAndInteractiveChecker()
    evidence = await checker.run_check(task_id, engine)

    assert evidence.passed is True
    assert evidence.exit_code == 0
    assert "Aesthetic verification passed" in evidence.stdout
    assert len(evidence.issues) == 0
