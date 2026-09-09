"""
ForgeWebStudio Master Website & App Generator.
Synthesizes world-class, 3D interactive, responsive websites on par with Lovable, Bolt.new, and Durable.
"""

from typing import Any

from app.templates.web_studio.design_system import (
    GOOGLE_FONTS_LINK,
    LUCIDE_ICONS_CDN,
    THREE_JS_CDN,
    generate_modern_css_theme,
)
from app.templates.web_studio.domain_synthesizer import DomainBlueprint, DomainSynthesizer
from app.templates.web_studio.three_d_engine import (
    generate_3d_tilt_script,
    generate_three_d_scene_script,
)


class ForgeWebStudio:
    """Master procedural synthesis engine for modern 3D web applications and attractive websites."""

    @classmethod
    def synthesize_website(
        cls,
        goal: str,
        requirements: list[str] | None = None,
        custom_options: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Synthesizes a complete, production-grade 3D interactive web project.
        Returns a mapping of relative file paths to file contents.
        """
        blueprint = DomainSynthesizer.analyze_goal(goal)
        options = custom_options or {}

        primary_hex = options.get("primary_color", blueprint.accent_color)
        secondary_hex = options.get("secondary_color", blueprint.secondary_color)

        html_content = cls._generate_html(blueprint, primary_hex, secondary_hex)
        css_content = generate_modern_css_theme(
            primary_color=primary_hex,
            accent_glow=secondary_hex,
        )
        js_content = cls._generate_js(blueprint, primary_hex, secondary_hex)
        readme_content = cls._generate_readme(goal, blueprint)

        return {
            "index.html": html_content,
            "style.css": css_content,
            "app.js": js_content,
            "README.md": readme_content,
        }

    @classmethod
    def _generate_html(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        # Generate category filter buttons
        filter_buttons = []
        for i, cat in enumerate(blueprint.categories):
            active_class = "active" if i == 0 else ""
            filter_buttons.append(
                f'<button class="filter-btn {active_class}" data-filter="{cat}">{cat}</button>'
            )
        filters_html = "\n                ".join(filter_buttons)

        # Generate showcase cards
        cards_html = []
        for item in blueprint.showcase_items:
            tags_html = "".join([f'<span class="pill-badge">{t}</span>' for t in item["tags"]])
            cards_html.append(f"""
            <article class="glass-card showcase-card tilt-card" data-category="{item['category']}" data-id="{item['id']}">
                <div class="card-header-bar">
                    <span class="category-pill">{item['category']}</span>
                    <span class="metrics-pill">{item.get('metrics', '')}</span>
                </div>
                <h3 class="card-title">{item['title']}</h3>
                <p class="card-desc">{item['description']}</p>
                <div class="card-tags">{tags_html}</div>
                <button class="btn-modern btn-glass btn-modal-trigger"
                        data-title="{item['title']}"
                        data-desc="{item['modal_details']}"
                        data-metrics="{item.get('metrics', '')}"
                        data-category="{item['category']}">
                    <span>Explore Details</span>
                    <i data-lucide="arrow-right" class="w-4 h-4"></i>
                </button>
            </article>""")
        showcase_grid_html = "\n".join(cards_html)

        # Generate bento features
        bento_cards = []
        for feat in blueprint.features_bento:
            bento_cards.append(f"""
            <div class="glass-card bento-card tilt-card">
                <div class="bento-icon-box">
                    <i data-lucide="{feat.get('icon', 'sparkles')}" class="w-6 h-6 text-indigo-400"></i>
                </div>
                <div class="bento-badge">{feat.get('highlight', 'Feature')}</div>
                <h4 class="bento-title">{feat['title']}</h4>
                <p class="bento-desc">{feat['subtitle']}</p>
            </div>""")
        bento_grid_html = "\n".join(bento_cards)

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blueprint.app_title}</title>
    <meta name="description" content="{blueprint.meta_description}">

    <!-- Design System Fonts & CDNs -->
    {GOOGLE_FONTS_LINK}
    {THREE_JS_CDN}
    {LUCIDE_ICONS_CDN}
    <link rel="stylesheet" href="style.css">

    <style>
        /* Component Specific Layout Additions */
        .navbar-brand {{
            font-family: var(--font-heading);
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-primary);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .category-pill {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--primary);
            text-transform: uppercase;
        }}
        .metrics-pill {{
            font-size: 0.75rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            border: 1px solid var(--border-subtle);
        }}
        .card-header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        .card-title {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
        }}
        .card-desc {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        .card-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 1.25rem;
        }}
        .filter-container {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 2.5rem;
        }}
        .filter-btn {{
            padding: 0.5rem 1.25rem;
            border-radius: 9999px;
            background: var(--glass-bg);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all var(--transition-smooth);
        }}
        .filter-btn.active, .filter-btn:hover {{
            background: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
            box-shadow: 0 4px 15px -3px var(--accent-glow);
        }}
        .modal-backdrop {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        .modal-backdrop.open {{
            display: flex;
            opacity: 1;
        }}
        .modal-dialog {{
            background: var(--bg-surface);
            border: 1px solid var(--border-highlight);
            border-radius: 1.25rem;
            width: 100%;
            max-width: 600px;
            padding: 2rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
            position: relative;
            transform: scale(0.95);
            transition: transform 0.3s ease;
        }}
        .modal-backdrop.open .modal-dialog {{
            transform: scale(1);
        }}
        .modal-close-btn {{
            position: absolute;
            top: 1.25rem;
            right: 1.25rem;
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.25rem;
        }}
        .modal-close-btn:hover {{
            color: var(--text-primary);
        }}
        .bento-icon-box {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: rgba(99, 102, 241, 0.12);
            border: 1px solid rgba(99, 102, 241, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
        }}
        .bento-badge {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        .bento-title {{
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }}
        .bento-desc {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <!-- Ambient Background Glow -->
    <div class="ambient-glow-layer">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
    </div>

    <!-- Navigation Bar -->
    <header class="glass-panel" style="position: sticky; top: 1rem; margin: 1rem auto; max-width: 1200px; width: calc(100% - 2rem); z-index: 50; padding: 0.75rem 1.5rem; border-radius: 9999px;">
        <nav style="display: flex; justify-content: space-between; align-items: center;">
            <a href="#" class="navbar-brand">
                <i data-lucide="zap" class="text-indigo-400"></i>
                <span class="gradient-text">{blueprint.app_title.split('—')[0].strip()}</span>
            </a>

            <div style="display: flex; align-items: center; gap: 2rem;">
                <div style="display: flex; gap: 1.5rem;" class="nav-links">
                    <a href="#showcase" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: color 0.2s;">Showcase</a>
                    <a href="#features" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: color 0.2s;">Capabilities</a>
                    <a href="#contact" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: color 0.2s;">Connect</a>
                </div>

                <button id="theme-toggle" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px;" aria-label="Toggle Theme">
                    <i data-lucide="sun" id="theme-icon-sun" style="display: none; width: 18px; height: 18px;"></i>
                    <i data-lucide="moon" id="theme-icon-moon" style="display: inline; width: 18px; height: 18px;"></i>
                </button>
            </div>
        </nav>
    </header>

    <!-- Main Content Area -->
    <main>
        <!-- 3D Interactive Hero Section -->
        <section class="canvas-container" style="min-height: 85vh; display: flex; align-items: center; justify-content: center; padding: 4rem 1.5rem; text-align: center;">
            <canvas id="webstudio-3d-canvas" class="hero-canvas"></canvas>

            <div class="hero-content" style="max-width: 850px; margin: 0 auto;">
                <div style="margin-bottom: 1.5rem;">
                    <span class="pill-badge">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); display: inline-block; box-shadow: 0 0 10px var(--success);"></span>
                        Next-Generation Autonomous Experience
                    </span>
                </div>

                <h1 style="font-size: clamp(2.5rem, 6vw, 4.5rem); margin-bottom: 1.5rem; letter-spacing: -0.03em;">
                    {blueprint.headline}
                </h1>

                <p style="font-size: clamp(1.1rem, 2vw, 1.35rem); color: var(--text-secondary); margin-bottom: 2.5rem; max-width: 680px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    {blueprint.subheadline}
                </p>

                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                    <a href="#showcase" class="btn-modern btn-primary">
                        <span>{blueprint.primary_cta}</span>
                        <i data-lucide="sparkles" class="w-4 h-4"></i>
                    </a>
                    <a href="#contact" class="btn-modern btn-glass">
                        <span>{blueprint.secondary_cta}</span>
                        <i data-lucide="arrow-right" class="w-4 h-4"></i>
                    </a>
                </div>
            </div>
        </section>

        <!-- Interactive Showcase / Bento Filter Section -->
        <section id="showcase" style="padding: 6rem 1.5rem; max-width: 1200px; margin: 0 auto;">
            <div style="text-align: center; margin-bottom: 3.5rem;">
                <span class="pill-badge" style="margin-bottom: 0.75rem;">Interactive Showcase</span>
                <h2 style="font-size: 2.5rem; margin-bottom: 1rem;">Engineered for Impact</h2>
                <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto;">
                    Filter and inspect interactive system modules crafted with 3D perspective dynamics.
                </p>
            </div>

            <!-- Filter Controls -->
            <div class="filter-container">
                {filters_html}
            </div>

            <!-- Cards Grid -->
            <div class="bento-grid">
                {showcase_grid_html}
            </div>
        </section>

        <!-- Capabilities Bento Section -->
        <section id="features" style="padding: 6rem 1.5rem; max-width: 1200px; margin: 0 auto;">
            <div style="text-align: center; margin-bottom: 3.5rem;">
                <span class="pill-badge" style="margin-bottom: 0.75rem;">System Architecture</span>
                <h2 style="font-size: 2.5rem; margin-bottom: 1rem;">Core Capabilities & Features</h2>
                <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto;">
                    Built with high-throughput primitives, sub-millisecond execution loops, and verified telemetry.
                </p>
            </div>

            <div class="bento-grid bento-grid-3">
                {bento_grid_html}
            </div>
        </section>

        <!-- Interactive Contact & Submission Section -->
        <section id="contact" style="padding: 6rem 1.5rem; max-width: 700px; margin: 0 auto;">
            <div class="glass-panel" style="padding: 3rem 2.5rem; border-radius: 1.5rem;">
                <div style="text-align: center; margin-bottom: 2.5rem;">
                    <span class="pill-badge" style="margin-bottom: 0.75rem;">Initiate Transmission</span>
                    <h2 style="font-size: 2.25rem; margin-bottom: 0.75rem;">Let's Build Together</h2>
                    <p style="color: var(--text-secondary); font-size: 0.95rem;">
                        Submit project requirements or architectural inquiries below.
                    </p>
                </div>

                <form id="contact-form" novalidate style="display: flex; flex-direction: column; gap: 1.25rem;">
                    <div>
                        <label for="form-name" style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-secondary);">Full Name</label>
                        <input type="text" id="form-name" name="name" required placeholder="e.g. Elena Rostova"
                               style="width: 100%; padding: 0.85rem 1rem; border-radius: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-primary); font-family: inherit; font-size: 0.95rem; outline: none; transition: border-color 0.2s;">
                        <span id="name-error" style="color: var(--danger); font-size: 0.75rem; display: none; margin-top: 0.25rem;">Please provide your name.</span>
                    </div>

                    <div>
                        <label for="form-email" style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-secondary);">Work Email</label>
                        <input type="email" id="form-email" name="email" required placeholder="elena@hyperion.ai"
                               style="width: 100%; padding: 0.85rem 1rem; border-radius: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-primary); font-family: inherit; font-size: 0.95rem; outline: none; transition: border-color 0.2s;">
                        <span id="email-error" style="color: var(--danger); font-size: 0.75rem; display: none; margin-top: 0.25rem;">Valid email address required.</span>
                    </div>

                    <div>
                        <label for="form-message" style="display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-secondary);">Project Scope or Inquiries</label>
                        <textarea id="form-message" name="message" rows="4" required placeholder="Describe system architecture, performance requirements, or timeline..."
                                  style="width: 100%; padding: 0.85rem 1rem; border-radius: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); color: var(--text-primary); font-family: inherit; font-size: 0.95rem; outline: none; transition: border-color 0.2s; resize: vertical;"></textarea>
                        <span id="message-error" style="color: var(--danger); font-size: 0.75rem; display: none; margin-top: 0.25rem;">Message must be at least 10 characters.</span>
                    </div>

                    <button type="submit" class="btn-modern btn-primary" style="padding: 0.95rem; margin-top: 0.5rem; width: 100%;">
                        <span>Send Transmission</span>
                        <i data-lucide="send" class="w-4 h-4"></i>
                    </button>
                </form>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer style="padding: 3rem 1.5rem; border-top: 1px solid var(--border-subtle); text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        <p>&copy; 2026 {blueprint.app_title.split('—')[0].strip()}. Synthesized autonomously by <strong>Project FORGE 3.0</strong>.</p>
    </footer>

    <!-- Interactive Details Modal Dialog -->
    <div id="details-modal" class="modal-backdrop" role="dialog" aria-modal="true" aria-hidden="true">
        <div class="modal-dialog">
            <button class="modal-close-btn" id="modal-close" aria-label="Close modal">&times;</button>
            <div style="margin-bottom: 1rem;">
                <span id="modal-category" class="pill-badge">Category</span>
                <span id="modal-metrics" style="font-size: 0.8rem; color: var(--text-muted); margin-left: 0.5rem;"></span>
            </div>
            <h3 id="modal-title" style="font-size: 1.5rem; margin-bottom: 1rem;">Module Details</h3>
            <p id="modal-desc" style="color: var(--text-secondary); line-height: 1.6; margin-bottom: 1.5rem;"></p>
            <button class="btn-modern btn-primary" id="modal-action-btn" style="width: 100%;">
                <span>Confirm Selection</span>
                <i data-lucide="check" class="w-4 h-4"></i>
            </button>
        </div>
    </div>

    <!-- Toast Container -->
    <div id="toast-container" class="toast-container" aria-live="polite"></div>

    <!-- Interactive Logic -->
    <script src="app.js"></script>
    <script>
        // Render Lucide Icons
        if (typeof lucide !== 'undefined') {{
            lucide.createIcons();
        }}
    </script>
</body>
</html>
"""

    @classmethod
    def _generate_js(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        canvas_script = generate_three_d_scene_script(
            canvas_id="webstudio-3d-canvas",
            primary_hex=primary_hex,
            accent_hex=secondary_hex,
        )
        tilt_script = generate_3d_tilt_script()

        return f"""// ==========================================================================
// ForgeWebStudio 3.0 — Interactive Runtime & State Management Engine
// ==========================================================================

{canvas_script}

{tilt_script}

document.addEventListener("DOMContentLoaded", () => {{
    // 1. Dark/Light Theme Switcher with localStorage persistence
    const themeBtn = document.getElementById("theme-toggle");
    const sunIcon = document.getElementById("theme-icon-sun");
    const moonIcon = document.getElementById("theme-icon-moon");

    function applyTheme(theme) {{
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("webstudio-theme", theme);
        if (theme === "light") {{
            if (sunIcon) sunIcon.style.display = "inline";
            if (moonIcon) moonIcon.style.display = "none";
        }} else {{
            if (sunIcon) sunIcon.style.display = "none";
            if (moonIcon) moonIcon.style.display = "inline";
        }}
    }}

    const savedTheme = localStorage.getItem("webstudio-theme") ||
        (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    applyTheme(savedTheme);

    if (themeBtn) {{
        themeBtn.addEventListener("click", () => {{
            const current = document.documentElement.getAttribute("data-theme");
            applyTheme(current === "dark" ? "light" : "dark");
        }});
    }}

    // 2. Interactive Category Filter
    const filterButtons = document.querySelectorAll(".filter-btn");
    const showcaseCards = document.querySelectorAll(".showcase-card");

    filterButtons.forEach(btn => {{
        btn.addEventListener("click", () => {{
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const filterValue = btn.getAttribute("data-filter");
            showcaseCards.forEach(card => {{
                const cardCategory = card.getAttribute("data-category");
                if (filterValue === "All Systems" || filterValue === "Featured" || filterValue === "All Gear" || cardCategory === filterValue) {{
                    card.style.display = "block";
                    setTimeout(() => {{
                        card.style.opacity = "1";
                        card.style.transform = "translateY(0)";
                    }}, 20);
                }} else {{
                    card.style.opacity = "0";
                    card.style.transform = "translateY(10px)";
                    setTimeout(() => {{
                        card.style.display = "none";
                    }}, 250);
                }}
            }});
        }});
    }});

    // 3. Interactive Details Modal
    const modal = document.getElementById("details-modal");
    const modalClose = document.getElementById("modal-close");
    const modalTitle = document.getElementById("modal-title");
    const modalDesc = document.getElementById("modal-desc");
    const modalCategory = document.getElementById("modal-category");
    const modalMetrics = document.getElementById("modal-metrics");
    const modalActionBtn = document.getElementById("modal-action-btn");

    function openModal(title, desc, category, metrics) {{
        if (!modal) return;
        modalTitle.textContent = title;
        modalDesc.textContent = desc;
        modalCategory.textContent = category;
        modalMetrics.textContent = metrics;
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    }}

    function closeModal() {{
        if (!modal) return;
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    }}

    document.querySelectorAll(".btn-modal-trigger").forEach(btn => {{
        btn.addEventListener("click", () => {{
            openModal(
                btn.getAttribute("data-title"),
                btn.getAttribute("data-desc"),
                btn.getAttribute("data-category"),
                btn.getAttribute("data-metrics")
            );
        }});
    }});

    if (modalClose) modalClose.addEventListener("click", closeModal);
    if (modal) {{
        modal.addEventListener("click", (e) => {{
            if (e.target === modal) closeModal();
        }});
    }}
    document.addEventListener("keydown", (e) => {{
        if (e.key === "Escape" && modal && modal.classList.contains("open")) closeModal();
    }});

    if (modalActionBtn) {{
        modalActionBtn.addEventListener("click", () => {{
            closeModal();
            showToast("Action Confirmed", "Module parameter locked into active context.", "success");
        }});
    }}

    // 4. Contact Form Validation with Animated Toast
    const form = document.getElementById("contact-form");
    if (form) {{
        form.addEventListener("submit", (e) => {{
            e.preventDefault();
            const nameInput = document.getElementById("form-name");
            const emailInput = document.getElementById("form-email");
            const messageInput = document.getElementById("form-message");

            let isValid = true;

            // Name check
            if (!nameInput.value.trim()) {{
                document.getElementById("name-error").style.display = "block";
                nameInput.style.borderColor = "var(--danger)";
                isValid = false;
            }} else {{
                document.getElementById("name-error").style.display = "none";
                nameInput.style.borderColor = "var(--border-subtle)";
            }}

            // Email check
            const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            if (!emailRegex.test(emailInput.value.trim())) {{
                document.getElementById("email-error").style.display = "block";
                emailInput.style.borderColor = "var(--danger)";
                isValid = false;
            }} else {{
                document.getElementById("email-error").style.display = "none";
                emailInput.style.borderColor = "var(--border-subtle)";
            }}

            // Message check
            if (messageInput.value.trim().length < 10) {{
                document.getElementById("message-error").style.display = "block";
                messageInput.style.borderColor = "var(--danger)";
                isValid = false;
            }} else {{
                document.getElementById("message-error").style.display = "none";
                messageInput.style.borderColor = "var(--border-subtle)";
            }}

            if (isValid) {{
                showToast("Transmission Received", `Thank you, ${{nameInput.value.trim()}}. We will respond shortly.`, "success");
                form.reset();
            }}
        }});
    }}

    // 5. Toast Notification System
    window.showToast = function(title, message, type = "info") {{
        const container = document.getElementById("toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = "toast";
        toast.innerHTML = `
            <div style="width: 10px; height: 10px; border-radius: 50%; background: ${{type === 'success' ? 'var(--success)' : 'var(--primary)'}};"></div>
            <div>
                <strong style="display: block; font-size: 0.85rem;">${{title}}</strong>
                <span style="font-size: 0.8rem; color: var(--text-secondary);">${{message}}</span>
            </div>
        `;
        container.appendChild(toast);

        setTimeout(() => toast.classList.add("show"), 20);
        setTimeout(() => {{
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 400);
        }}, 4000);
    }};
}});
"""

    @classmethod
    def _generate_readme(cls, goal: str, blueprint: DomainBlueprint) -> str:
        return f"""# {blueprint.app_title}

Generated autonomously by **Project FORGE 3.0 (WebStudio Engine)**.

## 🌟 Architectural Features
- **3D & Interactive Canvas**: Three.js WebGL interactive 3D geometry with high-performance 60 FPS particle physics fallback.
- **Modern Glassmorphic Design System**: Tailwind CSS, Lucide vector icons, Google Fonts typography scale, and responsive bento grids.
- **Zero External Bundler**: Runs instantly with zero `npm install` or node compilation required.
- **Interactive State**: Real-time category filtering, modal dialog inspection, client-side form validation, and toast notification alerts.
- **Theme Resilience**: Built-in dark/light mode toggle with `localStorage` memory.

## 🚀 Instant Preview
```powershell
python -m http.server 5000
```
Open [http://localhost:5000](http://localhost:5000) in your browser.
"""
