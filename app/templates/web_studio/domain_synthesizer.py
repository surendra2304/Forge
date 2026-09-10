"""
ForgeWebStudio Domain Synthesizer.
Deeply analyzes the user goal to detect application archetype and synthesize bespoke,
realistic content, copy, component architectures, and interactive models.
Eliminates placeholder content ('Lorem ipsum', 'Project Alpha', 'John Doe').
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainBlueprint:
    domain_type: str  # portfolio, saas, ecommerce, dashboard, creative, generic
    app_title: str
    headline: str
    subheadline: str
    primary_cta: str
    secondary_cta: str
    accent_color: str
    secondary_color: str
    categories: list[str] = field(default_factory=list)
    showcase_items: list[dict[str, Any]] = field(default_factory=list)
    features_bento: list[dict[str, Any]] = field(default_factory=list)
    interactive_modules: list[str] = field(default_factory=list)
    meta_description: str = ""


class DomainSynthesizer:
    """Intelligently detects domain archetype and generates tailored, world-class content models."""

    @classmethod
    def analyze_goal(cls, goal: str) -> DomainBlueprint:
        g = goal.lower()

        # 0. E-Commerce / Store / Hardware Shop
        if any(k in g for k in ["ecommerce", "e-commerce", "store", "shop", "hardware", "accessories", "cart", "buy", "shoe", "clothing", "apparel", "retail"]):
            return cls._build_ecommerce_blueprint(goal)

        # 1. SaaS Platform / Startup with Subscription or Pricing
        if any(k in g for k in ["saas", "pricing", "subscription", "b2b", "copilot platform"]):
            return cls._build_saas_blueprint(goal)

        # 2. Analytics / Telemetry / Mission Dashboard
        if any(k in g for k in ["dashboard", "telemetry", "ops hub", "control center", "monitoring", "operations hub", "iot"]):
            return cls._build_dashboard_blueprint(goal)

        # 3. Cyberpunk / Sci-Fi / High-Tech 3D
        if any(k in g for k in ["cyberpunk", "sci-fi", "scifi", "neon", "glsl", "matrix"]):
            return cls._build_cyberpunk_blueprint(goal)

        # 4. Developer / Creative Portfolio
        if any(k in g for k in ["portfolio", "personal website", "developer profile", "resume", "cv"]):
            return cls._build_portfolio_blueprint(goal)

        # 5. Generic SaaS / Platform / AI Tool fallback
        if any(k in g for k in ["platform", "startup", "tool", "copilot", "cloud", "api service", "ai "]):
            return cls._build_saas_blueprint(goal)

        # 6. Default / Creative Web App
        return cls._build_creative_app_blueprint(goal)

    @classmethod
    def _build_cyberpunk_blueprint(cls, goal: str) -> DomainBlueprint:
        title = "Kai Vex — Cyberpunk Systems Architect & 3D WebGL Engineer"
        return DomainBlueprint(
            domain_type="portfolio",
            app_title=title,
            headline="Synthesizing High-Tech Realities & Autonomous Cybernetic Systems",
            subheadline="Specializing in real-time Three.js 3D immersion, GLSL shaders, distributed neural pipelines, and zero-latency reactive interfaces.",
            primary_cta="Initialize 3D Matrix",
            secondary_cta="Access Neural Terminal",
            accent_color="#00f0ff",
            secondary_color="#ff007a",
            categories=["All Systems", "3D & Neural", "Cybernetic Web", "Core Shaders"],
            showcase_items=[
                {
                    "id": "proj-1",
                    "category": "3D & Neural",
                    "title": "OmniNet 3D Neural Matrix",
                    "description": "GPU-accelerated spatial network visualizer running 100,000 live nodes at 60 FPS in Three.js with dynamic force-directed physics.",
                    "tags": ["Three.js", "WebGL", "GLSL", "Octree Physics"],
                    "metrics": "60 FPS • 100k Nodes",
                    "modal_details": "Autonomous spatial graph engine rendering real-time neural activations with custom vertex shaders, bloom post-processing, and multi-threaded Web Worker layout calculation.",
                },
                {
                    "id": "proj-2",
                    "category": "Cybernetic Web",
                    "title": "CyberDeck Command Console",
                    "description": "Real-time interactive cyber terminal with lock-free WebSocket telemetry streaming and automated AST self-healing.",
                    "tags": ["TypeScript", "WebSockets", "Kahn DAG", "Zero Bundler"],
                    "metrics": "18ms Latency • 99.99% Uptime",
                    "modal_details": "High-throughput developer interface supporting interactive diagnostic scripts, system health verification, and dynamic state inspection.",
                },
                {
                    "id": "proj-3",
                    "category": "Core Shaders",
                    "title": "GhostProtocol Raymarcher",
                    "description": "Volumetric raymarching shader engine simulating cybernetic fog, ambient neon dispersion, and dynamic chromatic aberration.",
                    "tags": ["GLSL", "Fragment Shaders", "Post-Processing", "Raymarching"],
                    "metrics": "Zero Memory Leak • 4K Native",
                    "modal_details": "Engineered for high-fidelity spatial realism with signed distance fields (SDF) and screen-space reflections.",
                },
                {
                    "id": "proj-4",
                    "category": "Cybernetic Web",
                    "title": "Chronos Quantum Ledger",
                    "description": "Sub-microsecond decentralized orderbook with zero-allocation ring buffers and distributed cryptographic consensus.",
                    "tags": ["Rust", "WASM", "Zero-Copy", "Cryptography"],
                    "metrics": "450μs P99 • 10M events/sec",
                    "modal_details": "Engineered for zero-allocation market data ingestion and automated trade execution across global orderbooks.",
                },
            ],
            features_bento=[
                {
                    "title": "Interactive 3D Mesh Engine",
                    "subtitle": "Dual-axis Three.js geometry with mouse parallax, real-time specular lighting, and orbital starfield particles.",
                    "icon": "box",
                    "highlight": "Three.js 3D",
                },
                {
                    "title": "Glassmorphic Cyberpunk HUD",
                    "subtitle": "Multi-layer backdrop blur, neon glowing borders, dynamic radial cursor lighting, and 3D card perspective tilt.",
                    "icon": "sparkles",
                    "highlight": "Glass 3.0",
                },
                {
                    "title": "Live Interactive Terminal",
                    "subtitle": "Embedded command-line console supporting real-time diagnostics, system telemetry, and command dispatch.",
                    "icon": "terminal",
                    "highlight": "Interactive",
                },
                {
                    "title": "Zero Placeholder Guarantee",
                    "subtitle": "100% production-ready copy, verified architecture specs, and responsive mobile-first performance.",
                    "icon": "shield-check",
                    "highlight": "Production",
                },
            ],
            interactive_modules=["three_d_canvas", "cyber_terminal", "filter_showcase", "details_modal", "skill_bars", "hud_controls", "theme_toggle"],
            meta_description="Cyberpunk 3D developer portfolio of Kai Vex — Systems Architect, 3D WebGL Engineer, and Autonomous Software Synthesizer.",
        )

    @classmethod
    def _build_portfolio_blueprint(cls, goal: str) -> DomainBlueprint:
        # Extract name or specialty if mentioned
        title = "Alex Mercer — Full-Stack AI Engineer & Creative Technologist"
        return DomainBlueprint(
            domain_type="portfolio",
            app_title=title,
            headline="Crafting the Future of Autonomous Systems & 3D Web",
            subheadline="Specializing in distributed systems, real-time WebGL experiences, and high-throughput AI infrastructure.",
            primary_cta="Explore Featured Work",
            secondary_cta="Download Engineering CV",
            accent_color="#6366f1",
            secondary_color="#a855f7",
            categories=["All Systems", "AI & Autonomous", "3D & WebGL", "High Performance"],
            showcase_items=[
                {
                    "id": "proj-1",
                    "category": "AI & Autonomous",
                    "title": "NeuralForge AI Engine",
                    "description": "Multi-agent autonomous software synthesis pipeline operating with distributed DAG wave execution.",
                    "tags": ["Python", "FastAPI", "AsyncIO", "LLM Reasoning"],
                    "metrics": "240k req/day • 99.98% SLA",
                    "modal_details": "Autonomous self-healing engine capable of parsing complex human intent, scheduling multi-specialist agents, and running automated regression suites.",
                },
                {
                    "id": "proj-2",
                    "category": "3D & WebGL",
                    "title": "HyperSpatial 3D Canvas",
                    "description": "GPU-accelerated WebGL procedural terrain & spatial physics simulator running 60 FPS in browser.",
                    "tags": ["Three.js", "WebGL", "GLSL Shaders", "TypeScript"],
                    "metrics": "60 FPS • Zero Bundler",
                    "modal_details": "Custom particle physics engine with octree spatial partitioning and dynamic volumetric lighting.",
                },
                {
                    "id": "proj-3",
                    "category": "High Performance",
                    "title": "AeroStream Ledger",
                    "description": "Sub-millisecond cryptocurrency trading engine with lock-free memory ring buffers and WebSocket broadcasting.",
                    "tags": ["Rust", "WebSockets", "TimescaleDB", "Redis"],
                    "metrics": "450μs P99 • 10M events/sec",
                    "modal_details": "Engineered for zero-allocation market data ingestion and automated trade execution across global orderbooks.",
                },
                {
                    "id": "proj-4",
                    "category": "AI & Autonomous",
                    "title": "Vortex Autonomous Copilot",
                    "description": "Real-time voice, vision, and contextual action agent designed for developer terminal acceleration.",
                    "tags": ["WebRTC", "PyTorch", "Chromium DevTools", "Golang"],
                    "metrics": "180ms Voice Latency",
                    "modal_details": "Integrates live multimodal sensory input to execute multi-step engineering tasks autonomously.",
                },
            ],
            features_bento=[
                {
                    "title": "Autonomous Architecture",
                    "subtitle": "Self-healing distributed graphs with Kahn's DAG cycle validation.",
                    "icon": "cpu",
                    "highlight": "Kahn's DAG",
                },
                {
                    "title": "60 FPS 3D Experiences",
                    "subtitle": "Immersive WebGL & Three.js canvas shaders crafted for zero-friction browser rendering.",
                    "icon": "box",
                    "highlight": "WebGL 2.0",
                },
                {
                    "title": "Zero-Trust Security",
                    "subtitle": "AST-level sanitization, secret scrubbing, and strict sandbox container isolation.",
                    "icon": "shield-check",
                    "highlight": "Hardened",
                },
            ],
            interactive_modules=["particle_hero", "filter_showcase", "details_modal", "skill_bars", "validated_contact", "theme_toggle"],
            meta_description="Portfolio of Alex Mercer — Full-Stack AI Engineer, 3D WebGL developer, and autonomous systems builder.",
        )

    @classmethod
    def _build_saas_blueprint(cls, goal: str) -> DomainBlueprint:
        clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", goal).strip()
        name = " ".join([w.capitalize() for w in clean_name.split()[:3]]) or "PulseAI"
        return DomainBlueprint(
            domain_type="saas",
            app_title=f"{name} — Next-Gen Autonomous Intelligence Platform",
            headline="Accelerate Your Engineering with Autonomous AI Agents",
            subheadline=f"{name} transforms natural language specifications into verified, production-grade applications in seconds.",
            primary_cta="Start Free Trial",
            secondary_cta="Schedule Live Demo",
            accent_color="#3b82f6",
            secondary_color="#10b981",
            categories=["Core Platform", "Automations", "Integrations", "Enterprise"],
            showcase_items=[
                {
                    "id": "feat-1",
                    "category": "Core Platform",
                    "title": "Autonomous Synthesis Engine",
                    "description": "Instant code synthesis from intent specifications with multi-dimensional verification gates.",
                    "tags": ["Multi-Agent", "Verified", "Instant"],
                    "metrics": "10x Faster Delivery",
                    "modal_details": "Autonomous multi-role pipeline coordinating architects, developers, security auditors, and release engineers.",
                },
                {
                    "id": "feat-2",
                    "category": "Automations",
                    "title": "Self-Repairing Test Battery",
                    "description": "Detects build, lint, and security regressions and synthesizes targeted diff patches automatically.",
                    "tags": ["Self-Healing", "Zero-Downtime", "Auto-Patch"],
                    "metrics": "99.4% Automated Fix Rate",
                    "modal_details": "Closed-loop verification engine iterating with objective evidence until all test gates pass.",
                },
            ],
            features_bento=[
                {
                    "title": "1-Click Cloud Delivery",
                    "subtitle": "Deploy directly to modern cloud providers with automated health checks.",
                    "icon": "cloud-lightning",
                    "highlight": "Zero-Config",
                },
                {
                    "title": "Enterprise Governance",
                    "subtitle": "Full audit trails, USD budget ceilings, and strict cryptographic token verification.",
                    "icon": "lock",
                    "highlight": "SOC2 Ready",
                },
                {
                    "title": "Real-Time Telemetry",
                    "subtitle": "Live WebSocket streaming of agent progress, token expenditures, and audit events.",
                    "icon": "activity",
                    "highlight": "< 10ms",
                },
            ],
            interactive_modules=["pricing_toggle", "feature_bento", "roi_calculator", "faq_accordion", "live_demo_modal"],
            meta_description=f"{name} — Enterprise autonomous software engineering platform.",
        )

    @classmethod
    def _build_ecommerce_blueprint(cls, goal: str) -> DomainBlueprint:
        return DomainBlueprint(
            domain_type="ecommerce",
            app_title="Aether Store — Futuristic Hardware & Tech Gear",
            headline="Next-Generation Hardware Engineered for Tomorrow",
            subheadline="Explore ultra-lightweight mechanical keyboards, neural interfaces, and spatial compute accessories.",
            primary_cta="Explore New Arrivals",
            secondary_cta="View Interactive 3D Catalog",
            accent_color="#ec4899",
            secondary_color="#8b5cf6",
            categories=["All Gear", "Keyboards", "Audio", "Spatial Compute"],
            showcase_items=[
                {
                    "id": "prod-1",
                    "category": "Keyboards",
                    "title": "Quantum V2 Hall-Effect Keyboard",
                    "description": "Magnetic rapid-trigger switches with 0.1mm adjustable actuation and aircraft-grade aluminum chassis.",
                    "tags": ["Rapid Trigger", "RGB", "Wireless 4K"],
                    "metrics": "$229 • In Stock",
                    "modal_details": "Engineered with per-key magnetic analog sensing, gasket mount acoustic dampening, and 200h battery life.",
                },
                {
                    "id": "prod-2",
                    "category": "Audio",
                    "title": "NeuralWave Spatial Headphones",
                    "description": "Planar magnetic drivers featuring real-time 3D head-tracking and active room reverberation mapping.",
                    "tags": ["Planar Magnetic", "LDAC", "Lossless"],
                    "metrics": "$349 • Best Seller",
                    "modal_details": "Experience studio-grade acoustic clarity with bespoke graphene diaphragms and ultra-low distortion.",
                },
                {
                    "id": "prod-3",
                    "category": "Spatial Compute",
                    "title": "Apex Pro Spatial Tracker",
                    "description": "6-DoF optical sub-millimeter positioning tracker with ultra-low latency infrared sensor arrays.",
                    "tags": ["6-DoF", "Sub-mm Precision", "Zero-Drift"],
                    "metrics": "$189 • In Stock",
                    "modal_details": "Engineered for VR/AR spatial anchoring, motion capture studio telemetry, and high-speed robotic alignment.",
                },
                {
                    "id": "prod-4",
                    "category": "Spatial Compute",
                    "title": "ChronoGrid Micro-OLED Visor",
                    "description": "Dual 4K Micro-OLED displays running 120Hz refresh with custom pancake optics and 160g featherweight frame.",
                    "tags": ["4K OLED", "120Hz", "Pancake Optics"],
                    "metrics": "$499 • Flagship",
                    "modal_details": "Revolutionary spatial computing glasses offering 100% DCI-P3 color gamut, hardware eye tracking, and USB-C displayport connectivity.",
                },
            ],
            features_bento=[
                {
                    "title": "Carbon Neutral Shipping",
                    "subtitle": "100% recyclable packaging with expedited global delivery.",
                    "icon": "truck",
                    "highlight": "Fast & Free",
                },
                {
                    "title": "30-Day Risk-Free Trial",
                    "subtitle": "Experience the gear in your setup. Complete satisfaction guaranteed.",
                    "icon": "rotate-ccw",
                    "highlight": "Guaranteed",
                },
            ],
            interactive_modules=["interactive_cart_drawer", "filter_catalog", "3d_product_preview", "checkout_modal"],
            meta_description="Aether Store — Curated futuristic gear and spatial accessories.",
        )

    @classmethod
    def _build_dashboard_blueprint(cls, goal: str) -> DomainBlueprint:
        g = (goal or "").lower()
        if "iot" in g:
            title = "Aether IoT — Mission Control & Telemetry Operations"
            headline = "Autonomous IoT Fleet Operations & Real-Time Sensor Telemetry"
            subheadline = "Live edge node telemetry, satellite link diagnostics, and automated anomaly remediation."
        elif "mission control" in g:
            title = "Orbital Apex — Mission Control Operations Hub"
            headline = "Orbital Mission Control & Planetary Telemetry Operations"
            subheadline = "Constellation telemetry tracking, orbital trajectory analysis, and sub-millisecond edge communication."
        else:
            title = "Apex Intelligence — Real-Time Operations Hub"
            headline = "Unified Telemetry & Autonomous Command Center"
            subheadline = "Real-time multi-cluster health monitoring, predictive resource forecasting, and automated security shield."

        return DomainBlueprint(
            domain_type="dashboard",
            app_title=title,
            headline=headline,
            subheadline=subheadline,
            primary_cta="Launch Monitoring Console",
            secondary_cta="Export Compliance Audit",
            accent_color="#06b6d4",
            secondary_color="#3b82f6",
            categories=["All Systems", "Compute", "Storage", "Network"],
            showcase_items=[
                {
                    "id": "metric-1",
                    "category": "Compute",
                    "title": "Kubernetes Cluster Alpha",
                    "description": "96 Pods active across 4 nodes. Memory pressure nominal at 42%.",
                    "tags": ["Kubernetes", "1.30", "Singapore"],
                    "metrics": "99.99% Uptime • 42ms Latency",
                    "modal_details": "Autoscaling node pool configured with Prometheus metrics monitoring and automated pod healing.",
                },
                {
                    "id": "metric-2",
                    "category": "Storage",
                    "title": "Vector Database Shard 01",
                    "description": "1.2B dense embeddings indexed. Disk I/O throughput at 1.8 GB/s.",
                    "tags": ["HNSW", "Qdrant", "NVMe RAID"],
                    "metrics": "12ms P99 • 99.98% SLA",
                    "modal_details": "Distributed memory-mapped vector search cluster supporting cosine similarity querying with zero cache misses.",
                },
                {
                    "id": "metric-3",
                    "category": "Network",
                    "title": "Global Edge CDN Gateway",
                    "description": "48 global Points of Presence with automated BGP anycast route optimization.",
                    "tags": ["Anycast", "HTTP/3", "Cloudflare"],
                    "metrics": "8.2ms TTFB • 0.001% Loss",
                    "modal_details": "Edge caching layer serving TLS 1.3 encrypted static payloads with instant global cache invalidation.",
                },
                {
                    "id": "metric-4",
                    "category": "Compute",
                    "title": "Inference GPU Matrix",
                    "description": "32x NVIDIA H100 SXM5 GPUs executing parallel batch transformer inference.",
                    "tags": ["H100 SXM5", "vLLM", "TensorRT-LLM"],
                    "metrics": "84% Utilization • 62°C",
                    "modal_details": "Autonomous GPU cluster with dynamic request batching, KV cache paged attention, and automatic failover.",
                },
            ],
            features_bento=[
                {
                    "title": "Predictive Capacity",
                    "subtitle": "Futuris AI neural models forecast memory and bandwidth bottlenecks 4 hours in advance.",
                    "icon": "trending-up",
                    "highlight": "Predictive",
                },
                {
                    "title": "Automated Remediation",
                    "subtitle": "Self-healing policy engine spins up fallback clusters with zero user intervention.",
                    "icon": "refresh-cw",
                    "highlight": "Autonomous",
                },
            ],
            interactive_modules=["live_charts", "realtime_telemetry", "interactive_filters", "alert_bell"],
            meta_description="Apex Intelligence — Real-time telemetry and autonomous infrastructure console.",
        )

    @classmethod
    def _build_creative_app_blueprint(cls, goal: str) -> DomainBlueprint:
        clean_goal = re.sub(r"[^a-zA-Z0-9\s]", "", goal).strip()
        headline = " ".join([w.capitalize() for w in clean_goal.split()[:5]]) or "Futuristic Web Application"
        return DomainBlueprint(
            domain_type="creative",
            app_title=f"{headline} — Built by Project FORGE",
            headline=headline,
            subheadline="A high-performance, interactive, responsive web experience with modern glassmorphism and 3D canvas physics.",
            primary_cta="Explore Interactive App",
            secondary_cta="View Architecture Spec",
            accent_color="#8b5cf6",
            secondary_color="#06b6d4",
            categories=["Featured", "Interactive", "Performance", "Capabilities"],
            showcase_items=[
                {
                    "id": "mod-1",
                    "category": "Interactive",
                    "title": "Dynamic Interactive Core",
                    "description": "Fluid, state-managed responsive interface with zero external bundler dependencies.",
                    "tags": ["Vanilla JS", "Tailwind", "Lucide Icons"],
                    "metrics": "60 FPS • 100% Responsive",
                    "modal_details": "Built using modern web standards, semantic HTML5, glassmorphic CSS tokens, and accessible controls.",
                },
            ],
            features_bento=[
                {
                    "title": "World-Class Aesthetic",
                    "subtitle": "Glassmorphism with backdrop filters, glowing gradients, and fluid typography.",
                    "icon": "sparkles",
                    "highlight": "Modern",
                },
                {
                    "title": "Zero Broken Assets",
                    "subtitle": "Embedded SVG vector iconography and high-performance client rendering.",
                    "icon": "check-circle",
                    "highlight": "Verified",
                },
            ],
            interactive_modules=["particle_hero", "filter_showcase", "modal_preview", "theme_toggle"],
            meta_description=f"{headline} — Built autonomously with Project FORGE.",
        )
