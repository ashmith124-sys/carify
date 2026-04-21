/*
    CARIFY — CINEMATIC LUXURY 3D CAR EXPERIENCE
    ════════════════════════════════════════════
    Inspired by Rolls-Royce, Genesis & Lamborghini web presentations.
    
    Features:
    ▸ Ferrari GLTF model with physical clearcoat paint
    ▸ UnrealBloom post-processing (cinematic headlight glow)
    ▸ Mirror Reflector floor
    ▸ HDRI Venice sunset environment
    ▸ Cinematic reveal camera animation (intro pull-back)
    ▸ Animated studio sweeping rim light
    ▸ Floating copper micro-particles
    ▸ Mouse parallax + smooth orbit
    ▸ ACES filmic tone mapping
*/

import * as THREE from 'three';
import { GLTFLoader }       from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader }      from 'three/addons/loaders/DRACOLoader.js';
import { RGBELoader }       from 'three/addons/loaders/RGBELoader.js';
import { EffectComposer }   from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }       from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass }  from 'three/addons/postprocessing/UnrealBloomPass.js';
import { Reflector }        from 'three/addons/objects/Reflector.js';

// ─────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────
const container = document.getElementById('car-hero-container');
const canvas    = document.getElementById('car-hero-canvas');
if (!container || !canvas) throw new Error('Canvas elements missing');

const W = container.clientWidth;
const H = container.clientHeight;

// ─────────────────────────────────────────────────────────────
// RENDERER — Cinematic grade
// ─────────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(W, H);
renderer.shadowMap.enabled      = true;
renderer.shadowMap.type         = THREE.PCFSoftShadowMap;
renderer.toneMapping            = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure    = 0.9;
renderer.outputEncoding         = THREE.sRGBEncoding;
renderer.physicallyCorrectLights = true;

// ─────────────────────────────────────────────────────────────
// SCENE
// ─────────────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);  // Pure CRED black
scene.fog        = new THREE.FogExp2(0x070505, 0.028);

// ─────────────────────────────────────────────────────────────
// CAMERA — Cinematic 35mm look
// ─────────────────────────────────────────────────────────────
const camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 100);

// CRED-style: centered, slightly low, car floats in darkness
camera.position.set(0, 1.0, 4.5);
camera.lookAt(0, 0.4, 0);

// Cinematic intro start (very close, low)
const camStart  = new THREE.Vector3(0, 0.2, 1.8);
// Final position (centered viewing angle)
const camFinal  = new THREE.Vector3(0, 1.2, 5.5);
const camTarget = new THREE.Vector3(0, 0.3, 0);

// ─────────────────────────────────────────────────────────────
// POST-PROCESSING (Bloom for cinematic glow)
// ─────────────────────────────────────────────────────────────
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(W, H),
    0.65,   // stronger bloom for CRED drama
    0.6,    // radius
    0.78    // threshold — headlights + rim glow
);
composer.addPass(bloomPass);

// ─────────────────────────────────────────────────────────────
// HDR ENVIRONMENT
// ─────────────────────────────────────────────────────────────
const pmrem = new THREE.PMREMGenerator(renderer);
pmrem.compileEquirectangularShader();

new RGBELoader()
    .setPath('https://threejs.org/examples/textures/equirectangular/')
    .load('venice_sunset_1k.hdr', tex => {
        const env = pmrem.fromEquirectangular(tex).texture;
        scene.environment = env;
        tex.dispose();
        pmrem.dispose();
    });

// ─────────────────────────────────────────────────────────────
// MIRROR REFLECTOR FLOOR
// ─────────────────────────────────────────────────────────────
const reflector = new Reflector(new THREE.PlaneGeometry(40, 40), {
    color:           new THREE.Color(0x050404),
    textureWidth:    W * renderer.getPixelRatio(),
    textureHeight:   H * renderer.getPixelRatio(),
    clipBias:        0.003,
});
reflector.rotation.x = -Math.PI / 2;
reflector.position.y = -0.001;
scene.add(reflector);

// Dark floor mat on top of reflector (blends for realism)
const floorMat = new THREE.MeshStandardMaterial({
    color:     0x090808,
    metalness: 0.7,
    roughness: 0.3,
    transparent: true,
    opacity: 0.40,
});
const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), floorMat);
floor.rotation.x = -Math.PI / 2;
floor.position.y = 0.001;
floor.receiveShadow = true;
scene.add(floor);

// Subtle edge grid (ultra-dark)
const grid = new THREE.GridHelper(30, 30, 0x0f0c0c, 0x0f0c0c);
grid.position.y = 0.002;
grid.material.opacity = 0.4;
grid.material.transparent = true;
scene.add(grid);

// ─────────────────────────────────────────────────────────────
// LOADING SCREEN
// ─────────────────────────────────────────────────────────────
const loadOverlay = document.createElement('div');
loadOverlay.id = 'car-luxury-loader';
loadOverlay.innerHTML = `
  <div style="display:flex;flex-direction:column;align-items:center;gap:24px;">
    <div style="display:flex;gap:6px;align-items:center">
      <div class="load-dot" style="animation-delay:0s"></div>
      <div class="load-dot" style="animation-delay:0.2s"></div>
      <div class="load-dot" style="animation-delay:0.4s"></div>
    </div>
    <span style="
      font-family:'Outfit',sans-serif;
      font-size:0.55rem;
      letter-spacing:0.45em;
      color:rgba(232,80,2,0.6);
      text-transform:uppercase;
    ">CALIBRATING SPECIMEN</span>
    <div style="
      width:120px;height:1px;
      background:rgba(255,255,255,0.05);
      position:relative;overflow:hidden;
      border-radius:1px;
    ">
      <div id="lux-bar" style="
        position:absolute;height:100%;
        background:linear-gradient(90deg, #e85002, #fff8f0);
        width:0%;transition:width 0.3s ease;
        box-shadow:0 0 8px #e85002;
      "></div>
    </div>
  </div>
  <style>
    .load-dot {
      width:5px;height:5px;
      border-radius:50%;
      background:rgba(232,80,2,0.7);
      animation:dotPulse 1.2s ease-in-out infinite;
    }
    @keyframes dotPulse {
      0%,100%{opacity:0.2;transform:scale(0.8)}
      50%{opacity:1;transform:scale(1.2)}
    }
  </style>
`;
loadOverlay.style.cssText = `
  position:absolute;inset:0;z-index:20;
  display:flex;align-items:center;justify-content:center;
  background:#050404;
  transition:opacity 1.2s cubic-bezier(0.16,1,0.3,1);
`;
container.appendChild(loadOverlay);

// ─────────────────────────────────────────────────────────────
// LOAD FERRARI MODEL
// ─────────────────────────────────────────────────────────────
const draco = new DRACOLoader();
draco.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');

const loader = new GLTFLoader();
loader.setDRACOLoader(draco);

let car = null;
const wheelMeshes = [];

// ── Car body paint material ──
const paintMat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(0x080706),
    metalness:          0.9,
    roughness:          0.12,
    clearcoat:          1.0,
    clearcoatRoughness: 0.04,
    reflectivity:       1.0,
    envMapIntensity:    3.0,
});

const glassMat = new THREE.MeshPhysicalMaterial({
    color:           new THREE.Color(0x0a1520),
    metalness:       0.05,
    roughness:       0.0,
    transmission:    0.9,
    thickness:       0.5,
    transparent:     true,
    opacity:         0.35,
    envMapIntensity: 2.5,
});

const chromeMat = new THREE.MeshStandardMaterial({
    color:           new THREE.Color(0x999999),
    metalness:       1.0,
    roughness:       0.02,
    envMapIntensity: 4.0,
});

const tyreMat = new THREE.MeshStandardMaterial({
    color:     new THREE.Color(0x111111),
    metalness: 0,
    roughness: 0.9,
});

const emissiveDetailMat = new THREE.MeshStandardMaterial({
    color:            new THREE.Color(0xe85002),
    emissive:         new THREE.Color(0xe85002),
    emissiveIntensity:1.5,
    metalness:        0.5,
    roughness:        0.2,
});

loader.load(
    'https://threejs.org/examples/models/gltf/ferrari.glb',
    (gltf) => {
        car = gltf.scene;

        car.traverse(child => {
            if (!child.isMesh) return;
            child.castShadow    = true;
            child.receiveShadow = true;

            const n = child.name.toLowerCase();

            if (n === 'body')           { child.material = paintMat; }
            else if (n === 'glass')     { child.material = glassMat; }
            else if (n.includes('rim')) { child.material = chromeMat; }
            else if (n.includes('tire')|| n.includes('tyre')) { child.material = tyreMat; }
            else if (n.includes('light') && !n.includes('head') && !n.includes('tail')) {
                child.material = chromeMat;
            }

            // Collect wheels for spin
            if (n.includes('wheel') || n.includes('tire') || n.includes('rim')) {
                wheelMeshes.push(child);
            }
        });

        car.scale.set(1.5, 1.5, 1.5);
        car.position.set(0, 0, 0);

        // CRED-style: face slightly right (3/4 view)
        car.rotation.y = Math.PI / 5;

        scene.add(car);

        // ── Dramatic reveal: fade loader, start camera pullback ──
        loadOverlay.style.opacity = '0';
        setTimeout(() => { loadOverlay.remove(); }, 1200);
        startRevealAnimation();
    },
    xhr => {
        if (xhr.lengthComputable) {
            const pct = (xhr.loaded / xhr.total) * 100;
            const bar = document.getElementById('lux-bar');
            if (bar) bar.style.width = pct + '%';
        }
    },
    err => {
        console.error('Model load error:', err);
        loadOverlay.style.opacity = '0';
        setTimeout(() => loadOverlay.remove(), 600);
    }
);

// ─────────────────────────────────────────────────────────────
// LIGHTING — Luxury Studio Rig
// ─────────────────────────────────────────────────────────────

// Very dark CRED ambient — let lights define the car
scene.add(new THREE.AmbientLight(0x080604, 0.4));

// ── Primary overhead KEY light (car studio) ──
const keyLight = new THREE.DirectionalLight(0xfff6ee, 3.5);
keyLight.position.set(3, 10, 5);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(4096, 4096);
keyLight.shadow.camera.near   = 0.1;
keyLight.shadow.camera.far    = 30;
keyLight.shadow.camera.left   = -6;
keyLight.shadow.camera.right  = 6;
keyLight.shadow.camera.top    = 6;
keyLight.shadow.camera.bottom = -6;
keyLight.shadow.bias = -0.0005;
scene.add(keyLight);

// ── Left cool fill (blue dusk) ──
const fillLight = new THREE.DirectionalLight(0x5577cc, 0.6);
fillLight.position.set(-8, 3, -4);
scene.add(fillLight);

// ── Copper RIM light (back) — defines car silhouette, stronger for CRED drama
const rimLight = new THREE.DirectionalLight(0xe85002, 3.5);
rimLight.position.set(-4, 2, -5);
scene.add(rimLight);

// ── Animated sweeping studio light ──
const sweepLight = new THREE.DirectionalLight(0xffd0a0, 1.2);
sweepLight.position.set(5, 4, -3);
scene.add(sweepLight);

// ── Headlight SpotLights ──
const headL = new THREE.SpotLight(0xe85002, 8, 18, Math.PI / 8, 0.35, 1.8);
headL.position.set(2.2, 0.5, 0.5);
headL.target.position.set(12, -1,  1.5);
headL.castShadow = true;
scene.add(headL, headL.target);

const headR = new THREE.SpotLight(0xe85002, 8, 18, Math.PI / 8, 0.35, 1.8);
headR.position.set(2.2, 0.5, -0.5);
headR.target.position.set(12, -1, -1.5);
scene.add(headR, headR.target);

// ── Undercar copper glow ──
const underGlow = new THREE.PointLight(0xe85002, 1.5, 4);
underGlow.position.set(0, -0.05, 0);
scene.add(underGlow);

// ── Ground uplight (adds drama) ──
const groundUp = new THREE.PointLight(0x330d0d, 2, 5);
groundUp.position.set(0, -0.2, 0);
scene.add(groundUp);

// ─────────────────────────────────────────────────────────────
// FLOATING PARTICLES (copper dust motes)
// ─────────────────────────────────────────────────────────────
const particleCount = 120;
const pGeo = new THREE.BufferGeometry();
const pPos = new Float32Array(particleCount * 3);

for (let i = 0; i < particleCount; i++) {
    pPos[i * 3 + 0] = (Math.random() - 0.5) * 16;
    pPos[i * 3 + 1] = Math.random() * 5;
    pPos[i * 3 + 2] = (Math.random() - 0.5) * 12;
}
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));

const pMat = new THREE.PointsMaterial({
    color:       0xe85002,
    size:        0.025,
    transparent: true,
    opacity:     0.55,
    sizeAttenuation: true,
});
const particles = new THREE.Points(pGeo, pMat);
scene.add(particles);

// ─────────────────────────────────────────────────────────────
// CAMERA INTRO ANIMATION (slow cinematic pullback)
// ─────────────────────────────────────────────────────────────
let revealDone = false;
let revealProgress = 0; // 0 → 1

function startRevealAnimation() {
    revealDone = false;
    revealProgress = 0;
}

function updateReveal(dt) {
    if (revealDone) return;
    revealProgress = Math.min(revealProgress + dt * 0.22, 1);

    // Ease: cubic ease-out
    const t = 1 - Math.pow(1 - revealProgress, 3);

    // Interpolate camera from close intro to final position
    camera.position.lerpVectors(
        new THREE.Vector3(1.5, 0.6, 2.5),
        camFinal,
        t
    );

    if (revealProgress >= 1) revealDone = true;
}

// ─────────────────────────────────────────────────────────────
// MOUSE PARALLAX
// ─────────────────────────────────────────────────────────────
let mouseNX = 0, mouseNY = 0;
let targetCarY = Math.PI * 0.12;
let targetCarX = 0;

document.addEventListener('mousemove', e => {
    mouseNX = (e.clientX / window.innerWidth  - 0.5) * 2;
    mouseNY = (e.clientY / window.innerHeight - 0.5) * 2;
    if (revealDone) {
        targetCarY = Math.PI * 0.12 + mouseNX * 0.5;
        targetCarX = mouseNY * 0.06;
    }
});

// ─────────────────────────────────────────────────────────────
// RENDER LOOP
// ─────────────────────────────────────────────────────────────
let lastTime  = 0;
let time      = 0;
let autoAngle = 0;
let currentCarY = Math.PI * 0.12;
let currentCarX = 0;

function render(now) {
    requestAnimationFrame(render);

    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;
    time += dt;

    // ── Camera reveal ──
    updateReveal(dt);

    // ── Car mouse parallax (smooth) ──
    if (car) {
        autoAngle += dt * 0.25;
        const baseY = revealDone ? 0 : 0;
        currentCarY += (targetCarY + autoAngle * 0.15 - currentCarY) * 0.04;
        currentCarX += (targetCarX - currentCarX) * 0.04;

        car.rotation.y = currentCarY;
        car.rotation.x = currentCarX;

        // Breathing levitation
        car.position.y = Math.sin(time * 0.7) * 0.025;
    }

    // ── Sweeping studio rim light (orbits slowly) ──
    const sweepAngle = time * 0.4;
    sweepLight.position.set(
        Math.cos(sweepAngle) * 6,
        4,
        Math.sin(sweepAngle) * 6
    );

    // ── Animated headlight pulse ──
    headL.intensity = 7 + Math.sin(time * 1.8) * 0.8;
    headR.intensity = 7 + Math.sin(time * 1.8 + 0.3) * 0.8;

    // ── Undercar glow breathe ──
    underGlow.intensity = 1.2 + Math.sin(time * 2.5) * 0.3;

    // ── Particle drift ──
    const pPositions = particles.geometry.attributes.position.array;
    for (let i = 0; i < particleCount; i++) {
        pPositions[i * 3 + 1] += dt * 0.04;
        if (pPositions[i * 3 + 1] > 5) pPositions[i * 3 + 1] = 0;
    }
    particles.geometry.attributes.position.needsUpdate = true;
    particles.rotation.y += dt * 0.02;

    // ── Camera always looks at car center ──
    camera.lookAt(camTarget);

    // ── Render through post-processing ──
    composer.render();
}

requestAnimationFrame(render);

// ─────────────────────────────────────────────────────────────
// RESIZE
// ─────────────────────────────────────────────────────────────
window.addEventListener('resize', () => {
    const W = container.clientWidth;
    const H = container.clientHeight;
    camera.aspect = W / H;
    camera.updateProjectionMatrix();
    renderer.setSize(W, H);
    composer.setSize(W, H);
    reflector.getRenderTarget().setSize(
        W * renderer.getPixelRatio(),
        H * renderer.getPixelRatio()
    );
});
