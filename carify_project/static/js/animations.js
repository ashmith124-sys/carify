/*
    CARIFY — ELITE 3D ANIMATION ENGINE
    Inspired by Cred.club's premium interaction design
    Features: Custom Cursor, 3D Card Tilt, Magnetic Buttons,
              Parallax Depth, Smooth Reveal, Ambient Particles
*/

(function () {
    'use strict';

    // ─────────────────────────────────────────────
    // 1. CUSTOM LUXURY CURSOR
    // ─────────────────────────────────────────────
    function initCursor() {
        const cursor = document.createElement('div');
        cursor.id = 'carify-cursor';
        cursor.innerHTML = '<div class="cursor-dot"></div><div class="cursor-ring"></div>';
        document.body.appendChild(cursor);

        let mouseX = 0, mouseY = 0;
        let ringX = 0, ringY = 0;
        let isHovering = false;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        // Ring follows with smooth lag (Cred-style)
        function animateCursor() {
            const dot = cursor.querySelector('.cursor-dot');
            const ring = cursor.querySelector('.cursor-ring');

            // Dot follows instantly
            dot.style.transform = `translate(${mouseX}px, ${mouseY}px) translate(-50%, -50%)`;

            // Ring follows with easing
            ringX += (mouseX - ringX) * 0.12;
            ringY += (mouseY - ringY) * 0.12;
            ring.style.transform = `translate(${ringX}px, ${ringY}px) translate(-50%, -50%)`;

            requestAnimationFrame(animateCursor);
        }
        animateCursor();

        // Cursor state changes
        const magneticTargets = document.querySelectorAll('a, button, .shop-card, .btn, .nav-link, .lifestyle-section');
        magneticTargets.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.classList.add('hover');
            });
            el.addEventListener('mouseleave', () => {
                cursor.classList.remove('hover');
            });
        });

        // Hide on touch
        document.addEventListener('touchstart', () => {
            cursor.style.display = 'none';
        });
    }

    // ─────────────────────────────────────────────
    // 2. 3D CARD TILT ENGINE
    // ─────────────────────────────────────────────
    function initCardTilt() {
        const cards = document.querySelectorAll('.shop-card, .glass-panel, .card, .cg-pcard');

        cards.forEach(card => {
            // Enable 3D context
            card.style.transformStyle = 'preserve-3d';
            card.style.transition = 'transform 0.1s ease';
            card.style.willChange = 'transform';

            let rect;

            card.addEventListener('mouseenter', () => {
                rect = card.getBoundingClientRect();
                card.style.transition = 'transform 0.1s ease, box-shadow 0.3s ease';
            });

            card.addEventListener('mousemove', (e) => {
                if (!rect) rect = card.getBoundingClientRect();

                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                // Normalize -1 to 1
                const normalX = (x - centerX) / centerX;
                const normalY = (y - centerY) / centerY;

                const rotateX = normalY * -10; // max 10deg
                const rotateY = normalX * 10;

                // Subtle shine effect (x,y position on card)
                const shineX = (x / rect.width) * 100;
                const shineY = (y / rect.height) * 100;

                card.style.transform = `
                    perspective(1000px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    translateZ(10px)
                `;

                // Dynamic shadow
                card.style.boxShadow = `
                    ${-normalX * 20}px ${-normalY * 20}px 40px rgba(0,0,0,0.5),
                    0 0 80px rgba(217, 145, 90, 0.05)
                `;

                // Inject shine overlay
                let shine = card.querySelector('.tilt-shine');
                if (!shine) {
                    shine = document.createElement('div');
                    shine.className = 'tilt-shine';
                    card.style.position = 'relative';
                    card.style.overflow = 'hidden';
                    card.appendChild(shine);
                }
                shine.style.background = `radial-gradient(circle at ${shineX}% ${shineY}%, rgba(255,255,255,0.06) 0%, transparent 60%)`;
                shine.style.opacity = '1';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transition = 'transform 0.6s cubic-bezier(0.16,1,0.3,1), box-shadow 0.6s ease';
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
                card.style.boxShadow = '';

                const shine = card.querySelector('.tilt-shine');
                if (shine) shine.style.opacity = '0';
            });
        });
    }

    // ─────────────────────────────────────────────
    // 3. MAGNETIC BUTTON EFFECT
    // ─────────────────────────────────────────────
    function initMagneticButtons() {
        const buttons = document.querySelectorAll('.btn-primary, .btn-outline');

        buttons.forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;

                btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px) translateZ(5px)`;
                btn.style.transition = 'transform 0.1s ease';
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translate(0, 0) translateZ(0)';
                btn.style.transition = 'transform 0.6s cubic-bezier(0.16,1,0.3,1)';
            });
        });
    }

    // ─────────────────────────────────────────────
    // 4. PARALLAX DEPTH LAYERS
    // ─────────────────────────────────────────────
    function initParallax() {
        const layers = [
            { selector: '.lifestyle-bg', factor: 0.3 },
            { selector: '.hero-slide .lifestyle-bg', factor: 0.4 },
        ];

        function onScroll() {
            const scrollY = window.scrollY;

            layers.forEach(({ selector, factor }) => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.transform = `scale(1.1) translateY(${scrollY * factor}px)`;
                    el.style.willChange = 'transform';
                });
            });

            // Subtle text parallax on hero content
            const heroContent = document.querySelector('.lifestyle-content');
            if (heroContent) {
                heroContent.style.transform = `translateY(${scrollY * 0.2}px)`;
                heroContent.style.opacity = `${1 - scrollY / 600}`;
            }
        }

        window.addEventListener('scroll', onScroll, { passive: true });
    }

    // ─────────────────────────────────────────────
    // 5. SECTION 3D REVEAL (Cred-style depth entries)
    // ─────────────────────────────────────────────
    function initSectionReveal() {
        const style = document.createElement('style');
        style.textContent = `
            [data-appear] {
                opacity: 0;
                transform: perspective(1000px) translateY(50px) rotateX(8deg);
                transform-origin: center bottom;
                transition: opacity 1.0s cubic-bezier(0.16,1,0.3,1),
                            transform 1.0s cubic-bezier(0.16,1,0.3,1);
            }
            [data-appear].visible {
                opacity: 1;
                transform: perspective(1000px) translateY(0) rotateX(0deg);
            }
        `;
        document.head.appendChild(style);
    }

    // ─────────────────────────────────────────────
    // 6. FLOATING AMBIENT PARTICLES
    // ─────────────────────────────────────────────
    function initParticles() {
        const canvas = document.createElement('canvas');
        canvas.id = 'carify-particles';
        canvas.style.cssText = `
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.4;
        `;
        document.body.insertBefore(canvas, document.body.firstChild);

        const ctx = canvas.getContext('2d');
        let particles = [];

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', resize);

        class Particle {
            constructor() { this.reset(); }
            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 1.5 + 0.5;
                this.speedX = (Math.random() - 0.5) * 0.3;
                this.speedY = (Math.random() - 0.5) * 0.3;
                this.opacity = Math.random() * 0.4 + 0.1;
                this.color = Math.random() > 0.5 ? '217, 145, 90' : '255, 255, 255';
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                    this.reset();
                }
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
                ctx.fill();
            }
        }

        // Create particles (fewer = more subtle)
        for (let i = 0; i < 60; i++) {
            particles.push(new Particle());
        }

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => { p.update(); p.draw(); });
            requestAnimationFrame(animate);
        }
        animate();
    }

    // ─────────────────────────────────────────────
    // 7. SMOOTH HORIZONTAL SCROLL (touch-drag for arrivals row)
    // ─────────────────────────────────────────────
    function initSmoothDragScroll() {
        const sliders = document.querySelectorAll('.horizontal-scroll-row, .cg-prow');

        sliders.forEach(slider => {
            let isDown = false;
            let startX, scrollLeft;

            slider.addEventListener('mousedown', (e) => {
                isDown = true;
                slider.style.cursor = 'grabbing';
                startX = e.pageX - slider.offsetLeft;
                scrollLeft = slider.scrollLeft;
            });

            slider.addEventListener('mouseleave', () => {
                isDown = false;
                slider.style.cursor = 'grab';
            });

            slider.addEventListener('mouseup', () => {
                isDown = false;
                slider.style.cursor = 'grab';
            });

            slider.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - slider.offsetLeft;
                const walk = (x - startX) * 1.5;
                slider.scrollLeft = scrollLeft - walk;
            });

            slider.style.cursor = 'grab';
        });
    }

    function injectCursorStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Restore system cursor */
            * { cursor: auto; }
            a, button, [role="button"], .shop-card, .btn, .nav-link, .cg-btn-primary, .cg-btn-ghost { 
                cursor: pointer !important; 
            }
            input, textarea { 
                cursor: text; 
            }
            
            #carify-cursor { display: none !important; }

            .tilt-shine {
                position: absolute;
                inset: 0;
                pointer-events: none;
                border-radius: inherit;
                transition: opacity 0.3s ease;
                opacity: 0;
                z-index: 10;
            }

            @media (max-width: 768px) {
                * { cursor: auto !important; }
            }
        `;
        document.head.appendChild(style);
    }


    // ─────────────────────────────────────────────
    // BOOT
    // ─────────────────────────────────────────────
    function boot() {
        injectCursorStyles();
        initSectionReveal();
        initParticles();
        initParallax();

        requestAnimationFrame(() => {
            setTimeout(() => {
                // initCursor(); // Disabled to restore default cursor
                initCardTilt();
                initMagneticButtons();
                initSmoothDragScroll();
            }, 100);
        });
    }

    // EXPOSE TO GLOBAL BRIDGE
    window.CarifyAnimations = {
        reinit: () => {
             initCardTilt();
             initMagneticButtons();
             initSmoothDragScroll();
        }
    };


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();
