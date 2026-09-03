<script setup>
/**
 * Login view (UI only, standalone — no AppLayout).
 * Duolingo-inspired warmth but own identity: a brain made of nodes/lines that
 * appears progressively with a light wave. Animation is CSS/SVG only and pauses
 * under prefers-reduced-motion. "Entrar" simulates navigation to the dashboard.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')
const submitting = ref(false)

function submit() {
  if (submitting.value) return
  submitting.value = true
  // UI only: simulate a brief submission then navigate home.
  window.setTimeout(() => {
    router.push('/')
  }, 550)
}
</script>

<template>
  <div class="login">
    <!-- Left: animated brain-of-nodes on deep navy/violet -->
    <aside class="login__hero">
      <div class="login__hero-top">
        <span class="login__brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path
              d="M12 21c3-2.5 6-4.6 6-8a6 6 0 1 0-12 0c0 3.4 3 5.5 6 8Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <circle cx="12" cy="10" r="2.1" fill="none" stroke="currentColor" stroke-width="1.7" />
          </svg>
        </span>
        <span class="login__brand">F5 RISKAI</span>
      </div>

      <div class="login__brain" aria-hidden="true">
        <svg viewBox="0 0 360 260" class="login__brain-svg">
          <!-- light wave gradient -->
          <defs>
            <linearGradient id="wave" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="rgba(124,92,224,0.9)" />
              <stop offset="100%" stop-color="rgba(21,85,85,0.9)" />
            </linearGradient>
          </defs>

          <!-- links -->
          <g class="brain__links">
            <line x1="150" y1="70" x2="78" y2="140" />
            <line x1="150" y1="70" x2="210" y2="120" />
            <line x1="150" y1="70" x2="120" y2="170" />
            <line x1="78" y1="140" x2="40" y2="200" />
            <line x1="78" y1="140" x2="120" y2="170" />
            <line x1="210" y1="120" x2="300" y2="70" />
            <line x1="210" y1="120" x2="270" y2="190" />
            <line x1="210" y1="120" x2="120" y2="170" />
            <line x1="120" y1="170" x2="60" y2="225" />
            <line x1="120" y1="170" x2="200" y2="215" />
            <line x1="270" y1="190" x2="200" y2="215" />
            <line x1="300" y1="70" x2="330" y2="130" />
            <line x1="270" y1="190" x2="330" y2="130" />
          </g>

          <!-- nodes appear progressively with a light wave -->
          <g class="brain__nodes">
            <circle cx="150" cy="70" r="11" />
            <circle cx="78" cy="140" r="8" />
            <circle cx="210" cy="120" r="9" />
            <circle cx="120" cy="170" r="7" />
            <circle cx="300" cy="70" r="8" />
            <circle cx="270" cy="190" r="7" />
            <circle cx="40" cy="200" r="6" />
            <circle cx="60" cy="225" r="5.5" />
            <circle cx="200" cy="215" r="6" />
            <circle cx="330" cy="130" r="6" />
          </g>

          <!-- light wave -->
          <g class="brain__wave">
            <circle cx="150" cy="70" r="18" />
            <circle cx="150" cy="70" r="30" />
            <circle cx="150" cy="70" r="44" />
          </g>
        </svg>
      </div>

      <div class="login__hero-copy">
        <h1 class="login__headline">Inteligencia que protege vidas</h1>
        <p class="login__tagline">
          Estima el riesgo de ictus con apoyo de machine learning para decisiones
          más informadas.
        </p>
      </div>
    </aside>

    <!-- Right: login card -->
    <main class="login__panel">
      <div class="login__card">
        <h2 class="login__title">Bienvenido de nuevo</h2>
        <p class="login__subtitle">Inicia sesión para continuar.</p>

        <form class="login__form" @submit.prevent="submit">
          <label class="login__field">
            <span class="login__label">Correo electrónico</span>
            <input
              v-model="email"
              class="login__input"
              type="email"
              placeholder="usuario@ejemplo.com"
            />
          </label>

          <label class="login__field">
            <span class="login__label">Contraseña</span>
            <input
              v-model="password"
              class="login__input"
              type="password"
              placeholder="••••••••"
            />
          </label>

          <button class="login__cta" type="submit" :disabled="submitting">
            <span class="login__cta-text">{{ submitting ? 'Entrando…' : 'Entrar' }}</span>
            <span class="login__cta-arrow" aria-hidden="true">→</span>
          </button>
        </form>

        <p class="login__footnote">
          Acceso de demostración — no se requieren credenciales reales.
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  min-height: 100vh;
}

/* LEFT HERO (deep navy/violet) */
.login__hero {
  background:
    radial-gradient(120% 90% at 20% 0%, #3f3a52 0%, #232042 45%, #0e0c1f 100%);
  color: #fff;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  position: relative;
}

.login__hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(60% 50% at 85% 90%, rgba(21, 85, 85, 0.4) 0%, transparent 60%);
  pointer-events: none;
}

.login__hero-top {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.login__brand-mark {
  width: 38px;
  height: 38px;
  color: var(--color-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.login__brand-mark svg {
  width: 34px;
  height: 34px;
}

.login__brand {
  font-size: 16px;
  font-weight: var(--w-700);
  letter-spacing: 0.14em;
  color: var(--color-on-dark-mute);
}

.login__brain {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  margin: 20px 0;
}

.login__brain-svg {
  width: 100%;
  max-width: 380px;
  height: auto;
}

.login__hero-copy {
  position: relative;
  z-index: 1;
}

.login__headline {
  font-size: var(--fs-h2);
  color: #fff;
  max-width: 440px;
  line-height: 1.15;
}

.login__tagline {
  font-size: 15px;
  color: var(--color-on-dark-mute);
  max-width: 420px;
  margin-top: 12px;
  line-height: 1.5;
}

/* brain node/link styling */
.brain__links line {
  stroke: rgba(201, 180, 250, 0.35);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-dasharray: 10 120;
  stroke-dashoffset: 0;
  animation: draw 2.6s ease forwards infinite;
}

.brain__nodes circle {
  fill: var(--color-accent);
  animation: appear 1.6s ease forwards infinite;
}

.brain__wave circle {
  fill: none;
  stroke: url(#wave);
  stroke-width: 2;
  opacity: 0;
  stroke-linecap: round;
  animation: ripple 2.8s ease-out infinite;
  transform-origin: center;
}

.brain__nodes circle:nth-child(1) { animation-delay: 0.05s; }
.brain__nodes circle:nth-child(2) { animation-delay: 0.25s; }
.brain__nodes circle:nth-child(3) { animation-delay: 0.4s; }
.brain__nodes circle:nth-child(4) { animation-delay: 0.55s; }
.brain__nodes circle:nth-child(5) { animation-delay: 0.7s; }
.brain__nodes circle:nth-child(6) { animation-delay: 0.85s; }
.brain__nodes circle:nth-child(7) { animation-delay: 1s; }
.brain__nodes circle:nth-child(8) { animation-delay: 1.15s; }
.brain__nodes circle:nth-child(9) { animation-delay: 1.3s; }
.brain__nodes circle:nth-child(10) { animation-delay: 1.45s; }

.brain__links line:nth-child(1) { animation-delay: 0.1s; }
.brain__links line:nth-child(2) { animation-delay: 0.3s; }
.brain__links line:nth-child(3) { animation-delay: 0.5s; }
.brain__links line:nth-child(4) { animation-delay: 0.7s; }
.brain__links line:nth-child(5) { animation-delay: 0.9s; }
.brain__links line:nth-child(6) { animation-delay: 1.1s; }
.brain__links line:nth-child(7) { animation-delay: 1.3s; }
.brain__links line:nth-child(8) { animation-delay: 1.5s; }
.brain__links line:nth-child(9) { animation-delay: 1.7s; }
.brain__links line:nth-child(10) { animation-delay: 1.9s; }
.brain__links line:nth-child(11) { animation-delay: 2.1s; }
.brain__links line:nth-child(12) { animation-delay: 2.3s; }
.brain__links line:nth-child(13) { animation-delay: 2.5s; }

@keyframes draw {
  0% {
    stroke-dashoffset: 130;
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 0.5;
  }
}

@keyframes appear {
  0%,
  15% {
    opacity: 0;
    transform: scale(0.4);
  }
  45%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes ripple {
  0% {
    opacity: 0.7;
    transform: scale(0.6);
  }
  100% {
    opacity: 0;
    transform: scale(1.6);
  }
}

/* RIGHT PANEL */
.login__panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--color-canvas);
}

.login__card {
  width: 100%;
  max-width: 400px;
}

.login__title {
  font-size: var(--fs-h3);
  color: var(--color-primary);
}

.login__subtitle {
  margin-top: 6px;
  color: var(--color-ink-mute);
  font-size: 14px;
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 26px;
}

.login__field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.login__label {
  font-size: 12.5px;
  font-weight: var(--w-600);
  color: var(--color-ink);
}

.login__input {
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 13px 15px;
  font-size: 14px;
  background: var(--color-canvas);
  color: var(--color-ink);
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}

.login__input:focus {
  outline: none;
  border-color: var(--color-accent-strong);
  box-shadow: 0 0 0 3px rgba(124, 92, 224, 0.14);
}

.login__cta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: none;
  background: var(--color-primary);
  color: var(--color-on-accent);
  border-radius: var(--radius-md);
  padding: 15px 18px;
  font-size: 15px;
  font-weight: var(--w-600);
  box-shadow: var(--shadow-sm);
  transition: background var(--dur) var(--ease), transform var(--dur) var(--ease);
}

.login__cta:hover:not(:disabled) {
  background: var(--color-primary-deep);
  transform: translateY(-1px);
}

.login__cta:disabled {
  opacity: 0.7;
  cursor: default;
}

.login__cta-arrow {
  font-size: 18px;
  line-height: 1;
}

.login__footnote {
  margin-top: 22px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
  text-align: center;
}

/* REDUCED MOTION: disable all brain animation */
@media (prefers-reduced-motion: reduce) {
  .brain__links line,
  .brain__nodes circle,
  .brain__wave circle {
    animation: none !important;
    opacity: 1 !important;
  }
}

@media (max-width: 860px) {
  .login {
    grid-template-columns: 1fr;
  }
  .login__hero {
    padding: 32px;
  }
  .login__brain {
    margin: 12px 0;
  }
  .login__panel {
    padding: 32px;
  }
}
</style>