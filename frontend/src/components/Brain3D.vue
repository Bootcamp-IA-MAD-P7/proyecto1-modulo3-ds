<script setup>
/**
 * Brain3D — interactive human brain 3D visualization (Three.js).
 *
 * Evolves the previous pure-SVG neural placeholder into a real, interactive
 * anatomical 3D human brain rendered with Three.js. It is ALWAYS a VISUAL/UX
 * representation of the analysis, NEVER a medical diagnosis or lesion
 * localization (see the permanent `noDiagnosis` footer note).
 *
 * Model asset:
 *   - File: frontend/public/models/brain.glb (glTF 2.0 binary, ~2.5 MB).
 *   - Origin: thebuggeddev/anatomy -> public/models/brain.glb
 *     (https://github.com/thebuggeddev/anatomy/blob/main/public/models/brain.glb).
 *   - Format: EXT_meshopt_compression + webp textures; loaded with GLTFLoader
 *     + MeshoptDecoder (both bundled inside the installed `three` package).
 *   - LICENSE NOTE: that repository has NO explicit license file, so the asset
 *     is under default copyright (all rights reserved). It is used here for a
 *     personal/educational prototype; confirm you have the right to redistribute
 *     before shipping. No license is being claimed/invented in this codebase.
 *
 * Features:
 *   - Anatomical, immediately recognisable human brain (hemispheres, gyri,
 *     sulci, cerebellum, brainstem) from a photoreal PBR mesh.
 *   - Soft professional lighting, medical/tech aesthetic.
 *   - OrbitControls: rotate / zoom / pan with damping.
 *   - Gentle automatic rotation that pauses while the user interacts.
 *   - Theme-aware (light/dark) via the existing store + CSS variables.
 *   - Responsive (ResizeObserver) and visibility-aware (IntersectionObserver)
 *     so the render loop is paused off-screen (low CPU/GPU).
 *   - Full resource cleanup on unmount (no memory leaks).
 *
 * Prop API (consumed by Dashboard.vue and the tests):
 *   state  : 'idle' | 'analyzing' | 'low' | 'medium' | 'high'
 *            - idle / analyzing: neutral state / the existing scan animation
 *              (no definitive risk level is shown while the request runs)
 *            - low / medium / high: VISUAL risk levels derived from the REAL
 *              probability returned by POST /predict (see src/riskLevels.js).
 *              The brain glows green / gold / red with abstract pulse lights —
 *              a visual representation of the GENERAL risk level, NEVER a
 *              lesion, tumor or localized zone (see the noDiagnosis note).
*  label  : optional override for the risk text (defaults to the i18n risk key)
 *   percent: 0..100 — analysis progress while 'analyzing', otherwise the
 *            probability expressed as a percentage (probability * 100).
 *
 * IMPORTANT: the Three.js renderer is initialised lazily and guarded for
 * WebGL support. In non-WebGL environments (e.g. the happy-dom test runner)
 * the component falls back to the plain content without crashing, which keeps
 * the existing test suite green.
 */
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { t, state as storeState } from '@/store.js'

/**
 * Brain model asset, served statically by Vite from `frontend/public/`
 * (available at runtime as `/models/brain.glb`). Using a runtime/public asset
 * (not an inline JS import) keeps the WebGL guard: in non-WebGL environments
 * (e.g. the happy-dom test runner) the loader is never invoked, so no fetch or
 * decode happens and the existing tests stay green.
 */
const BRAIN_MODEL_URL = '/models/brain.glb'

const props = defineProps({
  state: {
    type: String,
    default: 'idle',
    validator: (v) => ['idle', 'analyzing', 'low', 'medium', 'high'].includes(v),
  },
  label: { type: String, default: '' },
  percent: { type: Number, default: 0 },
})

const pct = computed(() => Math.max(0, Math.min(100, Math.round(props.percent))))

// ---------------------------------------------------------------------------
// Visual risk levels (presentation-only — see src/riskLevels.js)
// ---------------------------------------------------------------------------
// Relative zoom applied over the FIT_SIZE normalisation so the anatomical brain
// fills a bit more of its card (10-15%) without touching the layout or 50/50.
const BRAIN_ZOOM = 1.12

/** Risk colors: green (LOW), golden (MEDIUM), red (HIGH) — abstract "system" glow. */
const RISK_COLORS = { low: 0x4cd98a, medium: 0xf4c95d, high: 0xff5a5a }
/**
 * Base emissive intensity on the brain surface per level. LOW/MEDIUM are
 * deliberately brighter than before so green and golden clearly read on the
 * sulci while RED stays the most evident (high stays the strongest tint).
 */
const RISK_EMISSIVE = { low: 0.3, medium: 0.36, high: 0.4 }
/** Base intensity of the surrounding risk point lights per level. */
const RISK_LIGHT = { low: 2.2, medium: 2.9, high: 3.2 }
/**
 * Pulse rhythm per level: slower/softer breathing for LOW, faster for HIGH,
 * modulated over the (brighter) base so the glow stays calm, not flashy.
 */
const RISK_PULSE = {
  low: { freq: 0.55, depth: 0.18 },
  medium: { freq: 0.9, depth: 0.26 },
  high: { freq: 1.4, depth: 0.34 },
}

// Live risk state (module-level so the render loop can pulse it cheaply; the
// value is reset on unmount and re-applied on mount from the prop).
let currentRisk = 'idle'
let riskColor = new THREE.Color(RISK_COLORS.low)
let riskEmissiveBase = 0
let riskLightBase = 0
let riskFreq = 0
let riskDepth = 0

/** Flat list of PBR materials of the loaded brain (cached for the per-frame glow). */
const brainMaterials = []
/** Abstract lights + tiny dots distributed around the brain shell. */
const riskLights = []
const riskDots = []

/**
 * Switch the 3D risk visualization on/off. Colors are applied to the brain
 * materials immediately; intensities are animated by the render loop, so an
 * idle/analyzing state simply zeroes them (neutral, no invented level).
 */
function applyRisk(newState) {
  currentRisk = ['low', 'medium', 'high'].includes(newState) ? newState : 'idle'
  if (currentRisk === 'idle') {
    riskEmissiveBase = 0
    riskLightBase = 0
    riskFreq = 0
    riskDepth = 0
  } else {
    riskColor.set(RISK_COLORS[currentRisk])
    riskEmissiveBase = RISK_EMISSIVE[currentRisk]
    riskLightBase = RISK_LIGHT[currentRisk]
    riskFreq = RISK_PULSE[currentRisk].freq
    riskDepth = RISK_PULSE[currentRisk].depth
  }
  for (const mat of brainMaterials) {
    mat.emissive.copy(riskColor)
    if (mat.needsUpdate !== undefined) mat.needsUpdate = true
  }
  for (const light of riskLights) light.color.copy(riskColor)
  for (const dot of riskDots) dot.material.color.copy(riskColor)
}

// Follow the prop: the risk state is driven by the REAL model result
// (probability -> riskLevel -> Brain3D state), never fetched here.
watch(
  () => props.state,
  (s) => applyRisk(s),
)

/** True while a definitive visual risk level is active. */
const isRiskState = computed(() =>
  ['low', 'medium', 'high'].includes(props.state),
)

/**
 * Risk text shown beside the color. Defaults to the i18n risk label; the
 * `label` prop can override it (used by tests / future callers).
 */
const riskLabel = computed(() => {
  if (!isRiskState.value) return ''
  if (props.label) return props.label
  const key =
    props.state === 'low'
      ? 'risk.levelLow'
      : props.state === 'medium'
        ? 'risk.levelMedium'
        : 'risk.levelHigh'
  return t(key)
})

// ---------------------------------------------------------------------------
// 3D scene element (mounted in the template)
// ---------------------------------------------------------------------------
const canvasHost = ref(null)

// ---------------------------------------------------------------------------
// Theme helpers — read from the existing store; no global theme changes.
// ---------------------------------------------------------------------------
const isDark = computed(() => storeState.theme === 'dark')

function hexToRgb(hex) {
  // Accepts #rrggbb, returns {r,g,b} 0..1. Safe for the CSS vars used.
  if (!hex || typeof hex !== 'string') return { r: 1, g: 1, b: 1 }
  let h = hex.replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  const n = parseInt(h, 16)
  if (Number.isNaN(n)) return { r: 1, g: 1, b: 1 }
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }
}

// Read a CSS variable value from the document (theme-defined).
function cssVar(name) {
  if (typeof window === 'undefined') return null
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)
  return v ? v.trim() : null
}

/** Palette resolved from existing light/dark CSS variables. */
function palette() {
  const light = isDark.value ? null : true
  const accent = cssVar('--color-accent') || '#f4c95d' // golden tech accent
  const glassBg = isDark.value
    ? (cssVar('--color-card-glass') || 'rgba(16,31,56,0.82)')
    : (cssVar('--color-card-glass') || 'rgba(255,255,255,0.9)')
  return {
    isLight: light,
    accent,
    bg: glassBg,
    // Brain body tones — soft medical gray-pink, tinted toward the theme:
    bodyLight: '#c9b8b2',
    bodyDark: '#a59ea8',
    cerebellumLight: '#bdaba7',
    cerebellumDark: '#948e98',
    stemLight: '#c9bcb4',
    stemDark: '#a89fa6',
  }
}

// ---------------------------------------------------------------------------
// Anatomical brain model loading (glTF asset, meshopt-compressed)
// ---------------------------------------------------------------------------

/**
 * Normalise the loaded brain so its largest axis fits a 0..FIT_SIZE bounding
 * cube centred on the origin (same convention as the reference viewer). The
 * raw brain.glb is authored in metres and would be far too large otherwise.
 */
const FIT_SIZE = 3.8

function normalizeModel(root) {
  const box = new THREE.Box3().setFromObject(root)
  const size = new THREE.Vector3()
  box.getSize(size)
  const center = new THREE.Vector3()
  box.getCenter(center)
  const maxAxis = Math.max(size.x, size.y, size.z) || 1
  const scale = FIT_SIZE / maxAxis
  root.position.sub(center).multiplyScalar(scale)
  root.scale.multiplyScalar(scale)
}

/**
 * Apply a clean, medical finish to the loaded PBR materials for the light/dark
 * UI: keep the diffuse/normal maps (so the anatomical folds stay readable),
 * neutralise metalness and normalise the roughness.
 */
function flattenBrainFinish(root) {
  root.traverse((child) => {
    if (!child.isMesh || !child.material) return
    const mats = Array.isArray(child.material) ? child.material : [child.material]
    for (const mat of mats) {
      if (!mat) continue
      if (mat.map) mat.map.colorSpace = THREE.SRGBColorSpace
      mat.roughness = mat.roughness === undefined ? 0.5 : Math.min(0.62, Math.max(0.42, mat.roughness))
      mat.metalness = 0
      if (mat.needsUpdate !== undefined) mat.needsUpdate = true
    }
  })
}

/**
 * Load the anatomical brain model. Returns a promise that resolves once the
 * scene graph is normalised and inserted into `scene`. Errors are swallowed and
 * resolved (not rejected) so the rest of the component (text copy) still works
 * in environments where the fetch fails; the WebGL guard already prevents this
 * from being reached in the test runner.
 */
function loadBrainModel(scene) {
  return new Promise((resolve) => {
    const loader = new GLTFLoader()
    loader.setMeshoptDecoder(MeshoptDecoder)
    const onLoad = (gltf) => {
      const root = gltf.scene
      normalizeModel(root)
      flattenBrainFinish(root)
      // Presentation zoom: fills more of the card (layout untouched).
      root.scale.multiplyScalar(BRAIN_ZOOM)
      // Cache the PBR materials so the risk glow can pulse them cheaply.
      root.traverse((child) => {
        if (!child.isMesh || !child.material) return
        const mats = Array.isArray(child.material) ? child.material : [child.material]
        for (const mat of mats) {
          if (mat && !brainMaterials.includes(mat)) brainMaterials.push(mat)
        }
      })
      scene.add(root)
      // Re-apply the risk coloring now that the materials exist.
      applyRisk(props.state)
      resolve()
    }
    loader.load(
      BRAIN_MODEL_URL,
      onLoad,
      undefined,
      (err) => {
        // eslint-disable-next-line no-console
        console.warn('[Brain3D] failed to load anatomical brain model:', err)
        resolve()
      },
    )
  })
}

// ---------------------------------------------------------------------------
// Three.js scene lifecycle
// ---------------------------------------------------------------------------
let renderer = null
let scene = null
let camera = null
let controls = null
let ambientLight = null
let keyLight = null
let fillLight = null
let rimLight = null
let frameId = null
let resizeObserver = null
let visibilityObserver = null

function applyPalette() {
  if (!scene) return
  const p = palette()
  // Transparent renderer: the existing CSS gradient of .brain stays visible
  // behind the model so it integrates with the current light/dark design.
  scene.background = null

  const body = hexToRgb(p.bodyLight)
  const bodyDark = hexToRgb(p.bodyDark)
  const tone = new THREE.Color(isDark.value ? bodyDark : body)
  // Repaint the loaded brain materials toward the current theme tone, keeping
  // their normal/diffuse maps so the anatomical folds remain visible.
  scene.traverse((child) => {
    if (!child.isMesh || !child.material) return
    const mats = Array.isArray(child.material) ? child.material : [child.material]
    for (const mat of mats) {
      if (!mat) continue
      const base = new THREE.Color(mat.color || 0xffffff)
      mat.color.copy(base).lerp(tone, 0.35)
      mat.roughness = isDark.value ? 0.62 : 0.5
      mat.metalness = 0
      if (mat.needsUpdate !== undefined) mat.needsUpdate = true
    }
  })

  // Slight golden accent glow in light theme, cooler in dark.
  const accent = hexToRgb(p.accent)
  ambientLight.color.set(isDark.value ? 0x444a5a : 0x99a3b3)
  ambientLight.intensity = isDark.value ? 0.5 : 0.4
  keyLight.intensity = isDark.value ? 0.9 : 1.1
  fillLight.intensity = isDark.value ? 0.4 : 0.55
  rimLight.color.set(accent.r, accent.g, accent.b)
}

let wasVisible = false
let respectReducedMotion = false

function animate() {
  // Always keep the RAF loop so resize/re-entry works; only render when
  // the component is on-screen and the user hasn't asked for reduced motion.
  frameId = requestAnimationFrame(animate)
  if (!renderer || !scene || !camera || !controls) return
  if (!wasVisible) return

  // Risk glow pulse: LOW breathes slow and soft, MEDIUM moderate, HIGH more
  // evident — applied to the brain emissive, the shell lights and the dots.
  // Dot opacity baseline is kept HIGH so green/gold points stay clearly
  // perceptible between the sulci even at the calmest point of the wave.
  const riskOn = currentRisk === 'low' || currentRisk === 'medium' || currentRisk === 'high'
  const wave = riskOn && !respectReducedMotion
    ? Math.sin(2 * Math.PI * riskFreq * (performance.now() / 1000))
    : 0
  const ei = riskOn ? riskEmissiveBase * (1 + riskDepth * wave) : 0
  const li = riskOn ? riskLightBase * (1 + riskDepth * wave) : 0
  const di = riskOn ? 0.75 + 0.25 * wave : 0
  for (const mat of brainMaterials) {
    if (mat.emissiveIntensity !== ei) mat.emissiveIntensity = ei
  }
  for (const light of riskLights) light.intensity = li
  for (const dot of riskDots) dot.material.opacity = di

  if (respectReducedMotion) {
    // Still honor a single render so the scene isn't blank.
    controls.update()
    renderer.render(scene, camera)
    return
  }
  controls.update()
  renderer.render(scene, camera)
}

function initThree() {
  const host = canvasHost.value
  if (!host) return false

  // Guard: only init if WebGL is actually available (browser yes, happy-dom no).
  if (typeof document === 'undefined') return false
  const testCanvas = document.createElement('canvas')
  const hasWebGL = !!(typeof WebGLRenderingContext !== 'undefined' &&
    (testCanvas.getContext('webgl2') || testCanvas.getContext('webgl')))
  if (!hasWebGL) return false

  const width = host.clientWidth || 320
  const height = host.clientHeight || 240

  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
  } catch (e) {
    return false
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(width, height)
  renderer.shadowMap.enabled = false // keep it light on purpose
  host.appendChild(renderer.domElement)
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  renderer.domElement.style.display = 'block'

  scene = new THREE.Scene()

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  // The anatomical model is normalised to a FIT_SIZE (3.8) cube centred on the
  // origin, so the camera sits further back than the old procedural brain.
  camera.position.set(1.8, 0.4, 5.6)

  // Lighting — soft and professional.
  ambientLight = new THREE.AmbientLight(0x99a3b3, 0.4)
  scene.add(ambientLight)

  keyLight = new THREE.DirectionalLight(0xffffff, 1.1)
  keyLight.position.set(2, 3, 2)
  scene.add(keyLight)

  fillLight = new THREE.DirectionalLight(0xffffff, 0.55)
  fillLight.position.set(-2, 1, -1.5)
  scene.add(fillLight)

  rimLight = new THREE.DirectionalLight(0xf4c95d, 0.5)
  rimLight.position.set(-1.5, 0.5, 2.5)
  scene.add(rimLight)

  // Risk visualization lights + dots: an abstract shell distributed around the
  // brain (golden-angle spiral, biased toward the front hemisphere the camera
  // sees). They are pure "system glow" — they NEVER mark a lesion, tumor or
  // localized zone; only the TOP-LEVEL category (LOW/MEDIUM/HIGH) is conveyed.
  const RISK_SHELL_RADIUS = 2.35
  const RISK_SPOTS = 8
  for (let i = 0; i < RISK_SPOTS; i += 1) {
    const phi = Math.acos(1 - (2 * (i + 0.5)) / RISK_SPOTS)
    const theta = Math.PI * (1 + Math.sqrt(5)) * i
    const pos = new THREE.Vector3(
      RISK_SHELL_RADIUS * Math.sin(phi) * Math.cos(theta),
      RISK_SHELL_RADIUS * Math.cos(phi) * 0.75,
      RISK_SHELL_RADIUS * Math.sin(phi) * Math.sin(theta),
    )
    if (pos.z < -0.4) pos.z = -pos.z // keep them in the visible hemisphere

    const light = new THREE.PointLight(riskColor, 0, RISK_SHELL_RADIUS * 2.2, 1.6)
    light.position.copy(pos)
    scene.add(light)
    riskLights.push(light)

    const dotMat = new THREE.MeshBasicMaterial({
      color: riskColor,
      transparent: true,
      opacity: 0,
    })
    const dot = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), dotMat)
    dot.position.copy(pos)
    scene.add(dot)
    riskDots.push(dot)
  }

  // Anatomical brain model (loaded async; normalised + added to the scene).
  loadBrainModel(scene).then(() => {
    // Repaint toward the current theme once the textured model is present.
    applyPalette()
    // Risk coloring already applied in onLoad; make sure it matches the prop.
    applyRisk(props.state)
    // Center the auto-rotate target on the fitted model.
    if (controls) controls.target.set(0, 0, 0)
  })

  // Controls.
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.rotateSpeed = 0.6
  controls.enablePan = false
  controls.minDistance = 3.0
  controls.maxDistance = 10
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.9
  controls.enableZoom = true
  controls.target.set(0, 0, 0)

  applyPalette()

  // Respect users who prefer reduced motion.
  if (typeof window.matchMedia === 'function') {
    respectReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }

  // Visibility-aware rendering (pause off-screen to save CPU/GPU).
  if (typeof IntersectionObserver !== 'undefined') {
    visibilityObserver = new IntersectionObserver(
      (entries) => { wasVisible = !!entries[0]?.isIntersecting },
      { threshold: 0.05 },
    )
    visibilityObserver.observe(host)
  } else {
    wasVisible = true
  }

  // Responsive resize.
  resizeObserver = new ResizeObserver(() => resizeRenderer())
  resizeObserver.observe(host)

  // Start the loop.
  animate()
  return true
}

function resizeRenderer() {
  const host = canvasHost.value
  if (!host || !renderer || !camera) return
  const w = host.clientWidth || 0
  const h = host.clientHeight || 0
  if (!w || !h) return
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

// ---------------------------------------------------------------------------
// Lifecycle hooks
// ---------------------------------------------------------------------------
onMounted(() => {
  initThree()
  // Apply the initial risk level (neutral unless a real result is present).
  applyRisk(props.state)
  // React to theme changes (light/dark) without touching the global theme system.
  themeWatcher = watch(
    () => storeState.theme,
    () => {
      if (renderer && scene) applyPalette()
    },
  )
})

let themeWatcher = null

onBeforeUnmount(() => {
  if (themeWatcher) themeWatcher()
  themeWatcher = null

  // Reset the module-level risk state for a clean remount.
  currentRisk = 'idle'
  riskEmissiveBase = 0
  riskLightBase = 0
  riskFreq = 0
  riskDepth = 0
  brainMaterials.length = 0
  riskLights.length = 0
  riskDots.length = 0

  if (frameId) cancelAnimationFrame(frameId)
  frameId = null

  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = null

  if (visibilityObserver) visibilityObserver.disconnect()
  visibilityObserver = null

  if (controls) {
    controls.dispose()
    controls = null
  }

  // Release GPU resources.
  if (renderer) {
    renderer.dispose()
    if (renderer.domElement && renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
    renderer = null
  }

  if (scene) {
    scene.traverse((obj) => {
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) {
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material]
        mats.forEach((m) => {
          Object.values(m).forEach((v) => {
            if (v && typeof v.dispose === 'function') v.dispose()
          })
          m.dispose()
        })
      }
    })
    scene = null
  }
})
</script>

<template>
  <section class="brain" aria-label="Visualización neuronal Brain3D">
    <!-- Interactive 3D brain layer -->
    <div ref="canvasHost" class="brain__canvas" aria-hidden="true"></div>

    <!-- State-dependent copy (kept for accessibility, i18n and tests) -->
    <div class="brain__content">
      <!-- idle: neutral — no "NEURAL SYSTEM" text, no risk level, the brain
           itself is the message (only the disclaimer stays) -->

      <template v-if="state === 'analyzing'">
        <h3 class="brain__title brain__title--pulse">{{ t('brain.analyzing') }}</h3>
        <p class="brain__hint">{{ t('brain.analyzingHint') }}</p>
        <div class="brain__progress" role="progressbar" :aria-valuenow="pct" aria-valuemin="0" aria-valuemax="100">
          <div class="brain__progress-bar" :style="{ width: pct + '%' }"></div>
        </div>
        <span class="brain__percent">{{ pct }}%</span>
      </template>

      <!-- Risk states: text label ALWAYS accompanies the color (accessibility).
           LOW/MEDIUM/ELEVATED are general categories from the REAL model
           probability — never a lesion, tumor or localized zone. -->
      <template v-else-if="isRiskState">
        <span class="brain__chip" :class="`brain__chip--${state}`">{{ riskLabel }}</span>
        <span class="brain__risk-pct">{{ pct }}%</span>
      </template>

      <p class="brain__note">{{ t('brain.noDiagnosis') }}</p>
    </div>
  </section>
</template>

<style scoped>
.brain {
  position: relative;
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 16px;
  text-align: center;
  overflow: hidden;
  background:
    radial-gradient(120% 120% at 50% 0%, rgba(217, 169, 40, 0.10), transparent 66%),
    linear-gradient(180deg, #eef2f7 0%, #edf0f5 100%);
}

:root[data-theme='dark'] .brain {
  border: 1px dashed rgba(244, 201, 93, 0.35);
  background:
    radial-gradient(120% 120% at 50% 0%, rgba(244, 201, 93, 0.13), transparent 66%),
    linear-gradient(180deg, #101f38 0%, #071426 100%);
}

/* 3D canvas covers the whole zone; copy sits above it. */
.brain__canvas {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
}

.brain__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  max-width: 340px;
  pointer-events: none; /* keep canvas interactions working underneath */
}

.brain__canvas:empty {
  /* no WebGL: keep the gradient stage fully visible behind the copy */
  display: none;
}

/* ---------- copy styles (unchanged from previous version) ---------- */
.brain__progress {
  width: 100%;
  max-width: 220px;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--color-canvas-soft);
  overflow: hidden;
  margin-top: 4px;
}

.brain__progress-bar {
  height: 100%;
  border-radius: var(--radius-pill);
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent-strong));
  transition: width 0.35s var(--ease);
}

.brain__title {
  font-size: 16px;
  font-weight: var(--w-700);
  letter-spacing: -0.01em;
  color: var(--color-primary);
}

.brain__title--pulse {
  color: var(--color-accent-strong);
  animation: pulse 1.4s ease-in-out infinite;
}

.brain__label {
  font-size: 18px;
  font-weight: var(--w-700);
  color: var(--color-accent-strong);
}

.brain__text {
  font-size: 13.5px;
  font-weight: var(--w-600);
  color: var(--color-ink-mute);
}

.brain__subtext {
  font-size: 12px;
  color: var(--color-ink-faint);
  max-width: 300px;
}

.brain__hint {
  font-size: 12px;
  font-weight: var(--w-700);
  letter-spacing: 0.06em;
  color: var(--color-ink-mute);
}

.brain__chip {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border: 1px solid rgba(217, 169, 40, 0.28);
  border-radius: var(--radius-pill);
  padding: 5px 14px;
}

:root[data-theme='dark'] .brain__chip {
  color: var(--color-accent);
}

/* Risk color variants — green / gold / red, always paired with text (a11y). */
.brain__chip--low {
  color: #2fae6e;
  background: rgba(76, 217, 138, 0.12);
  border-color: rgba(76, 217, 138, 0.35);
}

.brain__chip--medium {
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border-color: rgba(217, 169, 40, 0.35);
}

.brain__chip--high {
  color: #e54444;
  background: rgba(255, 90, 90, 0.12);
  border-color: rgba(255, 90, 90, 0.38);
}

:root[data-theme='dark'] .brain__chip--low {
  color: #4cd98a;
}

:root[data-theme='dark'] .brain__chip--medium {
  color: var(--color-accent);
}

:root[data-theme='dark'] .brain__chip--high {
  color: #ff7a7a;
}

.brain__risk-pct {
  font-size: 15px;
  font-weight: var(--w-700);
  letter-spacing: 0.02em;
  color: var(--color-primary);
}

.brain__percent {
  font-size: 13px;
  font-weight: var(--w-700);
  color: var(--color-accent-strong);
}

.brain__note {
  font-size: 11.5px;
  color: var(--color-ink-faint);
  max-width: 320px;
  line-height: 1.4;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}
</style>
