"""
ForgeWebStudio Master Website & App Generator.
Synthesizes world-class, 3D interactive, responsive websites on par with Lovable, Bolt.new, and Durable.
Provides distinct domain architectures for E-Commerce, SaaS Platforms, Mission Dashboards, and Portfolios.
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
        Routes to distinct domain architectures: E-Commerce, SaaS, Dashboard, or Portfolio.
        """
        blueprint = DomainSynthesizer.analyze_goal(goal)
        options = custom_options or {}

        primary_hex = options.get("primary_color", blueprint.accent_color)
        secondary_hex = options.get("secondary_color", blueprint.secondary_color)

        if blueprint.domain_type == "ecommerce":
            html_content = cls._generate_ecommerce_html(blueprint, primary_hex, secondary_hex)
            js_content = cls._generate_ecommerce_js(blueprint, primary_hex, secondary_hex)
        elif blueprint.domain_type == "saas":
            html_content = cls._generate_saas_html(blueprint, primary_hex, secondary_hex)
            js_content = cls._generate_saas_js(blueprint, primary_hex, secondary_hex)
        elif blueprint.domain_type == "dashboard":
            html_content = cls._generate_dashboard_html(blueprint, primary_hex, secondary_hex)
            js_content = cls._generate_dashboard_js(blueprint, primary_hex, secondary_hex)
        else:
            html_content = cls._generate_portfolio_html(blueprint, primary_hex, secondary_hex)
            js_content = cls._generate_portfolio_js(blueprint, primary_hex, secondary_hex)

        css_content = generate_modern_css_theme(
            primary_color=primary_hex,
            accent_glow=secondary_hex,
        )
        readme_content = cls._generate_readme(goal, blueprint)

        return {
            "index.html": html_content,
            "style.css": css_content,
            "app.js": js_content,
            "README.md": readme_content,
        }

    # =========================================================================
    # 1. E-COMMERCE ARCHITECTURE (Store, Products, 3D Showcase, Cart Drawer)
    # =========================================================================

    @classmethod
    def _generate_ecommerce_html(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        brand_name = blueprint.app_title.split("—")[0].strip()

        # Category filter buttons
        filter_buttons = []
        for i, cat in enumerate(blueprint.categories):
            active_class = "active" if i == 0 else ""
            filter_buttons.append(
                f'<button class="filter-btn {active_class}" data-filter="{cat}">{cat}</button>'
            )
        filters_html = "\n                ".join(filter_buttons)

        # Product cards
        cards_html = []
        for item in blueprint.showcase_items:
            price_text = item.get("metrics", "$229").split("•")[0].strip()
            tags_html = "".join([f'<span class="pill-badge">{t}</span>' for t in item.get("tags", [])])
            cards_html.append(f"""
            <article class="glass-card product-card tilt-card" data-category="{item['category']}" data-id="{item['id']}" data-price="{price_text}" data-title="{item['title']}">
                <div class="card-header-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="category-pill" style="font-size: 0.75rem; font-weight: 600; color: var(--primary); text-transform: uppercase;">{item['category']}</span>
                    <span class="price-tag" style="font-size: 1.1rem; font-weight: 800; color: var(--text-primary);">{price_text}</span>
                </div>
                <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem;">{item['title']}</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.5;">{item['description']}</p>
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem;">{tags_html}</div>
                <div style="display: flex; gap: 0.75rem;">
                    <button class="btn-modern btn-primary add-to-cart-btn" style="flex: 1;"
                            data-id="{item['id']}"
                            data-title="{item['title']}"
                            data-price="{price_text}">
                        <i data-lucide="shopping-bag" style="width: 16px; height: 16px;"></i>
                        <span>Add to Bag</span>
                    </button>
                    <button class="btn-modern btn-glass btn-modal-trigger"
                            data-title="{item['title']}"
                            data-desc="{item.get('modal_details', item['description'])}"
                            data-metrics="{item.get('metrics', '')}"
                            data-category="{item['category']}"
                            title="View Specifications">
                        <i data-lucide="info" style="width: 16px; height: 16px;"></i>
                    </button>
                </div>
            </article>""")
        products_grid_html = "\n".join(cards_html)

        # Bento Trust Features
        bento_cards = []
        for feat in blueprint.features_bento:
            bento_cards.append(f"""
            <div class="glass-card bento-card tilt-card" style="padding: 1.75rem; border-radius: 1rem;">
                <div style="width: 44px; height: 44px; border-radius: 10px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
                    <i data-lucide="{feat.get('icon', 'shield-check')}" style="width: 22px; height: 22px; color: var(--primary);"></i>
                </div>
                <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--primary); margin-bottom: 0.5rem;">{feat.get('highlight', 'Guaranteed')}</div>
                <h4 style="font-size: 1.15rem; margin-bottom: 0.5rem;">{feat['title']}</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">{feat['subtitle']}</p>
            </div>""")
        bento_grid_html = "\n".join(bento_cards)

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blueprint.app_title}</title>
    <meta name="description" content="{blueprint.meta_description}">

    {GOOGLE_FONTS_LINK}
    {THREE_JS_CDN}
    {LUCIDE_ICONS_CDN}
    <link rel="stylesheet" href="style.css">

    <style>
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
    </style>
</head>
<body>
    <!-- Ambient Glow Layer -->
    <div class="ambient-glow-layer">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
    </div>

    <!-- Navigation Bar -->
    <header class="glass-panel" style="position: sticky; top: 1rem; margin: 1rem auto; max-width: 1200px; width: calc(100% - 2rem); z-index: 50; padding: 0.75rem 1.5rem; border-radius: 9999px;">
        <nav style="display: flex; justify-content: space-between; align-items: center;">
            <a href="#" style="font-family: var(--font-heading); font-size: 1.35rem; font-weight: 800; color: var(--text-primary); text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="package" style="color: var(--primary);"></i>
                <span class="gradient-text">{brand_name}</span>
            </a>

            <div style="display: flex; align-items: center; gap: 1.75rem;">
                <div style="display: flex; gap: 1.5rem;" class="nav-links">
                    <a href="#catalog" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Catalog</a>
                    <a href="#guarantees" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Guarantees</a>
                    <a href="#about" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Technology</a>
                </div>

                <!-- Shopping Bag Button -->
                <button id="cart-btn" class="btn-modern btn-primary" style="padding: 0.45rem 1rem; border-radius: 9999px; display: flex; align-items: center; gap: 0.4rem;" aria-label="View Shopping Bag">
                    <i data-lucide="shopping-bag" style="width: 18px; height: 18px;"></i>
                    <span>Bag</span>
                    <span id="cart-badge" class="cart-badge">0</span>
                </button>

                <!-- Theme Toggle -->
                <button id="theme-toggle" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px;" aria-label="Toggle Theme">
                    <i data-lucide="sun" id="theme-icon-sun" style="display: none; width: 18px; height: 18px;"></i>
                    <i data-lucide="moon" id="theme-icon-moon" style="display: inline; width: 18px; height: 18px;"></i>
                </button>
            </div>
        </nav>
    </header>

    <main>
        <!-- 3D Interactive Product Hero Section -->
        <section class="canvas-container" style="min-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 4rem 1.5rem; text-align: center; position: relative;">
            <canvas id="webstudio-3d-canvas" class="hero-canvas"></canvas>

            <div class="hero-content" style="max-width: 800px; margin: 0 auto; position: relative; z-index: 10;">
                <div style="margin-bottom: 1.5rem;">
                    <span class="pill-badge">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); display: inline-block; box-shadow: 0 0 10px var(--success);"></span>
                        3D Interactive Hardware Showcase • Drag to Spin
                    </span>
                </div>

                <h1 style="font-size: clamp(2.5rem, 5.5vw, 4.2rem); margin-bottom: 1.5rem; letter-spacing: -0.03em;">
                    {blueprint.headline}
                </h1>

                <p style="font-size: clamp(1.1rem, 2vw, 1.3rem); color: var(--text-secondary); margin-bottom: 2.5rem; max-width: 650px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    {blueprint.subheadline}
                </p>

                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                    <a href="#catalog" class="btn-modern btn-primary">
                        <span>{blueprint.primary_cta}</span>
                        <i data-lucide="arrow-down" style="width: 18px; height: 18px;"></i>
                    </a>
                    <button id="hero-quick-order-btn" class="btn-modern btn-glass">
                        <span>Quick Order Flagship</span>
                        <i data-lucide="zap" style="width: 18px; height: 18px;"></i>
                    </button>
                </div>
            </div>
        </section>

        <!-- Product Catalog Section -->
        <section id="catalog" style="max-width: 1200px; margin: 2rem auto 5rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 3rem;">
                <h2 style="font-size: 2.2rem; margin-bottom: 0.75rem;">Curated Hardware Fleet</h2>
                <p style="color: var(--text-secondary); max-width: 550px; margin: 0 auto;">Precision engineered tactile gear and spatial compute accessories designed for uncompromising creators.</p>
            </div>

            <!-- Category Filter Tabs -->
            <div class="filter-container">
                {filters_html}
            </div>

            <!-- Product Grid -->
            <div id="product-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.75rem;">
                {products_grid_html}
            </div>
        </section>

        <!-- Trust & Guarantees Bento Section -->
        <section id="guarantees" style="max-width: 1200px; margin: 0 auto 6rem auto; padding: 0 1.5rem;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                {bento_grid_html}
            </div>
        </section>
    </main>

    <!-- Slide-Out Shopping Cart Drawer -->
    <div id="cart-backdrop" class="cart-drawer-backdrop"></div>
    <aside id="cart-drawer" class="cart-drawer" aria-label="Shopping Bag Drawer">
        <div class="cart-drawer-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="shopping-bag" style="color: var(--primary); width: 20px; height: 20px;"></i>
                <h3 style="font-size: 1.2rem; font-weight: 700;">Your Shopping Bag</h3>
            </div>
            <button id="cart-close-btn" class="btn-modern btn-glass" style="padding: 0.35rem 0.65rem; border-radius: 50%;" aria-label="Close Bag">
                <i data-lucide="x" style="width: 18px; height: 18px;"></i>
            </button>
        </div>

        <div id="cart-items-container" class="cart-drawer-body">
            <div id="cart-empty-msg" style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
                <i data-lucide="package-open" style="width: 48px; height: 48px; margin: 0 auto 1rem auto; opacity: 0.4;"></i>
                <p>Your bag is currently empty.</p>
                <p style="font-size: 0.85rem; margin-top: 0.5rem;">Add precision gear from the catalog above.</p>
            </div>
        </div>

        <div class="cart-drawer-footer">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; color: var(--text-secondary); font-size: 0.9rem;">
                <span>Subtotal:</span>
                <span id="cart-subtotal">$0.00</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                <span>Worldwide Express Shipping:</span>
                <span style="color: var(--success); font-weight: 600;">FREE</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 800;">
                <span>Total:</span>
                <span id="cart-total" class="gradient-text">$0.00</span>
            </div>
            <button id="checkout-btn" class="btn-modern btn-primary" style="width: 100%; padding: 0.85rem;" disabled>
                <span>Proceed to Checkout</span>
                <i data-lucide="credit-card" style="width: 18px; height: 18px;"></i>
            </button>
        </div>
    </aside>

    <!-- Checkout Modal Dialog -->
    <div id="checkout-modal" class="modal-backdrop" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 1100; display: none; align-items: center; justify-content: center; padding: 1.5rem;">
        <div class="modal-dialog glass-panel" style="background: var(--bg-surface); border: 1px solid var(--border-highlight); border-radius: 1.25rem; width: 100%; max-width: 520px; padding: 2rem; position: relative;">
            <button id="checkout-close-btn" style="position: absolute; top: 1.25rem; right: 1.25rem; background: transparent; border: none; color: var(--text-muted); cursor: pointer;">
                <i data-lucide="x" style="width: 20px; height: 20px;"></i>
            </button>

            <div id="checkout-form-view">
                <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem;">Fast-Track Checkout</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">Simulated 1-click autonomous order dispatch.</p>

                <form id="checkout-form" style="display: flex; flex-direction: column; gap: 1rem;">
                    <div>
                        <label style="display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;">Full Name</label>
                        <input type="text" id="cust-name" required placeholder="Elena Rostova" style="width: 100%; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;">Email Address</label>
                        <input type="email" id="cust-email" required placeholder="elena@autonomous.dev" style="width: 100%; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;">Delivery Destination</label>
                        <input type="text" id="cust-address" required placeholder="Orbital Station 4, Level 9" style="width: 100%; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                    </div>
                    <button type="submit" class="btn-modern btn-primary" style="margin-top: 0.75rem; padding: 0.85rem;">
                        <span>Confirm & Dispatch Order</span>
                        <i data-lucide="check-circle" style="width: 18px; height: 18px;"></i>
                    </button>
                </form>
            </div>

            <div id="checkout-success-view" style="display: none; text-align: center; padding: 1.5rem 0;">
                <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(16, 185, 129, 0.15); border: 1px solid var(--success); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem auto;">
                    <i data-lucide="check" style="width: 28px; height: 28px; color: var(--success);"></i>
                </div>
                <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem;">Order Successfully Dispatched!</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">Order tracking code: <strong id="order-id-display" class="gradient-text">ORD-94821</strong></p>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">Your hardware has been allocated and is routing via autonomous freight.</p>
                <button id="order-done-btn" class="btn-modern btn-glass" style="width: 100%;">
                    <span>Return to Store</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Product Details Modal Dialog -->
    <div id="details-modal" class="modal-backdrop" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 1100; display: none; align-items: center; justify-content: center; padding: 1.5rem;">
        <div class="modal-dialog glass-panel" style="background: var(--bg-surface); border: 1px solid var(--border-highlight); border-radius: 1.25rem; width: 100%; max-width: 550px; padding: 2rem; position: relative;">
            <button id="details-close-btn" style="position: absolute; top: 1.25rem; right: 1.25rem; background: transparent; border: none; color: var(--text-muted); cursor: pointer;">
                <i data-lucide="x" style="width: 20px; height: 20px;"></i>
            </button>
            <span id="modal-category" style="font-size: 0.75rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">CATEGORY</span>
            <h3 id="modal-title" style="font-size: 1.4rem; margin: 0.5rem 0 1rem 0;">Product Title</h3>
            <p id="modal-desc" style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">Description</p>
            <div id="modal-metrics" style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); padding: 0.75rem 1rem; border-radius: 0.5rem; font-size: 0.85rem; margin-bottom: 1.5rem;"></div>
            <button id="modal-add-bag-btn" class="btn-modern btn-primary" style="width: 100%;">
                <i data-lucide="shopping-bag" style="width: 16px; height: 16px;"></i>
                <span>Add Item to Bag</span>
            </button>
        </div>
    </div>

    <!-- Footer -->
    <footer style="max-width: 1200px; margin: 4rem auto 2rem auto; padding: 2rem 1.5rem; border-top: 1px solid var(--border-subtle); text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        <p>© 2026 {brand_name}. Synthesized autonomously with Project FORGE WebStudio.</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
"""

    @classmethod
    def _generate_ecommerce_js(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        three_d_code = generate_three_d_scene_script(
            canvas_id="webstudio-3d-canvas",
            scene_mode="ecommerce",
            primary_hex=primary_hex,
            accent_hex=secondary_hex,
            domain_type="ecommerce",
        )
        tilt_code = generate_3d_tilt_script()

        return f"""// ==========================================================================
// ForgeWebStudio 3.0 — E-Commerce Application Runtime
// ==========================================================================

{three_d_code}

{tilt_code}

document.addEventListener('DOMContentLoaded', () => {{
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // --------------------------------------------------------------------------
    // Theme Management
    // --------------------------------------------------------------------------
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    function applyTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        if (sunIcon && moonIcon) {{
            sunIcon.style.display = theme === 'light' ? 'inline' : 'none';
            moonIcon.style.display = theme === 'dark' ? 'inline' : 'none';
        }}
    }}
    const savedTheme = localStorage.getItem('forge_theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('forge_theme', next);
        }});
    }}

    // --------------------------------------------------------------------------
    // Shopping Cart State & Drawer Controls
    // --------------------------------------------------------------------------
    let cart = [];

    const cartBtn = document.getElementById('cart-btn');
    const cartDrawer = document.getElementById('cart-drawer');
    const cartBackdrop = document.getElementById('cart-backdrop');
    const cartCloseBtn = document.getElementById('cart-close-btn');
    const cartBadge = document.getElementById('cart-badge');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartEmptyMsg = document.getElementById('cart-empty-msg');
    const cartSubtotal = document.getElementById('cart-subtotal');
    const cartTotal = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');

    function openCart() {{
        if (cartDrawer) cartDrawer.classList.add('open');
        if (cartBackdrop) cartBackdrop.classList.add('open');
    }}

    function closeCart() {{
        if (cartDrawer) cartDrawer.classList.remove('open');
        if (cartBackdrop) cartBackdrop.classList.remove('open');
    }}

    if (cartBtn) cartBtn.addEventListener('click', openCart);
    if (cartCloseBtn) cartCloseBtn.addEventListener('click', closeCart);
    if (cartBackdrop) cartBackdrop.addEventListener('click', closeCart);

    function updateCartUI() {{
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        if (cartBadge) cartBadge.textContent = totalItems;

        const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const formattedTotal = `$${{subtotal.toFixed(2)}}`;
        if (cartSubtotal) cartSubtotal.textContent = formattedTotal;
        if (cartTotal) cartTotal.textContent = formattedTotal;

        if (checkoutBtn) {{
            checkoutBtn.disabled = cart.length === 0;
        }}

        if (!cartItemsContainer) return;

        if (cart.length === 0) {{
            cartItemsContainer.innerHTML = `
                <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
                    <i data-lucide="package-open" style="width: 48px; height: 48px; margin: 0 auto 1rem auto; opacity: 0.4;"></i>
                    <p>Your bag is currently empty.</p>
                    <p style="font-size: 0.85rem; margin-top: 0.5rem;">Add precision gear from the catalog above.</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }}

        cartItemsContainer.innerHTML = '';
        cart.forEach(item => {{
            const row = document.createElement('div');
            row.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 0; border-bottom: 1px solid var(--border-subtle);";
            row.innerHTML = `
                <div style="flex: 1; padding-right: 0.75rem;">
                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">${{item.title}}</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">$${{item.price.toFixed(2)}} each</div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <button class="cart-qty-btn dec-qty" data-id="${{item.id}}" style="padding: 0.2rem 0.5rem; background: var(--glass-bg); border: 1px solid var(--border-subtle); color: var(--text-primary); border-radius: 4px; cursor: pointer;">-</button>
                    <span style="font-weight: 700; font-size: 0.9rem; min-width: 18px; text-align: center;">${{item.quantity}}</span>
                    <button class="cart-qty-btn inc-qty" data-id="${{item.id}}" style="padding: 0.2rem 0.5rem; background: var(--glass-bg); border: 1px solid var(--border-subtle); color: var(--text-primary); border-radius: 4px; cursor: pointer;">+</button>
                    <button class="cart-remove-btn" data-id="${{item.id}}" style="margin-left: 0.35rem; background: transparent; border: none; color: var(--danger); cursor: pointer;" title="Remove">
                        <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
                    </button>
                </div>
            `;
            cartItemsContainer.appendChild(row);
        }});

        // Bind quantity controls
        cartItemsContainer.querySelectorAll('.inc-qty').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const id = btn.getAttribute('data-id');
                const target = cart.find(i => i.id === id);
                if (target) {{
                    target.quantity += 1;
                    updateCartUI();
                }}
            }});
        }});

        cartItemsContainer.querySelectorAll('.dec-qty').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const id = btn.getAttribute('data-id');
                const target = cart.find(i => i.id === id);
                if (target) {{
                    target.quantity -= 1;
                    if (target.quantity <= 0) {{
                        cart = cart.filter(i => i.id !== id);
                    }}
                    updateCartUI();
                }}
            }});
        }});

        cartItemsContainer.querySelectorAll('.cart-remove-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const id = btn.getAttribute('data-id');
                cart = cart.filter(i => i.id !== id);
                updateCartUI();
            }});
        }});

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }}

    function addToCart(id, title, priceStr) {{
        const cleanPrice = parseFloat(priceStr.replace(/[^0-9.]/g, '')) || 229;
        const existing = cart.find(i => i.id === id);
        if (existing) {{
            existing.quantity += 1;
        }} else {{
            cart.push({{ id, title, price: cleanPrice, quantity: 1 }});
        }}
        updateCartUI();
        openCart();
    }}

    // Bind Add to Bag buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const id = btn.getAttribute('data-id');
            const title = btn.getAttribute('data-title');
            const price = btn.getAttribute('data-price');
            addToCart(id, title, price);
        }});
    }});

    const heroQuickOrder = document.getElementById('hero-quick-order-btn');
    if (heroQuickOrder) {{
        heroQuickOrder.addEventListener('click', () => {{
            addToCart('flagship-1', 'Quantum V2 Flagship Keyboard', '$229.00');
        }});
    }}

    // --------------------------------------------------------------------------
    // Category Filtering
    // --------------------------------------------------------------------------
    const filterBtns = document.querySelectorAll('.filter-btn');
    const productCards = document.querySelectorAll('.product-card');

    filterBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');
            productCards.forEach(card => {{
                const cat = card.getAttribute('data-category');
                if (filter === 'All Gear' || filter === cat || cat.includes(filter)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    }});

    // --------------------------------------------------------------------------
    // Checkout Modal & Simulated Fulfillment
    // --------------------------------------------------------------------------
    const checkoutModal = document.getElementById('checkout-modal');
    const checkoutCloseBtn = document.getElementById('checkout-close-btn');
    const checkoutForm = document.getElementById('checkout-form');
    const checkoutFormView = document.getElementById('checkout-form-view');
    const checkoutSuccessView = document.getElementById('checkout-success-view');
    const orderDoneBtn = document.getElementById('order-done-btn');

    if (checkoutBtn) {{
        checkoutBtn.addEventListener('click', () => {{
            closeCart();
            if (checkoutModal) {{
                checkoutModal.style.display = 'flex';
                if (checkoutFormView) checkoutFormView.style.display = 'block';
                if (checkoutSuccessView) checkoutSuccessView.style.display = 'none';
            }}
        }});
    }}

    if (checkoutCloseBtn) {{
        checkoutCloseBtn.addEventListener('click', () => {{
            if (checkoutModal) checkoutModal.style.display = 'none';
        }});
    }}

    if (checkoutForm) {{
        checkoutForm.addEventListener('submit', (e) => {{
            e.preventDefault();
            const orderId = 'ORD-' + Math.floor(10000 + Math.random() * 90000);
            const orderDisp = document.getElementById('order-id-display');
            if (orderDisp) orderDisp.textContent = orderId;

            if (checkoutFormView) checkoutFormView.style.display = 'none';
            if (checkoutSuccessView) checkoutSuccessView.style.display = 'block';

            cart = [];
            updateCartUI();
        }});
    }}

    if (orderDoneBtn) {{
        orderDoneBtn.addEventListener('click', () => {{
            if (checkoutModal) checkoutModal.style.display = 'none';
        }});
    }}

    // --------------------------------------------------------------------------
    // Product Details Modal
    // --------------------------------------------------------------------------
    const detailsModal = document.getElementById('details-modal');
    const detailsCloseBtn = document.getElementById('details-close-btn');
    let currentModalProduct = null;

    document.querySelectorAll('.btn-modal-trigger').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const title = btn.getAttribute('data-title');
            const desc = btn.getAttribute('data-desc');
            const cat = btn.getAttribute('data-category');
            const metrics = btn.getAttribute('data-metrics');

            currentModalProduct = {{ title, price: metrics.split('•')[0].trim() }};

            const tEl = document.getElementById('modal-title');
            const dEl = document.getElementById('modal-desc');
            const cEl = document.getElementById('modal-category');
            const mEl = document.getElementById('modal-metrics');

            if (tEl) tEl.textContent = title;
            if (dEl) dEl.textContent = desc;
            if (cEl) cEl.textContent = cat;
            if (mEl) mEl.textContent = metrics ? `Specifications: ${{metrics}}` : '';

            if (detailsModal) detailsModal.style.display = 'flex';
        }});
    }});

    if (detailsCloseBtn) {{
        detailsCloseBtn.addEventListener('click', () => {{
            if (detailsModal) detailsModal.style.display = 'none';
        }});
    }}

    const modalAddBagBtn = document.getElementById('modal-add-bag-btn');
    if (modalAddBagBtn) {{
        modalAddBagBtn.addEventListener('click', () => {{
            if (currentModalProduct) {{
                addToCart('modal-' + Date.now(), currentModalProduct.title, currentModalProduct.price);
            }}
            if (detailsModal) detailsModal.style.display = 'none';
        }});
    }}
}});
"""

    # =========================================================================
    # 2. SAAS PLATFORM ARCHITECTURE (Pricing Toggle, ROI Slider, 3D Neural Core)
    # =========================================================================

    @classmethod
    def _generate_saas_html(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        brand_name = blueprint.app_title.split("—")[0].strip()

        # Features bento
        bento_cards = []
        for feat in blueprint.features_bento:
            bento_cards.append(f"""
            <div class="glass-card bento-card tilt-card" style="padding: 2rem; border-radius: 1.25rem;">
                <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); display: flex; align-items: center; justify-content: center; margin-bottom: 1.25rem;">
                    <i data-lucide="{feat.get('icon', 'sparkles')}" style="width: 24px; height: 24px; color: var(--primary);"></i>
                </div>
                <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--primary); margin-bottom: 0.5rem;">{feat.get('highlight', 'Platform')}</div>
                <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem;">{feat['title']}</h4>
                <p style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6;">{feat['subtitle']}</p>
            </div>""")
        bento_grid_html = "\n".join(bento_cards)

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blueprint.app_title}</title>
    <meta name="description" content="{blueprint.meta_description}">

    {GOOGLE_FONTS_LINK}
    {THREE_JS_CDN}
    {LUCIDE_ICONS_CDN}
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="ambient-glow-layer">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
    </div>

    <!-- Navigation Bar -->
    <header class="glass-panel" style="position: sticky; top: 1rem; margin: 1rem auto; max-width: 1200px; width: calc(100% - 2rem); z-index: 50; padding: 0.75rem 1.5rem; border-radius: 9999px;">
        <nav style="display: flex; justify-content: space-between; align-items: center;">
            <a href="#" style="font-family: var(--font-heading); font-size: 1.35rem; font-weight: 800; color: var(--text-primary); text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="cpu" style="color: var(--primary);"></i>
                <span class="gradient-text">{brand_name}</span>
            </a>

            <div style="display: flex; align-items: center; gap: 2rem;">
                <div style="display: flex; gap: 1.75rem;" class="nav-links">
                    <a href="#roi-calculator" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">ROI Calculator</a>
                    <a href="#capabilities" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Platform</a>
                    <a href="#pricing" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Pricing</a>
                    <a href="#faq" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">FAQ</a>
                </div>

                <button id="trial-nav-btn" class="btn-modern btn-primary" style="padding: 0.45rem 1.1rem; border-radius: 9999px;">
                    <span>Start Free Trial</span>
                </button>

                <button id="theme-toggle" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px;" aria-label="Toggle Theme">
                    <i data-lucide="sun" id="theme-icon-sun" style="display: none; width: 18px; height: 18px;"></i>
                    <i data-lucide="moon" id="theme-icon-moon" style="display: inline; width: 18px; height: 18px;"></i>
                </button>
            </div>
        </nav>
    </header>

    <main>
        <!-- 3D AI Neural Core Hero Section -->
        <section class="canvas-container" style="min-height: 85vh; display: flex; align-items: center; justify-content: center; padding: 4rem 1.5rem; text-align: center; position: relative;">
            <canvas id="webstudio-3d-canvas" class="hero-canvas"></canvas>

            <div class="hero-content" style="max-width: 850px; margin: 0 auto; position: relative; z-index: 10;">
                <div style="margin-bottom: 1.5rem;">
                    <span class="pill-badge">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); display: inline-block; box-shadow: 0 0 10px var(--success);"></span>
                        Autonomous Software Intelligence 3.0
                    </span>
                </div>

                <h1 style="font-size: clamp(2.5rem, 6vw, 4.5rem); margin-bottom: 1.5rem; letter-spacing: -0.03em;">
                    {blueprint.headline}
                </h1>

                <p style="font-size: clamp(1.1rem, 2vw, 1.35rem); color: var(--text-secondary); margin-bottom: 2.5rem; max-width: 680px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    {blueprint.subheadline}
                </p>

                <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                    <button id="hero-trial-btn" class="btn-modern btn-primary">
                        <span>{blueprint.primary_cta}</span>
                        <i data-lucide="sparkles" style="width: 18px; height: 18px;"></i>
                    </button>
                    <button id="hero-demo-btn" class="btn-modern btn-glass">
                        <span>Watch Interactive Demo</span>
                        <i data-lucide="play-circle" style="width: 18px; height: 18px;"></i>
                    </button>
                </div>
            </div>
        </section>

        <!-- Social Proof Metric Band -->
        <section style="max-width: 1200px; margin: -2rem auto 4rem auto; padding: 0 1.5rem; position: relative; z-index: 10;">
            <div class="glass-card telemetry-strip" style="border-color: var(--border-highlight);">
                <div class="telemetry-item">
                    <div class="stat-number gradient-text">10x</div>
                    <span class="stat-label">Faster Engineering Delivery</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text">99.4%</div>
                    <span class="stat-label">Automated Fix Rate</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text">180k+</div>
                    <span class="stat-label">Verified Deployments</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text">0</div>
                    <span class="stat-label">Security Vulnerabilities Leaked</span>
                </div>
            </div>
        </section>

        <!-- Interactive ROI Savings Calculator Section -->
        <section id="roi-calculator" style="max-width: 1000px; margin: 4rem auto 6rem auto; padding: 0 1.5rem;">
            <div class="glass-card" style="padding: 3rem 2.5rem; border-radius: 1.5rem; border-color: var(--border-glow);">
                <div style="text-align: center; margin-bottom: 2.5rem;">
                    <span class="pill-badge" style="margin-bottom: 0.75rem;">Interactive ROI Model</span>
                    <h2 style="font-size: 2.2rem; margin-bottom: 0.5rem;">Calculate Your Team's Velocity & Cost Savings</h2>
                    <p style="color: var(--text-secondary);">See how autonomous multi-agent synthesis transforms your engineering economics.</p>
                </div>

                <div style="margin-bottom: 2.5rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem; font-weight: 600;">
                        <span>Engineering Team Size:</span>
                        <span class="gradient-text" style="font-size: 1.25rem;"><span id="team-size-val">25</span> Developers</span>
                    </div>
                    <input type="range" id="team-size-slider" min="5" max="300" step="5" value="25" style="width: 100%; height: 8px; border-radius: 4px; background: var(--bg-surface-elevated); outline: none; cursor: pointer;">
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem;">
                    <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem; text-align: center;">
                        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">Hours Saved Annually</div>
                        <div id="calc-hours" class="gradient-text" style="font-size: 2rem; font-weight: 800;">12,000</div>
                        <div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">480 hrs / engineer / year</div>
                    </div>
                    <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem; text-align: center;">
                        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">Estimated Cost Savings</div>
                        <div id="calc-savings" class="gradient-text" style="font-size: 2rem; font-weight: 800;">$962,500</div>
                        <div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">Based on $80/hr blend rate</div>
                    </div>
                    <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem; text-align: center;">
                        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">Velocity Multiplier</div>
                        <div id="calc-velocity" class="gradient-text" style="font-size: 2rem; font-weight: 800;">4.8x</div>
                        <div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">Cycle time reduction</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Capabilities Bento Section -->
        <section id="capabilities" style="max-width: 1200px; margin: 0 auto 6rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 3rem;">
                <h2 style="font-size: 2.2rem; margin-bottom: 0.75rem;">Autonomous Multi-Agent Architecture</h2>
                <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto;">Self-orchestrating specialist roles coordinated across Kahn's topological DAG wave execution.</p>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem;">
                {bento_grid_html}
            </div>
        </section>

        <!-- Interactive Pricing Section -->
        <section id="pricing" style="max-width: 1200px; margin: 0 auto 6rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 2.5rem;">
                <h2 style="font-size: 2.2rem; margin-bottom: 0.75rem;">Predictable, Transparent Pricing</h2>
                <p style="color: var(--text-secondary); max-width: 500px; margin: 0 auto 2rem auto;">Scale your autonomous engineering capacity with zero hidden fees.</p>

                <!-- Billing Cycle Toggle -->
                <div class="pricing-toggle-bar">
                    <span style="font-size: 0.95rem; font-weight: 600;">Monthly</span>
                    <div id="billing-toggle" class="toggle-switch-track" aria-label="Toggle Annual Billing">
                        <div class="toggle-switch-thumb"></div>
                    </div>
                    <span style="font-size: 0.95rem; font-weight: 600;">
                        Annual <span class="pill-badge" style="color: var(--success); border-color: rgba(16, 185, 129, 0.3);">Save 20%</span>
                    </span>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.75rem;">
                <!-- Starter -->
                <div class="glass-card pricing-card tilt-card">
                    <div>
                        <h3 style="font-size: 1.3rem; margin-bottom: 0.5rem;">Starter Tier</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">For solo engineers and high-velocity prototyping.</p>
                        <div style="font-size: 3rem; font-weight: 800; margin-bottom: 1.5rem;">
                            <span class="tier-price" data-monthly="29" data-annual="23">$29</span>
                            <span style="font-size: 1rem; color: var(--text-muted); font-weight: 400;">/ mo</span>
                        </div>
                        <ul style="list-style: none; padding: 0; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.9rem; color: var(--text-secondary);">
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Up to 50 Autonomous Tasks/mo</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Three.js & Modern Web Synthesis</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Automated Verification Battery</li>
                        </ul>
                    </div>
                    <button class="btn-modern btn-glass plan-cta-btn" style="width: 100%;">Select Starter</button>
                </div>

                <!-- Pro (Featured) -->
                <div class="glass-card pricing-card featured tilt-card">
                    <div style="position: absolute; top: -0.75rem; right: 2rem;">
                        <span class="pill-badge" style="background: var(--primary); color: #fff; border: none; font-weight: 700;">MOST POPULAR</span>
                    </div>
                    <div>
                        <h3 style="font-size: 1.3rem; margin-bottom: 0.5rem;">Engineering Pro</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">For growth teams shipping production software daily.</p>
                        <div style="font-size: 3rem; font-weight: 800; margin-bottom: 1.5rem;">
                            <span class="tier-price" data-monthly="99" data-annual="79">$99</span>
                            <span style="font-size: 1rem; color: var(--text-muted); font-weight: 400;">/ mo</span>
                        </div>
                        <ul style="list-style: none; padding: 0; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.9rem; color: var(--text-secondary);">
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Unlimited Autonomous Synthesis</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Memora Long-Term Cognitive Memory</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Self-Healing Test & Security Gates</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Priority Multi-Agent Wave Queue</li>
                        </ul>
                    </div>
                    <button class="btn-modern btn-primary plan-cta-btn" style="width: 100%;">Start Pro Trial</button>
                </div>

                <!-- Enterprise -->
                <div class="glass-card pricing-card tilt-card">
                    <div>
                        <h3 style="font-size: 1.3rem; margin-bottom: 0.5rem;">Enterprise Scale</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">Dedicated infrastructure, custom SLA, and SOC2.</p>
                        <div style="font-size: 3rem; font-weight: 800; margin-bottom: 1.5rem;">
                            <span class="tier-price" data-monthly="299" data-annual="239">$299</span>
                            <span style="font-size: 1rem; color: var(--text-muted); font-weight: 400;">/ mo</span>
                        </div>
                        <ul style="list-style: none; padding: 0; margin-bottom: 2rem; display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.9rem; color: var(--text-secondary);">
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Dedicated Air-Gapped Runner Fleet</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> Custom Fine-Tuned Agent Roles</li>
                            <li style="display: flex; align-items: center; gap: 0.5rem;"><i data-lucide="check" style="color: var(--success); width: 16px; height: 16px;"></i> 99.99% Uptime Guarantee & SLA</li>
                        </ul>
                    </div>
                    <button class="btn-modern btn-glass plan-cta-btn" style="width: 100%;">Contact Enterprise</button>
                </div>
            </div>
        </section>

        <!-- FAQ Section -->
        <section id="faq" style="max-width: 850px; margin: 0 auto 6rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 2.5rem;">
                <h2 style="font-size: 2rem; margin-bottom: 0.5rem;">Frequently Asked Questions</h2>
            </div>
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div class="glass-card" style="padding: 1.25rem 1.5rem; border-radius: 0.75rem; cursor: pointer;">
                    <h4 style="font-size: 1.05rem; margin-bottom: 0.5rem;">How does Forge differ from simple coding assistants?</h4>
                    <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">Unlike one-shot code completers, Forge operates as an autonomous multi-agent engineering team: planning architecture, breaking dependencies into topological waves, implementing verified code, and self-healing regressions.</p>
                </div>
                <div class="glass-card" style="padding: 1.25rem 1.5rem; border-radius: 0.75rem; cursor: pointer;">
                    <h4 style="font-size: 1.05rem; margin-bottom: 0.5rem;">Can I export the synthesized websites directly to GitHub?</h4>
                    <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">Yes. All synthesized projects are self-contained with zero external bundler lock-in. You can push directly to GitHub or deploy to Vercel, Netlify, or AWS with a single command.</p>
                </div>
                <div class="glass-card" style="padding: 1.25rem 1.5rem; border-radius: 0.75rem; cursor: pointer;">
                    <h4 style="font-size: 1.05rem; margin-bottom: 0.5rem;">How does Memora long-term cognitive memory work?</h4>
                    <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">Memora stores your engineering preferences, design rules, and past architectural patterns across builds, ensuring Forge becomes faster, smarter, and more tailored to your stack with every synthesis.</p>
                </div>
            </div>
        </section>
    </main>

    <!-- Interactive Live Demo Modal -->
    <div id="demo-modal" class="modal-backdrop" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 1100; display: none; align-items: center; justify-content: center; padding: 1.5rem;">
        <div class="modal-dialog glass-panel" style="background: var(--bg-surface); border: 1px solid var(--border-highlight); border-radius: 1.25rem; width: 100%; max-width: 600px; padding: 2rem; position: relative;">
            <button id="demo-close-btn" style="position: absolute; top: 1.25rem; right: 1.25rem; background: transparent; border: none; color: var(--text-muted); cursor: pointer;">
                <i data-lucide="x" style="width: 20px; height: 20px;"></i>
            </button>
            <h3 style="font-size: 1.4rem; margin-bottom: 0.5rem;">Interactive Synthesis Simulator</h3>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.25rem;">Watch multi-agent autonomous execution in action.</p>

            <div style="display: flex; gap: 0.5rem; margin-bottom: 1.25rem;">
                <input type="text" id="sim-prompt-input" value="Build a high-performance 3D analytics dashboard" style="flex: 1; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                <button id="sim-run-btn" class="btn-modern btn-primary">
                    <i data-lucide="play" style="width: 16px; height: 16px;"></i>
                    <span>Simulate</span>
                </button>
            </div>

            <div id="sim-terminal" style="background: rgba(5, 10, 20, 0.95); border: 1px solid var(--border-subtle); border-radius: 0.75rem; padding: 1rem; font-family: monospace; font-size: 0.85rem; min-height: 180px; max-height: 240px; overflow-y: auto; color: #a5f3fc; line-height: 1.6;">
                <div style="color: var(--text-muted);">&gt; Click 'Simulate' to start autonomous software synthesis...</div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer style="max-width: 1200px; margin: 4rem auto 2rem auto; padding: 2rem 1.5rem; border-top: 1px solid var(--border-subtle); text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        <p>© 2026 {brand_name}. Synthesized autonomously with Project FORGE WebStudio.</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
"""

    @classmethod
    def _generate_saas_js(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        three_d_code = generate_three_d_scene_script(
            canvas_id="webstudio-3d-canvas",
            scene_mode="saas",
            primary_hex=primary_hex,
            accent_hex=secondary_hex,
            domain_type="saas",
        )
        tilt_code = generate_3d_tilt_script()

        return f"""// ==========================================================================
// ForgeWebStudio 3.0 — SaaS Platform Application Runtime
// ==========================================================================

{three_d_code}

{tilt_code}

document.addEventListener('DOMContentLoaded', () => {{
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Theme Management
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    function applyTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        if (sunIcon && moonIcon) {{
            sunIcon.style.display = theme === 'light' ? 'inline' : 'none';
            moonIcon.style.display = theme === 'dark' ? 'inline' : 'none';
        }}
    }}
    const savedTheme = localStorage.getItem('forge_theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('forge_theme', next);
        }});
    }}

    // ROI Calculator Slider Logic
    const teamSlider = document.getElementById('team-size-slider');
    const teamSizeVal = document.getElementById('team-size-val');
    const calcHours = document.getElementById('calc-hours');
    const calcSavings = document.getElementById('calc-savings');
    const calcVelocity = document.getElementById('calc-velocity');

    if (teamSlider) {{
        teamSlider.addEventListener('input', () => {{
            const size = parseInt(teamSlider.value, 10);
            if (teamSizeVal) teamSizeVal.textContent = size;

            const hours = size * 480;
            const savings = size * 38500;
            const vel = (3.2 + (size / 100)).toFixed(1);

            if (calcHours) calcHours.textContent = hours.toLocaleString();
            if (calcSavings) calcSavings.textContent = '$' + savings.toLocaleString();
            if (calcVelocity) calcVelocity.textContent = vel + 'x';
        }});
    }}

    // Billing Cycle Switch (Monthly vs Annual 20% Off)
    const billingToggle = document.getElementById('billing-toggle');
    if (billingToggle) {{
        billingToggle.addEventListener('click', () => {{
            const isAnnual = billingToggle.classList.toggle('annual');
            document.querySelectorAll('.tier-price').forEach(el => {{
                el.textContent = isAnnual ? '$' + el.getAttribute('data-annual') : '$' + el.getAttribute('data-monthly');
            }});
        }});
    }}

    // Interactive Demo Simulation Modal
    const demoModal = document.getElementById('demo-modal');
    const demoCloseBtn = document.getElementById('demo-close-btn');
    const simRunBtn = document.getElementById('sim-run-btn');
    const simInput = document.getElementById('sim-prompt-input');
    const simTerm = document.getElementById('sim-terminal');

    function openDemoModal() {{
        if (demoModal) demoModal.style.display = 'flex';
    }}

    function closeDemoModal() {{
        if (demoModal) demoModal.style.display = 'none';
    }}

    document.querySelectorAll('#hero-demo-btn, #hero-trial-btn, #trial-nav-btn, .plan-cta-btn').forEach(btn => {{
        btn.addEventListener('click', openDemoModal);
    }});

    if (demoCloseBtn) demoCloseBtn.addEventListener('click', closeDemoModal);

    if (simRunBtn && simTerm) {{
        simRunBtn.addEventListener('click', () => {{
            const prompt = (simInput ? simInput.value : '').trim() || 'Software Synthesis';
            simTerm.innerHTML = '';

            const logs = [
                `[PLANNER] Analyzing goal: "${{prompt}}"`,
                `[PLANNER] Decomposing into 8-stage topological TaskGraph wave...`,
                `[ARCHITECT] Designing schemas, API endpoints, and File Manifest...`,
                `[DEVELOPER] Synthesizing verified HTML, CSS, and Three.js 3D assets...`,
                `[TESTER] Executing automated verification battery (10/10 gates passed)...`,
                `[MEMORA] Checkpointed interaction into persistent cognitive memory fabric.`,
                `[SUCCESS] 🚀 Synthesis completed with 0 errors in 1.4s!`
            ];

            logs.forEach((log, index) => {{
                setTimeout(() => {{
                    const line = document.createElement('div');
                    line.style.color = index === logs.length - 1 ? 'var(--success)' : '#a5f3fc';
                    line.textContent = log;
                    simTerm.appendChild(line);
                    simTerm.scrollTop = simTerm.scrollHeight;
                }}, index * 350);
            }});
        }});
    }}
}});
"""

    # =========================================================================
    # 3. MISSION DASHBOARD ARCHITECTURE (4 KPI Gauges, Live Telemetry Table)
    # =========================================================================

    @classmethod
    def _generate_dashboard_html(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        brand_name = blueprint.app_title.split("—")[0].strip()

        # Telemetry table initial rows
        initial_services = [
            {"name": "api-gateway", "category": "Network", "status": "nominal", "cpu": "24%", "mem": "38%", "lat": "12ms"},
            {"name": "auth-service", "category": "Compute", "status": "nominal", "cpu": "18%", "mem": "42%", "lat": "16ms"},
            {"name": "vector-db-shard-1", "category": "Storage", "status": "nominal", "cpu": "62%", "mem": "71%", "lat": "22ms"},
            {"name": "inference-worker-01", "category": "Compute", "status": "nominal", "cpu": "84%", "mem": "65%", "lat": "45ms"},
            {"name": "edge-caching-sg", "category": "Network", "status": "nominal", "cpu": "12%", "mem": "29%", "lat": "8ms"},
        ]

        table_rows = []
        for s in initial_services:
            table_rows.append(f"""
            <tr data-service="{s['name']}" data-category="{s['category']}">
                <td style="font-weight: 700; color: var(--text-primary);">{s['name']}</td>
                <td><span class="pill-badge">{s['category']}</span></td>
                <td><span class="status-pill {s['status']}"><span style="width: 6px; height: 6px; border-radius: 50%; background: currentColor;"></span> Nominal</span></td>
                <td class="col-cpu">{s['cpu']}</td>
                <td class="col-mem">{s['mem']}</td>
                <td class="col-lat" style="color: var(--success); font-weight: 600;">{s['lat']}</td>
                <td>
                    <button class="btn-modern btn-glass restart-service-btn" data-service="{s['name']}" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;">Restart</button>
                </td>
            </tr>""")
        table_rows_html = "\n".join(table_rows)

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blueprint.app_title}</title>
    <meta name="description" content="{blueprint.meta_description}">

    {GOOGLE_FONTS_LINK}
    {THREE_JS_CDN}
    {LUCIDE_ICONS_CDN}
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="ambient-glow-layer">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
    </div>

    <!-- Operations Hub Top Navigation Bar -->
    <header class="glass-panel" style="position: sticky; top: 1rem; margin: 1rem auto; max-width: 1200px; width: calc(100% - 2rem); z-index: 50; padding: 0.75rem 1.5rem; border-radius: 9999px;">
        <nav style="display: flex; justify-content: space-between; align-items: center;">
            <a href="#" style="font-family: var(--font-heading); font-size: 1.35rem; font-weight: 800; color: var(--text-primary); text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="activity" style="color: var(--primary);"></i>
                <span class="gradient-text">{brand_name}</span>
            </a>

            <!-- Search Bar -->
            <div style="flex: 1; max-width: 380px; margin: 0 1.5rem;">
                <input type="text" id="telemetry-search-input" placeholder="Search services, clusters, or regions..." style="width: 100%; padding: 0.45rem 0.95rem; border-radius: 9999px; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); font-size: 0.85rem; outline: none;">
            </div>

            <div style="display: flex; align-items: center; gap: 1rem;">
                <span class="status-pill nominal">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--success); box-shadow: 0 0 8px var(--success);"></span>
                    sg-prod-01 (Nominal)
                </span>

                <button id="alert-bell-btn" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px; position: relative;" aria-label="View Alerts">
                    <i data-lucide="bell" style="width: 18px; height: 18px;"></i>
                    <span id="alert-badge" class="cart-badge" style="position: absolute; top: -4px; right: -4px;">2</span>
                </button>

                <button id="theme-toggle" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px;" aria-label="Toggle Theme">
                    <i data-lucide="sun" id="theme-icon-sun" style="display: none; width: 18px; height: 18px;"></i>
                    <i data-lucide="moon" id="theme-icon-moon" style="display: inline; width: 18px; height: 18px;"></i>
                </button>
            </div>
        </nav>
    </header>

    <main>
        <!-- 3D Planetary Telemetry Sphere Hero Section -->
        <section class="canvas-container" style="min-height: 70vh; display: flex; align-items: center; justify-content: center; padding: 3rem 1.5rem; text-align: center; position: relative;">
            <canvas id="webstudio-3d-canvas" class="hero-canvas"></canvas>

            <div class="hero-content" style="max-width: 800px; margin: 0 auto; position: relative; z-index: 10;">
                <div style="margin-bottom: 1rem;">
                    <span class="pill-badge">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); display: inline-block;"></span>
                        Global Orbital Telemetry Mesh
                    </span>
                </div>
                <h1 style="font-size: clamp(2.2rem, 5vw, 3.8rem); margin-bottom: 1rem; letter-spacing: -0.03em;">
                    {blueprint.headline}
                </h1>
                <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto 2rem auto; font-size: 1.1rem; line-height: 1.6;">
                    {blueprint.subheadline}
                </p>
            </div>
        </section>

        <!-- 4 KPI Telemetry Gauges Strip -->
        <section style="max-width: 1200px; margin: -2rem auto 3.5rem auto; padding: 0 1.5rem; position: relative; z-index: 10;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem;">
                <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-muted); font-size: 0.85rem;">Active Pods / Fleet</span>
                        <i data-lucide="server" style="color: var(--primary); width: 18px; height: 18px;"></i>
                    </div>
                    <div id="kpi-pods" style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">96 / 100</div>
                    <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
                        <div id="kpi-pods-bar" style="width: 96%; height: 100%; background: var(--primary);"></div>
                    </div>
                </div>

                <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-muted); font-size: 0.85rem;">Global Throughput</span>
                        <i data-lucide="activity" style="color: var(--success); width: 18px; height: 18px;"></i>
                    </div>
                    <div id="kpi-throughput" class="gradient-text" style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">24,850 req/s</div>
                    <div style="color: var(--success); font-size: 0.8rem; font-weight: 600;">↑ 12.4% vs last hour</div>
                </div>

                <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-muted); font-size: 0.85rem;">P99 Latency</span>
                        <i data-lucide="gauge" style="color: var(--primary); width: 18px; height: 18px;"></i>
                    </div>
                    <div id="kpi-latency" style="font-size: 2rem; font-weight: 800; color: var(--success); margin-bottom: 0.5rem;">18.4 ms</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem;">Target SLA: &lt; 50ms</div>
                </div>

                <div class="glass-card" style="padding: 1.5rem; border-radius: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-muted); font-size: 0.85rem;">Error Incident Rate</span>
                        <i data-lucide="shield-check" style="color: var(--success); width: 18px; height: 18px;"></i>
                    </div>
                    <div id="kpi-errors" style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">0.002%</div>
                    <div style="color: var(--text-secondary); font-size: 0.8rem;">Zero unhandled exceptions</div>
                </div>
            </div>
        </section>

        <!-- Live Telemetry Stream Table Section -->
        <section style="max-width: 1200px; margin: 0 auto 6rem auto; padding: 0 1.5rem;">
            <div class="glass-card" style="padding: 2rem; border-radius: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h2 style="font-size: 1.4rem; margin-bottom: 0.25rem;">Active Service Fleet</h2>
                        <p style="color: var(--text-secondary); font-size: 0.85rem;">Live streaming metrics with real-time auto-healing listeners.</p>
                    </div>
                    <button id="simulate-spike-btn" class="btn-modern btn-glass">
                        <i data-lucide="zap" style="width: 16px; height: 16px;"></i>
                        <span>Simulate Traffic Spike</span>
                    </button>
                </div>

                <div style="overflow-x: auto;">
                    <table id="telemetry-table" class="telemetry-table">
                        <thead>
                            <tr>
                                <th>Service Name</th>
                                <th>Domain</th>
                                <th>Health Status</th>
                                <th>CPU Load</th>
                                <th>Memory</th>
                                <th>P99 Latency</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="telemetry-tbody">
                            {table_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    </main>

    <!-- Slide-Out Alerts Drawer -->
    <div id="alerts-backdrop" class="cart-drawer-backdrop"></div>
    <aside id="alerts-drawer" class="cart-drawer" aria-label="System Activity & Alerts">
        <div class="cart-drawer-header">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="bell" style="color: var(--primary); width: 20px; height: 20px;"></i>
                <h3 style="font-size: 1.2rem; font-weight: 700;">Recent Events & Alerts</h3>
            </div>
            <button id="alerts-close-btn" class="btn-modern btn-glass" style="padding: 0.35rem 0.65rem; border-radius: 50%;">
                <i data-lucide="x" style="width: 18px; height: 18px;"></i>
            </button>
        </div>
        <div class="cart-drawer-body" style="display: flex; flex-direction: column; gap: 1rem;">
            <div class="glass-card" style="padding: 1rem; border-radius: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                    <span>AUTOSCALER</span>
                    <span>1 min ago</span>
                </div>
                <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.25rem;">+4 Compute Pods Provisioned</div>
                <div style="color: var(--text-secondary); font-size: 0.8rem;">Scaled worker pool in sg-prod-01 to handle anticipated batch pipeline.</div>
            </div>
            <div class="glass-card" style="padding: 1rem; border-radius: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                    <span>MEMORY DEFENSE</span>
                    <span>4 mins ago</span>
                </div>
                <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.25rem;">Vector Shard Garbage Collected</div>
                <div style="color: var(--text-secondary); font-size: 0.8rem;">Reclaimed 4.2 GB buffer memory with zero index query degradation.</div>
            </div>
            <div class="glass-card" style="padding: 1rem; border-radius: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.35rem;">
                    <span>MEMORA FABRIC</span>
                    <span>7 mins ago</span>
                </div>
                <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 0.25rem;">Telemetry Snapshot Checkpointed</div>
                <div style="color: var(--text-secondary); font-size: 0.8rem;">Telemetry state committed to memora://forge/telemetry.</div>
            </div>
        </div>
    </aside>

    <!-- Footer -->
    <footer style="max-width: 1200px; margin: 4rem auto 2rem auto; padding: 2rem 1.5rem; border-top: 1px solid var(--border-subtle); text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        <p>© 2026 {brand_name}. Synthesized autonomously with Project FORGE WebStudio.</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
"""

    @classmethod
    def _generate_dashboard_js(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        three_d_code = generate_three_d_scene_script(
            canvas_id="webstudio-3d-canvas",
            scene_mode="dashboard",
            primary_hex=primary_hex,
            accent_hex=secondary_hex,
            domain_type="dashboard",
        )
        tilt_code = generate_3d_tilt_script()

        return f"""// ==========================================================================
// ForgeWebStudio 3.0 — Mission Dashboard Application Runtime
// ==========================================================================

{three_d_code}

{tilt_code}

document.addEventListener('DOMContentLoaded', () => {{
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Theme Management
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    function applyTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        if (sunIcon && moonIcon) {{
            sunIcon.style.display = theme === 'light' ? 'inline' : 'none';
            moonIcon.style.display = theme === 'dark' ? 'inline' : 'none';
        }}
    }}
    const savedTheme = localStorage.getItem('forge_theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('forge_theme', next);
        }});
    }}

    // Real-Time Telemetry Streaming Simulation
    const kpiThroughput = document.getElementById('kpi-throughput');
    const kpiLatency = document.getElementById('kpi-latency');
    const tbody = document.getElementById('telemetry-tbody');

    setInterval(() => {{
        if (kpiThroughput) {{
            const val = 24800 + Math.floor(Math.random() * 250);
            kpiThroughput.textContent = val.toLocaleString() + ' req/s';
        }}
        if (kpiLatency) {{
            const lat = (17.5 + Math.random() * 1.8).toFixed(1);
            kpiLatency.textContent = lat + ' ms';
        }}

        // Jitter table latency values subtly
        if (tbody) {{
            tbody.querySelectorAll('.col-lat').forEach(cell => {{
                const base = parseInt(cell.textContent, 10) || 15;
                const jitter = Math.max(6, base + Math.floor((Math.random() - 0.5) * 4));
                cell.textContent = jitter + 'ms';
            }});
        }}
    }}, 2500);

    // Search Filtering
    const searchInput = document.getElementById('telemetry-search-input');
    if (searchInput && tbody) {{
        searchInput.addEventListener('input', () => {{
            const term = searchInput.value.toLowerCase().trim();
            tbody.querySelectorAll('tr').forEach(row => {{
                const svc = (row.getAttribute('data-service') || '').toLowerCase();
                const cat = (row.getAttribute('data-category') || '').toLowerCase();
                if (!term || svc.includes(term) || cat.includes(term)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }});
    }}

    // Traffic Spike Simulation
    const spikeBtn = document.getElementById('simulate-spike-btn');
    if (spikeBtn) {{
        spikeBtn.addEventListener('click', () => {{
            spikeBtn.disabled = true;
            if (kpiThroughput) kpiThroughput.textContent = '78,420 req/s';
            if (kpiLatency) {{
                kpiLatency.textContent = '84.2 ms';
                kpiLatency.style.color = 'var(--warning)';
            }}

            setTimeout(() => {{
                if (kpiThroughput) kpiThroughput.textContent = '24,850 req/s';
                if (kpiLatency) {{
                    kpiLatency.textContent = '18.4 ms';
                    kpiLatency.style.color = 'var(--success)';
                }}
                spikeBtn.disabled = false;
            }}, 4000);
        }});
    }}

    // Alerts Drawer
    const alertBell = document.getElementById('alert-bell-btn');
    const alertsDrawer = document.getElementById('alerts-drawer');
    const alertsBackdrop = document.getElementById('alerts-backdrop');
    const alertsClose = document.getElementById('alerts-close-btn');

    function openAlerts() {{
        if (alertsDrawer) alertsDrawer.classList.add('open');
        if (alertsBackdrop) alertsBackdrop.classList.add('open');
    }}
    function closeAlerts() {{
        if (alertsDrawer) alertsDrawer.classList.remove('open');
        if (alertsBackdrop) alertsBackdrop.classList.remove('open');
    }}

    if (alertBell) alertBell.addEventListener('click', openAlerts);
    if (alertsClose) alertsClose.addEventListener('click', closeAlerts);
    if (alertsBackdrop) alertsBackdrop.addEventListener('click', closeAlerts);

    // Service restart simulation
    if (tbody) {{
        tbody.querySelectorAll('.restart-service-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const svc = btn.getAttribute('data-service');
                btn.textContent = 'Restarting...';
                btn.disabled = true;
                setTimeout(() => {{
                    btn.textContent = 'Restart';
                    btn.disabled = false;
                }}, 1200);
            }});
        }});
    }}
}});
"""

    # =========================================================================
    # 4. PORTFOLIO / CYBERPUNK ARCHITECTURE (HUD Controls, Terminal, Torus Knot)
    # =========================================================================

    @classmethod
    def _generate_portfolio_html(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        filter_buttons = []
        for i, cat in enumerate(blueprint.categories):
            active_class = "active" if i == 0 else ""
            filter_buttons.append(
                f'<button class="filter-btn {active_class}" data-filter="{cat}">{cat}</button>'
            )
        filters_html = "\n                ".join(filter_buttons)

        cards_html = []
        for item in blueprint.showcase_items:
            tags_html = "".join([f'<span class="pill-badge">{t}</span>' for t in item.get("tags", [])])
            cards_html.append(f"""
            <article class="glass-card showcase-card tilt-card" data-category="{item['category']}" data-id="{item['id']}">
                <div class="card-header-bar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="category-pill" style="font-size: 0.75rem; font-weight: 600; color: var(--primary); text-transform: uppercase;">{item['category']}</span>
                    <span class="metrics-pill" style="font-size: 0.75rem; color: var(--text-muted); background: rgba(255, 255, 255, 0.05); padding: 0.2rem 0.6rem; border-radius: 9999px; border: 1px solid var(--border-subtle);">{item.get('metrics', '')}</span>
                </div>
                <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem;">{item['title']}</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.5;">{item['description']}</p>
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem;">{tags_html}</div>
                <button class="btn-modern btn-glass btn-modal-trigger"
                        data-title="{item['title']}"
                        data-desc="{item.get('modal_details', item['description'])}"
                        data-metrics="{item.get('metrics', '')}"
                        data-category="{item['category']}">
                    <span>Explore Details</span>
                    <i data-lucide="arrow-right" style="width: 16px; height: 16px;"></i>
                </button>
            </article>""")
        showcase_grid_html = "\n".join(cards_html)

        bento_cards = []
        for feat in blueprint.features_bento:
            bento_cards.append(f"""
            <div class="glass-card bento-card tilt-card" style="padding: 1.75rem; border-radius: 1rem;">
                <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
                    <i data-lucide="{feat.get('icon', 'sparkles')}" style="width: 24px; height: 24px; color: var(--primary);"></i>
                </div>
                <div style="font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--primary); margin-bottom: 0.5rem;">{feat.get('highlight', 'Feature')}</div>
                <h4 style="font-size: 1.2rem; margin-bottom: 0.5rem;">{feat['title']}</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;">{feat['subtitle']}</p>
            </div>""")
        bento_grid_html = "\n".join(bento_cards)

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blueprint.app_title}</title>
    <meta name="description" content="{blueprint.meta_description}">

    {GOOGLE_FONTS_LINK}
    {THREE_JS_CDN}
    {LUCIDE_ICONS_CDN}
    <link rel="stylesheet" href="style.css">

    <style>
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
    </style>
</head>
<body>
    <div class="ambient-glow-layer">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
    </div>

    <!-- Navigation Bar -->
    <header class="glass-panel" style="position: sticky; top: 1rem; margin: 1rem auto; max-width: 1200px; width: calc(100% - 2rem); z-index: 50; padding: 0.75rem 1.5rem; border-radius: 9999px;">
        <nav style="display: flex; justify-content: space-between; align-items: center;">
            <a href="#" style="font-family: var(--font-heading); font-size: 1.35rem; font-weight: 800; color: var(--text-primary); text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">
                <i data-lucide="zap" style="color: var(--primary);"></i>
                <span class="gradient-text">{blueprint.app_title.split('—')[0].strip()}</span>
            </a>

            <div style="display: flex; align-items: center; gap: 2rem;">
                <div style="display: flex; gap: 1.5rem;" class="nav-links">
                    <a href="#showcase" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Showcase</a>
                    <a href="#features" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Capabilities</a>
                    <a href="#terminal" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Terminal</a>
                    <a href="#contact" style="color: var(--text-secondary); text-decoration: none; font-weight: 500; font-size: 0.9rem;">Connect</a>
                </div>

                <button id="theme-toggle" class="btn-modern btn-glass" style="padding: 0.45rem 0.85rem; border-radius: 9999px;" aria-label="Toggle Theme">
                    <i data-lucide="sun" id="theme-icon-sun" style="display: none; width: 18px; height: 18px;"></i>
                    <i data-lucide="moon" id="theme-icon-moon" style="display: inline; width: 18px; height: 18px;"></i>
                </button>
            </div>
        </nav>
    </header>

    <main>
        <!-- 3D Interactive Hero Section -->
        <section class="canvas-container" style="min-height: 85vh; display: flex; align-items: center; justify-content: center; padding: 4rem 1.5rem; text-align: center; position: relative;">
            <canvas id="webstudio-3d-canvas" class="hero-canvas"></canvas>

            <div class="hero-content" style="max-width: 850px; margin: 0 auto; position: relative; z-index: 10;">
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
                        <i data-lucide="sparkles" style="width: 18px; height: 18px;"></i>
                    </a>
                    <a href="#contact" class="btn-modern btn-glass">
                        <span>{blueprint.secondary_cta}</span>
                        <i data-lucide="arrow-right" style="width: 18px; height: 18px;"></i>
                    </a>
                </div>

                <!-- Interactive 3D HUD Controls Pill -->
                <div style="margin-top: 2.25rem;">
                    <div class="hud-controls-bar" style="display: inline-flex; align-items: center; gap: 0.75rem; background: var(--glass-bg); padding: 0.4rem 0.85rem; border-radius: 9999px; border: 1px solid var(--border-subtle);">
                        <button id="hud-wireframe-toggle" class="btn-modern btn-glass active" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 9999px;" title="Toggle 3D Wireframe / Solid Mesh">
                            <i data-lucide="box" style="width: 14px; height: 14px;"></i>
                            <span>Wireframe</span>
                        </button>
                        <button id="hud-speed-toggle" class="btn-modern btn-glass" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 9999px;" title="Cycle Rotation Speed">
                            <i data-lucide="gauge" style="width: 14px; height: 14px;"></i>
                            <span id="hud-speed-label">Speed: 1.0x</span>
                        </button>
                        <button id="hud-reset-view" class="btn-modern btn-glass" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 9999px;" title="Reset 3D Scene View">
                            <i data-lucide="rotate-ccw" style="width: 14px; height: 14px;"></i>
                            <span>Reset</span>
                        </button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Live Telemetry Strip -->
        <section style="max-width: 1200px; margin: -2.5rem auto 3.5rem auto; padding: 0 1.5rem; position: relative; z-index: 10;">
            <div class="glass-card telemetry-strip" style="border-color: var(--border-highlight);">
                <div class="telemetry-item">
                    <div class="stat-number gradient-text" data-target="60">60</div>
                    <span class="stat-label">FPS Native 3D WebGL</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text" data-target="99.9" data-decimals="1" data-suffix="%">99.9%</div>
                    <span class="stat-label">Autonomous SLA</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text" data-target="45" data-suffix="ms">45ms</div>
                    <span class="stat-label">P99 Frame Latency</span>
                </div>
                <div class="telemetry-item">
                    <div class="stat-number gradient-text" data-target="100" data-suffix="%">100%</div>
                    <span class="stat-label">Zero Placeholder Rigor</span>
                </div>
            </div>
        </section>

        <!-- Showcase Cards Section -->
        <section id="showcase" style="max-width: 1200px; margin: 0 auto 5rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 2.5rem;">
                <h2 style="font-size: 2.2rem; margin-bottom: 0.75rem;">Featured Engineering Systems</h2>
                <p style="color: var(--text-secondary); max-width: 550px; margin: 0 auto;">Zero dummy data. Verified multi-agent architectures.</p>
            </div>
            <div class="filter-container">
                {filters_html}
            </div>
            <div id="showcase-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.75rem;">
                {showcase_grid_html}
            </div>
        </section>

        <!-- Capabilities Bento Section -->
        <section id="features" style="max-width: 1200px; margin: 0 auto 5rem auto; padding: 0 1.5rem;">
            <div style="text-align: center; margin-bottom: 3rem;">
                <h2 style="font-size: 2.2rem; margin-bottom: 0.75rem;">Core Competencies</h2>
                <p style="color: var(--text-secondary);">Production-ready capabilities built into every autonomous synthesis.</p>
            </div>
            <div class="bento-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
                {bento_grid_html}
            </div>
        </section>

        <!-- Cyber Command Terminal Section -->
        <section id="terminal" style="max-width: 850px; margin: 0 auto 5rem auto; padding: 0 1.5rem;">
            <div class="terminal-container">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <div class="terminal-dot" style="background: #ef4444;"></div>
                        <div class="terminal-dot" style="background: #f59e0b;"></div>
                        <div class="terminal-dot" style="background: #10b981;"></div>
                    </div>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">forge-terminal://session-active</span>
                </div>
                <div id="terminal-output" class="terminal-output">
                    <div>Welcome to CyberDeck Command Terminal 3.0.</div>
                    <div>Type <span style="color: var(--primary);">'help'</span> to inspect available diagnostics.</div>
                </div>
                <div class="terminal-chips">
                    <button class="terminal-chip" data-cmd="help">help</button>
                    <button class="terminal-chip" data-cmd="skills">skills</button>
                    <button class="terminal-chip" data-cmd="projects">projects</button>
                    <button class="terminal-chip" data-cmd="stats">stats</button>
                    <button class="terminal-chip" data-cmd="clear">clear</button>
                </div>
                <form id="terminal-form" class="terminal-input-row">
                    <span class="terminal-prompt">&gt;</span>
                    <input type="text" id="terminal-input" class="terminal-input" placeholder="Type a command (e.g. 'help', 'skills')..." autocomplete="off">
                </form>
            </div>
        </section>

        <!-- Contact Section -->
        <section id="contact" style="max-width: 600px; margin: 0 auto 5rem auto; padding: 0 1.5rem; text-align: center;">
            <h2 style="font-size: 2rem; margin-bottom: 0.75rem;">Initialize Collaboration</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">Connect with the engineering team for high-throughput autonomous systems.</p>
            <form id="contact-form" class="glass-card" style="padding: 2rem; border-radius: 1rem; display: flex; flex-direction: column; gap: 1rem; text-align: left;">
                <div>
                    <label style="display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;">Your Name</label>
                    <input type="text" required placeholder="Elena Rostova" style="width: 100%; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                </div>
                <div>
                    <label style="display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;">Email</label>
                    <input type="email" required placeholder="elena@autonomous.dev" style="width: 100%; padding: 0.65rem 0.85rem; border-radius: 0.5rem; background: var(--bg-base); border: 1px solid var(--border-subtle); color: var(--text-primary); outline: none;">
                </div>
                <button type="submit" class="btn-modern btn-primary" style="margin-top: 0.5rem;">
                    <span>Transmit Message</span>
                    <i data-lucide="send" style="width: 16px; height: 16px;"></i>
                </button>
            </form>
        </section>
    </main>

    <!-- Details Modal Dialog -->
    <div id="details-modal" class="modal-backdrop" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 1100; display: none; align-items: center; justify-content: center; padding: 1.5rem;">
        <div class="modal-dialog glass-panel" style="background: var(--bg-surface); border: 1px solid var(--border-highlight); border-radius: 1.25rem; width: 100%; max-width: 550px; padding: 2rem; position: relative;">
            <button id="modal-close-btn" style="position: absolute; top: 1.25rem; right: 1.25rem; background: transparent; border: none; color: var(--text-muted); cursor: pointer;">
                <i data-lucide="x" style="width: 20px; height: 20px;"></i>
            </button>
            <span id="modal-category" style="font-size: 0.75rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">CATEGORY</span>
            <h3 id="modal-title" style="font-size: 1.4rem; margin: 0.5rem 0 1rem 0;">Project Title</h3>
            <p id="modal-desc" style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">Description</p>
            <div id="modal-metrics" style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); padding: 0.75rem 1rem; border-radius: 0.5rem; font-size: 0.85rem;"></div>
        </div>
    </div>

    <!-- Footer -->
    <footer style="max-width: 1200px; margin: 4rem auto 2rem auto; padding: 2rem 1.5rem; border-top: 1px solid var(--border-subtle); text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        <p>© 2026 {blueprint.app_title.split('—')[0].strip()}. Synthesized autonomously with Project FORGE WebStudio.</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
"""

    @classmethod
    def _generate_portfolio_js(
        cls, blueprint: DomainBlueprint, primary_hex: str, secondary_hex: str
    ) -> str:
        three_d_code = generate_three_d_scene_script(
            canvas_id="webstudio-3d-canvas",
            scene_mode="portfolio",
            primary_hex=primary_hex,
            accent_hex=secondary_hex,
            domain_type="portfolio",
        )
        tilt_code = generate_3d_tilt_script()

        return f"""// ==========================================================================
// ForgeWebStudio 3.0 — Portfolio / Cyberpunk Application Runtime
// ==========================================================================

{three_d_code}

{tilt_code}

document.addEventListener('DOMContentLoaded', () => {{
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Theme Management
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    function applyTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        if (sunIcon && moonIcon) {{
            sunIcon.style.display = theme === 'light' ? 'inline' : 'none';
            moonIcon.style.display = theme === 'dark' ? 'inline' : 'none';
        }}
    }}
    const savedTheme = localStorage.getItem('forge_theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggle) {{
        themeToggle.addEventListener('click', () => {{
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            localStorage.setItem('forge_theme', next);
        }});
    }}

    // Telemetry Stat Number Animations
    function animateCounters() {{
        const counters = document.querySelectorAll('.stat-number');
        counters.forEach(counter => {{
            const target = parseFloat(counter.getAttribute('data-target')) || 0;
            const decimals = parseInt(counter.getAttribute('data-decimals') || '0', 10);
            const suffix = counter.getAttribute('data-suffix') || '';
            let current = 0;
            const step = target / 30;
            const timer = setInterval(() => {{
                current += step;
                if (current >= target) {{
                    current = target;
                    clearInterval(timer);
                }}
                counter.textContent = current.toFixed(decimals) + suffix;
            }}, 30);
        }});
    }}
    animateCounters();

    // Category Filter Buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.showcase-card');

    filterBtns.forEach(btn => {{
        btn.addEventListener('click', () => {{
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');
            cards.forEach(card => {{
                const cat = card.getAttribute('data-category');
                if (filter === 'All Systems' || filter === cat || cat.includes(filter)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }});
    }});

    // Details Modal
    const modal = document.getElementById('details-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    document.querySelectorAll('.btn-modal-trigger').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const title = btn.getAttribute('data-title');
            const desc = btn.getAttribute('data-desc');
            const cat = btn.getAttribute('data-category');
            const metrics = btn.getAttribute('data-metrics');

            const tEl = document.getElementById('modal-title');
            const dEl = document.getElementById('modal-desc');
            const cEl = document.getElementById('modal-category');
            const mEl = document.getElementById('modal-metrics');

            if (tEl) tEl.textContent = title;
            if (dEl) dEl.textContent = desc;
            if (cEl) cEl.textContent = cat;
            if (mEl) mEl.textContent = metrics ? `Metrics: ${{metrics}}` : '';

            if (modal) modal.style.display = 'flex';
        }});
    }});

    if (modalCloseBtn) {{
        modalCloseBtn.addEventListener('click', () => {{
            if (modal) modal.style.display = 'none';
        }});
    }}

    // CyberDeck Command Terminal
    const termOutput = document.getElementById('terminal-output');
    const termInput = document.getElementById('terminal-input');
    const termForm = document.getElementById('terminal-form');
    const termChips = document.querySelectorAll('.terminal-chip');

    const terminalCommands = {{
        help: () => [
            "Available CyberDeck Diagnostic Commands:",
            "  • help     - Print available CLI commands",
            "  • skills   - List engineering specializations & shader pipelines",
            "  • projects - Dump featured production architectures",
            "  • stats    - Output 3D engine telemetry & frame rates",
            "  • clear    - Clear command output buffer"
        ],
        skills: () => [
            "Architectural Competencies:",
            "  • WebGL 3D & Shaders: Three.js, GLSL, Signed Distance Fields",
            "  • Autonomous Systems: Multi-agent orchestration, TaskGraph execution",
            "  • High-Throughput Engines: Rust, WASM, zero-copy buffers",
            "  • Modern Frontend: Glassmorphic token architecture, bento grids"
        ],
        projects: () => [
            "Featured Production Systems:",
            "  1. OmniNet 3D Neural Matrix    [Three.js / WebGL / Graph Neural Networks]",
            "  2. CyberDeck Command Console   [TypeScript / WebSocket / Real-Time Telemetry]",
            "  3. GhostProtocol Raymarcher    [GLSL / Fragment Shaders / Raymarching]",
            "  4. Chronos Quantum Ledger      [Rust / WASM / Sub-Microsecond Engine]"
        ],
        stats: () => [
            "Runtime Diagnostics & Telemetry:",
            "  • Engine: Project FORGE WebStudio 3.0",
            "  • 3D Scene Pipeline: Three.js WebGL Native",
            "  • Frame Rate: 60 FPS Native WebGL",
            "  • Status: ONLINE • Zero Unhandled Exceptions"
        ],
        clear: () => {{
            if (termOutput) termOutput.innerHTML = "";
            return [];
        }}
    }};

    function runTerminalCommand(cmdText) {{
        if (!termOutput) return;
        const cleanCmd = (cmdText || "").trim().toLowerCase();
        if (!cleanCmd) return;

        const cmdLine = document.createElement("div");
        cmdLine.style.color = "#ffffff";
        cmdLine.innerHTML = `<span style="color: var(--primary);">&gt;</span> ${{cleanCmd}}`;
        termOutput.appendChild(cmdLine);

        if (terminalCommands[cleanCmd]) {{
            const lines = terminalCommands[cleanCmd]();
            lines.forEach(l => {{
                const outLine = document.createElement("div");
                outLine.textContent = l;
                termOutput.appendChild(outLine);
            }});
        }} else {{
            const errLine = document.createElement("div");
            errLine.style.color = "var(--danger)";
            errLine.textContent = `Command not recognized: '${{cleanCmd}}'. Type 'help' for available commands.`;
            termOutput.appendChild(errLine);
        }}

        termOutput.scrollTop = termOutput.scrollHeight;
        if (termInput) termInput.value = "";
    }}

    if (termForm) {{
        termForm.addEventListener("submit", (e) => {{
            e.preventDefault();
            if (termInput) runTerminalCommand(termInput.value);
        }});
    }}

    termChips.forEach(chip => {{
        chip.addEventListener("click", () => {{
            const cmd = chip.getAttribute("data-cmd");
            if (cmd) runTerminalCommand(cmd);
        }});
    }});
}});
"""

    @classmethod
    def _generate_readme(cls, goal: str, blueprint: DomainBlueprint) -> str:
        return f"""# {blueprint.app_title}

Generated autonomously by **Project FORGE 3.0 (WebStudio Engine)**.

## 🌟 Architectural Features
- **Domain Archetype**: `{blueprint.domain_type.upper()}`
- **3D & Interactive Canvas**: Three.js WebGL interactive 3D geometry with high-performance 60 FPS particle physics fallback.
- **Modern Glassmorphic Design System**: Tailwind CSS, Lucide vector icons, Google Fonts typography scale, and responsive bento grids.
- **Zero External Bundler**: Runs instantly with zero `npm install` or node compilation required.
- **Interactive State**: Real-time domain components (e.g. cart drawer, pricing switch, ROI slider, telemetry gauges).
- **Theme Resilience**: Built-in dark/light mode toggle with `localStorage` memory.

## 🚀 Instant Preview
```powershell
python -m http.server 5000
```
Open [http://localhost:5000](http://localhost:5000) in your browser.
"""
