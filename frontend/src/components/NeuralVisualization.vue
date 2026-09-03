<script setup>
/**
 * Neural visualization placeholder.
 * A reserved "Visualización neuronal" area for a future Brain3D.
 * Deliberately NO real 3D model / no Three.js / no WebGL / no canvas.
 * Abstract nodes/lines/particles are pure SVG/CSS, ready to be swapped.
 * Theme-aware (light/dark) and localized (es/en).
 */
import { t } from '@/store.js'
</script>

<template>
  <section class="neural" aria-label="Visualización neuronal placeholder">
    <div class="neural__stage" aria-hidden="true">
      <svg viewBox="0 0 300 210" class="neural__svg">
        <g class="neural__links">
          <line x1="80" y1="54" x2="40" y2="116" />
          <line x1="80" y1="54" x2="132" y2="104" />
          <line x1="80" y1="54" x2="92" y2="146" />
          <line x1="132" y1="104" x2="212" y2="64" />
          <line x1="132" y1="104" x2="192" y2="154" />
          <line x1="132" y1="104" x2="62" y2="166" />
          <line x1="40" y1="116" x2="22" y2="176" />
          <line x1="212" y1="64" x2="252" y2="124" />
          <line x1="192" y1="154" x2="252" y2="124" />
          <line x1="92" y1="146" x2="62" y2="166" />
        </g>
        <g class="neural__nodes">
          <circle cx="80" cy="54" r="10" />
          <circle cx="40" cy="116" r="7" />
          <circle cx="132" cy="104" r="8" />
          <circle cx="92" cy="146" r="5.5" />
          <circle cx="212" cy="64" r="7" />
          <circle cx="192" cy="154" r="4.5" />
          <circle cx="62" cy="166" r="4" />
          <circle cx="22" cy="176" r="3.5" />
          <circle cx="252" cy="124" r="5" />
        </g>
        <g class="neural__particles">
          <circle cx="150" cy="30" r="2" />
          <circle cx="240" cy="180" r="2" />
          <circle cx="28" cy="60" r="2" />
          <circle cx="175" cy="188" r="2" />
        </g>
      </svg>
    </div>

    <h3 class="neural__title">{{ t('brainTitle') }}</h3>
    <p class="neural__text">{{ t('brainReserved') }}</p>
    <span class="neural__chip">{{ t('integrationChip') }}</span>
    <p class="neural__hint">{{ t('neuralHint') }}</p>

    <span class="visually-hidden">Neural Visualization</span>
  </section>
</template>

<style scoped>
.neural {
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  min-height: 210px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 18px 16px;
  text-align: center;
  overflow: hidden;
  background:
    radial-gradient(120% 120% at 50% 0%, rgba(217, 169, 40, 0.12), transparent 66%),
    linear-gradient(180deg, #eef2f7 0%, #edf0f5 100%);
}

:root[data-theme='dark'] .neural {
  border: 1px dashed rgba(244, 201, 93, 0.35);
  background:
    radial-gradient(120% 120% at 50% 0%, rgba(244, 201, 93, 0.14), transparent 66%),
    linear-gradient(180deg, #101f38 0%, #071426 100%);
}

.neural__stage {
  width: 100%;
  max-width: 220px;
}

.neural__svg {
  width: 100%;
  height: auto;
}

.neural__links line {
  stroke: var(--color-accent);
  stroke-width: 1.7;
  opacity: 0.4;
  stroke-linecap: round;
}

.neural__nodes circle {
  fill: var(--color-accent-strong);
  opacity: 0.85;
  filter: drop-shadow(0 0 5px rgba(244, 201, 93, 0.55));
  animation: pulse 2.8s ease-in-out infinite;
}

.neural__nodes circle:nth-child(2n) {
  animation-delay: 0.5s;
}

.neural__nodes circle:nth-child(3n) {
  animation-delay: 1s;
}

.neural__particles circle {
  fill: var(--color-accent);
  opacity: 0.6;
  animation: floaty 3.4s ease-in-out infinite;
}

.neural__particles circle:nth-child(2n) {
  animation-delay: 0.8s;
}

.neural__title {
  font-size: 16px;
  font-weight: var(--w-700);
  letter-spacing: -0.01em;
  color: var(--color-primary);
}

.neural__text {
  font-size: 13.5px;
  font-weight: var(--w-600);
  color: var(--color-ink-mute);
}

.neural__chip {
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

:root[data-theme='dark'] .neural__chip {
  color: var(--color-accent);
}

.neural__hint {
  font-size: 12px;
  color: var(--color-ink-faint);
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

@keyframes floaty {
  0%,
  100% {
    opacity: 0.4;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-4px);
  }
}
</style>