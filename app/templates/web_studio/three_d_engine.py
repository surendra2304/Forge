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

(function init3DHeroCanvas() {{
    const canvas = document.getElementById("{canvas_id}");
    if (!canvas) return;

    // Check if Three.js is loaded
    if (typeof THREE !== 'undefined') {{
        initThreeJSScene(canvas);
    }} else {{
        initHighSpeedParticleCanvas(canvas);
    }}

    function initThreeJSScene(targetCanvas) {{
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, targetCanvas.clientWidth / targetCanvas.clientHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ canvas: targetCanvas, alpha: true, antialias: true }});
        renderer.setSize(targetCanvas.clientWidth, targetCanvas.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Create 3D Geometric Torus / Mesh
        const geometry = new THREE.IcosahedronGeometry(2.2, 2);
        const material = new THREE.MeshStandardMaterial({{
            color: '{primary_hex}',
            roughness: 0.2,
            metalness: 0.85,
            wireframe: true,
            emissive: '{accent_hex}',
            emissiveIntensity: 0.2
        }});
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);

        // Surrounding Particle Cloud
        const particlesCount = 350;
        const positions = new Float32Array(particlesCount * 3);
        for (let i = 0; i < particlesCount * 3; i += 3) {{
            positions[i] = (Math.random() - 0.5) * 12;
            positions[i + 1] = (Math.random() - 0.5) * 12;
            positions[i + 2] = (Math.random() - 0.5) * 12;
        }}
        const particlesGeometry = new THREE.BufferGeometry();
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const particlesMaterial = new THREE.PointsMaterial({{
            size: 0.04,
            color: '{accent_hex}',
            transparent: true,
            opacity: 0.8
        }});
        const particleMesh = new THREE.Points(particlesGeometry, particlesMaterial);
        scene.add(particleMesh);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        scene.add(ambientLight);

        const pointLight = new THREE.PointLight('{primary_hex}', 2, 50);
        pointLight.position.set(5, 5, 5);
        scene.add(pointLight);

        camera.position.z = 4.8;

        // Mouse Parallax Interaction
        let mouseX = 0, mouseY = 0;
        window.addEventListener('mousemove', (e) => {{
            mouseX = (e.clientX / window.innerWidth) * 2 - 1;
            mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
        }});

        function animate() {{
            requestAnimationFrame(animate);
            mesh.rotation.x += 0.003;
            mesh.rotation.y += 0.005;
            particleMesh.rotation.y -= 0.001;

            mesh.position.x += (mouseX * 0.5 - mesh.position.x) * 0.05;
            mesh.position.y += (mouseY * 0.5 - mesh.position.y) * 0.05;

            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            const w = targetCanvas.clientWidth;
            const h = targetCanvas.clientHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }});
    }}

    function initHighSpeedParticleCanvas(targetCanvas) {{
        const ctx = targetCanvas.getContext('2d');
        let width = targetCanvas.width = targetCanvas.clientWidth;
        let height = targetCanvas.height = targetCanvas.clientHeight;

        const particles = [];
        const numParticles = Math.min(80, Math.floor(width / 15));
        const maxDistance = 120;

        let mouse = {{ x: null, y: null, radius: 140 }};

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
                this.vx = (Math.random() - 0.5) * 1.2;
                this.vy = (Math.random() - 0.5) * 1.2;
                this.radius = Math.random() * 2 + 1.2;
                this.baseAlpha = Math.random() * 0.5 + 0.3;
            }}
            update() {{
                this.x += this.vx;
                this.y += this.vy;

                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;

                // Mouse interaction
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
                        ctx.globalAlpha = (1 - dist / maxDistance) * 0.25;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }}
                }}
            }}
            requestAnimationFrame(animate);
        }}
        animate();

        window.addEventListener('resize', () => {{
            width = targetCanvas.width = targetCanvas.clientWidth;
            height = targetCanvas.height = targetCanvas.clientHeight;
        }});
    }}
}})();
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

