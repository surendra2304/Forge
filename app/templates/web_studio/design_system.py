"""
ForgeWebStudio Design System: Modern Visual Architecture & Design Tokens.
Inspired by Lovable, Bolt.new, and modern 3D web design principles.
Provides production-grade CSS design systems, glassmorphism tokens, bento grids, and responsive layouts.
"""


# CDN References for World-Class Web Apps
TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
LUCIDE_ICONS_CDN = '<script src="https://unpkg.com/lucide@latest"></script>'
GOOGLE_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">'
)
THREE_JS_CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'


def generate_modern_css_theme(
    theme_name: str = "futuristic_dark",
    primary_color: str = "#6366f1",
    accent_glow: str = "#a855f7",
) -> str:
    """Generate a complete, self-contained modern CSS design system with glassmorphism & dark/light mode."""
    return f"""/* ==========================================================================
   FORGE WebStudio 3.0 — Modern Design System (Glassmorphic / Futuristic)
   ========================================================================== */

:root {{
    --font-primary: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-heading: 'Space Grotesk', var(--font-primary);
    --font-body: 'Inter', var(--font-primary);

    /* Dynamic Theme Colors */
    --primary: {primary_color};
    --primary-hover: #4f46e5;
    --primary-light: rgba(99, 102, 241, 0.15);
    --accent: {accent_glow};
    --accent-glow: rgba(168, 85, 247, 0.4);

    /* Dark Surface Foundations (Default) */
    --bg-base: #090d16;
    --bg-surface: #0f172a;
    --bg-surface-elevated: #1e293b;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-highlight: rgba(255, 255, 255, 0.18);
    --border-glow: rgba(99, 102, 241, 0.4);

    /* Glassmorphism Tokens */
    --glass-bg: rgba(15, 23, 42, 0.65);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-blur: blur(16px);
    --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);

    /* Text Hierarchy */
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    /* Status Indicators */
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;

    /* Animations & Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-smooth: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-bounce: 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
}}

/* Light Mode Overrides */
[data-theme="light"] {{
    --bg-base: #f8fafc;
    --bg-surface: #ffffff;
    --bg-surface-elevated: #f1f5f9;
    --border-subtle: rgba(0, 0, 0, 0.08);
    --border-highlight: rgba(0, 0, 0, 0.15);
    --border-glow: rgba(99, 102, 241, 0.3);

    --glass-bg: rgba(255, 255, 255, 0.75);
    --glass-border: rgba(0, 0, 0, 0.08);
    --glass-shadow: 0 8px 24px 0 rgba(148, 163, 184, 0.2);

    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
}}

/* Global Reset & Box-Sizing */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html {{
    scroll-behavior: smooth;
    font-size: 16px;
}}

body {{
    font-family: var(--font-body);
    background-color: var(--bg-base);
    color: var(--text-primary);
    line-height: 1.6;
    overflow-x: hidden;
    position: relative;
    min-height: 100vh;
    transition: background-color var(--transition-smooth), color var(--transition-smooth);
}}

/* Background Ambient Glow */
.ambient-glow-layer {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}

.ambient-orb {{
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.25;
    animation: floatOrb 20s ease-in-out infinite alternate;
}}

.orb-1 {{
    top: -10%;
    left: -10%;
    width: 50vw;
    height: 50vw;
    background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
}}

.orb-2 {{
    bottom: -15%;
    right: -10%;
    width: 60vw;
    height: 60vw;
    background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
    animation-delay: -7s;
}}

@keyframes floatOrb {{
    0% {{ transform: translate(0, 0) scale(1); }}
    100% {{ transform: translate(60px, 40px) scale(1.1); }}
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-heading);
    font-weight: 700;
    line-height: 1.2;
    color: var(--text-primary);
}}

.gradient-text {{
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--primary) 50%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
}}

/* Glassmorphism Containers */
.glass-panel {{
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    box-shadow: var(--glass-shadow);
    border-radius: 1rem;
}}

.glass-card {{
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 1rem;
    padding: 1.5rem;
    transition: transform var(--transition-smooth), border-color var(--transition-smooth), box-shadow var(--transition-smooth);
    position: relative;
    overflow: hidden;
}}

.glass-card:hover {{
    transform: translateY(-4px);
    border-color: var(--border-glow);
    box-shadow: 0 12px 30px -10px var(--accent-glow);
}}

.tilt-card {{
    transform-style: preserve-3d;
    will-change: transform;
}}

/* Bento Grid Architecture */
.bento-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
}}

@media (min-width: 1024px) {{
    .bento-grid-3 {{
        grid-template-columns: repeat(3, 1fr);
    }}
    .bento-col-span-2 {{
        grid-column: span 2;
    }}
}}

/* Modern Buttons */
.btn-modern {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-family: var(--font-primary);
    font-weight: 600;
    font-size: 0.95rem;
    border-radius: 0.75rem;
    border: none;
    cursor: pointer;
    text-decoration: none;
    transition: all var(--transition-smooth);
}}

.btn-primary {{
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
    color: #ffffff;
    box-shadow: 0 4px 20px -2px var(--accent-glow);
}}

.btn-primary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 25px 0 var(--accent-glow);
}}

.btn-glass {{
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    color: var(--text-primary);
}}

.btn-glass:hover {{
    background: var(--bg-surface-elevated);
    border-color: var(--border-highlight);
    transform: translateY(-2px);
}}

/* Interactive Canvas / 3D Container */
.canvas-container {{
    position: relative;
    width: 100%;
    overflow: hidden;
}}

.hero-canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: auto;
    z-index: 1;
}}

.hero-content {{
    position: relative;
    z-index: 2;
    pointer-events: none;
}}

.hero-content * {{
    pointer-events: auto;
}}

/* Badges and Tags */
.pill-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-radius: 9999px;
    background: var(--primary-light);
    color: var(--primary);
    border: 1px solid rgba(99, 102, 241, 0.3);
}}

/* Toast Notifications */
.toast-container {{
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    pointer-events: none;
}}

.toast {{
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-radius: 0.75rem;
    background: var(--bg-surface-elevated);
    border: 1px solid var(--border-highlight);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    color: var(--text-primary);
    font-size: 0.9rem;
    transform: translateY(20px);
    opacity: 0;
    transition: all var(--transition-bounce);
}}

.toast.show {{
    transform: translateY(0);
    opacity: 1;
}}
"""
