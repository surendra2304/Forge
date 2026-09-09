"""
ForgeWebStudio 3D & Interactive Canvas Engine.
Provides client-side 3D WebGL scenes, interactive particle physics, 3D card tilt, and mouse-reactive visual shaders.
Zero external bundler required; runs natively in modern browsers.
"""


def generate_three_d_scene_script(
    canvas_id: str = "webstudio-3d-canvas",
    scene_mode: str = "particles_mesh",
    primary_hex: str = "#6366f1",
    accent_hex: str = "#a855f7",
) -> str:
    """
    Generates high-performance, responsive 3D / WebGL JavaScript code.
    Supports Three.js interactive 3D geometry or high-speed 60FPS 2D/3D particle constellations.
    """
    return f"""// ==========================================================================
// ForgeWebStudio 3.0 — 3D Scene & Particle Physics Engine
// ==========================================================================

function init3DHeroCanvas() {{
    const canvas = document.getElementById("{canvas_id}");
    if (!canvas) return;

    // Check if Three.js is loaded, retry briefly if still streaming from CDN
    let attempts = 0;
    function tryMount() {{
        if (typeof THREE !== 'undefined') {{
            initThreeJSScene(canvas);
        }} else if (attempts < 10) {{
            attempts++;
            setTimeout(tryMount, 200);
        }} else {{
            initHighSpeedParticleCanvas(canvas);
        }}
    }}
    tryMount();

    function initThreeJSScene(targetCanvas) {{
        const container = targetCanvas.parentElement || document.body;
        let width = targetCanvas.clientWidth || container.clientWidth || window.innerWidth;
        let height = targetCanvas.clientHeight || container.clientHeight || window.innerHeight || 600;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(65, width / height, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ canvas: targetCanvas, alpha: true, antialias: true, powerPreference: "high-performance" }});
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Group containing all 3D geometries
        const group = new THREE.Group();
        scene.add(group);

        // 1. Primary Cybernetic Mesh (High-Fidelity Torus Knot)
        const mainGeometry = new THREE.TorusKnotGeometry(2.0, 0.45, 128, 32);
        const mainMaterial = new THREE.MeshStandardMaterial({{
            color: '{primary_hex}',
            wireframe: true,
            roughness: 0.15,
            metalness: 0.9,
            emissive: '{accent_hex}',
            emissiveIntensity: 0.35,
            transparent: true,
            opacity: 0.9
        }});
        const mainMesh = new THREE.Mesh(mainGeometry, mainMaterial);
        group.add(mainMesh);

        // 2. Inner Glowing Core
        const coreGeometry = new THREE.IcosahedronGeometry(1.2, 2);
        const coreMaterial = new THREE.MeshStandardMaterial({{
            color: '{accent_hex}',
            wireframe: false,
            roughness: 0.2,
            metalness: 0.8,
            emissive: '{primary_hex}',
            emissiveIntensity: 0.5
        }});
        const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
        group.add(coreMesh);

        // 3. Orbital Particle Galaxy
        const particlesCount = 500;
        const positions = new Float32Array(particlesCount * 3);
        const colors = new Float32Array(particlesCount * 3);
        const c1 = new THREE.Color('{primary_hex}');
        const c2 = new THREE.Color('{accent_hex}');

        for (let i = 0; i < particlesCount * 3; i += 3) {{
            positions[i] = (Math.random() - 0.5) * 16;
            positions[i + 1] = (Math.random() - 0.5) * 16;
            positions[i + 2] = (Math.random() - 0.5) * 16;

            const mixed = Math.random() > 0.5 ? c1 : c2;
            colors[i] = mixed.r;
            colors[i + 1] = mixed.g;
            colors[i + 2] = mixed.b;
        }}
        const particlesGeometry = new THREE.BufferGeometry();
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const particlesMaterial = new THREE.PointsMaterial({{
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.85
        }});
        const particleMesh = new THREE.Points(particlesGeometry, particlesMaterial);
        group.add(particleMesh);

        // 4. Lighting Rig
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight('{primary_hex}', 3, 50);
        pointLight1.position.set(6, 4, 5);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight('{accent_hex}', 3, 50);
        pointLight2.position.set(-6, -4, 5);
        scene.add(pointLight2);

        camera.position.z = 5.6;

        // Mouse Parallax & Dynamic Interaction
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;
        let rotSpeed = 1.0;

        window.addEventListener('mousemove', (e) => {{
            mouseX = (e.clientX / window.innerWidth) * 2 - 1;
            mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
        }});

        // Interactive 3D HUD Controls Wiring
        const wireframeBtn = document.getElementById('hud-wireframe-toggle');
        if (wireframeBtn) {{
            wireframeBtn.addEventListener('click', () => {{
                mainMaterial.wireframe = !mainMaterial.wireframe;
                wireframeBtn.classList.toggle('active');
            }});
        }}

        const speedBtn = document.getElementById('hud-speed-toggle');
        if (speedBtn) {{
            speedBtn.addEventListener('click', () => {{
                rotSpeed = rotSpeed === 1.0 ? 2.5 : (rotSpeed === 2.5 ? 5.0 : 1.0);
                speedBtn.textContent = `Speed: ${{rotSpeed}}x`;
            }});
        }}

        const resetBtn = document.getElementById('hud-reset-view');
        if (resetBtn) {{
            resetBtn.addEventListener('click', () => {{
                rotSpeed = 1.0;
                if (speedBtn) speedBtn.textContent = 'Speed: 1.0x';
                mainMaterial.wireframe = true;
                if (wireframeBtn) wireframeBtn.classList.add('active');
                targetX = 0;
                targetY = 0;
                group.position.x = 0;
                group.position.y = 0;
            }});
        }}

        // Animation Loop
        let clock = new THREE.Clock();
        function animate() {{
            requestAnimationFrame(animate);
            const delta = clock.getDelta();

            // Rotations
            mainMesh.rotation.x += 0.004 * rotSpeed;
            mainMesh.rotation.y += 0.007 * rotSpeed;
            coreMesh.rotation.x -= 0.008 * rotSpeed;
            coreMesh.rotation.y += 0.005 * rotSpeed;
            particleMesh.rotation.y -= 0.001 * rotSpeed;

            // Smooth mouse follow (easing)
            targetX += (mouseX * 0.8 - targetX) * 0.05;
            targetY += (mouseY * 0.8 - targetY) * 0.05;
            group.position.x = targetX;
            group.position.y = targetY;

            renderer.render(scene, camera);
        }}
        animate();

        // Responsive Resize
        function onResize() {{
            const w = targetCanvas.clientWidth || container.clientWidth || window.innerWidth;
            const h = targetCanvas.clientHeight || container.clientHeight || window.innerHeight || 600;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }}
        window.addEventListener('resize', onResize);
    }}

    function initHighSpeedParticleCanvas(targetCanvas) {{
        const ctx = targetCanvas.getContext('2d');
        let width = targetCanvas.width = targetCanvas.clientWidth || window.innerWidth;
        let height = targetCanvas.height = targetCanvas.clientHeight || 600;

        const particles = [];
        const numParticles = Math.min(100, Math.floor(width / 12));
        const maxDistance = 130;

        let mouse = {{ x: null, y: null, radius: 150 }};
        window.addEventListener('mousemove', (e) => {{
            const rect = targetCanvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
        }});
        window.addEventListener('mouseleave', () => {{
            mouse.x = null;
            mouse.y = null;
        }});

        class Particle {{
            constructor() {{
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 1.5;
                this.vy = (Math.random() - 0.5) * 1.5;
                this.radius = Math.random() * 2.2 + 1.2;
                this.baseAlpha = Math.random() * 0.5 + 0.4;
            }}
            update() {{
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;

                if (mouse.x !== null) {{
                    const dx = mouse.x - this.x;
                    const dy = mouse.y - this.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < mouse.radius) {{
                        const force = (mouse.radius - dist) / mouse.radius;
                        this.x -= (dx / dist) * force * 3;
                        this.y -= (dy / dist) * force * 3;
                    }}
                }}
            }}
            draw() {{
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = '{primary_hex}';
                ctx.globalAlpha = this.baseAlpha;
                ctx.fill();
            }}
        }}

        for (let i = 0; i < numParticles; i++) {{
            particles.push(new Particle());
        }}

        function animate() {{
            ctx.clearRect(0, 0, width, height);
            for (let i = 0; i < particles.length; i++) {{
                particles[i].update();
                particles[i].draw();

                for (let j = i + 1; j < particles.length; j++) {{
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < maxDistance) {{
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = '{accent_hex}';
                        ctx.globalAlpha = (1 - dist / maxDistance) * 0.35;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }}
                }}
            }}
            requestAnimationFrame(animate);
        }}
        animate();

        window.addEventListener('resize', () => {{
            width = targetCanvas.width = targetCanvas.clientWidth || window.innerWidth;
            height = targetCanvas.height = targetCanvas.clientHeight || 600;
        }});
    }}
}}

if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init3DHeroCanvas);
}} else {{
    init3DHeroCanvas();
}}
"""


def generate_3d_tilt_script() -> str:
    """
    Generates interactive 3D perspective tilt effect for cards and bento boxes.
    Adds specular glare and perspective rotation on cursor hover.
    """
    return """// ==========================================================================
// ForgeWebStudio 3.0 — 3D Tilt Card Perspective Engine
// ==========================================================================

function init3DTiltCards() {
    const cards = document.querySelectorAll('.tilt-card, .glass-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -8;
            const rotateY = ((x - centerX) / centerX) * 8;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
            card.style.transition = 'transform 0.4s ease';
        });

        card.addEventListener('mouseenter', () => {
            card.style.transition = 'none';
        });
    });
}

document.addEventListener('DOMContentLoaded', init3DTiltCards);
"""


class Web3DEngine:
    """Convenience wrapper for 3D scripts and particle physics engines."""

    @staticmethod
    def generate_engine_js(
        canvas_id: str = "webstudio-3d-canvas",
        scene_mode: str = "particles_mesh",
        primary_hex: str = "#6366f1",
        accent_hex: str = "#a855f7",
    ) -> str:
        return generate_three_d_scene_script(canvas_id, scene_mode, primary_hex, accent_hex)

    @staticmethod
    def generate_card_tilt_js() -> str:
        return generate_3d_tilt_script()

