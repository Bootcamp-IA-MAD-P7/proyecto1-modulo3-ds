<script setup>
/**
 * Brain3D — dynamic neural visualization component.
 *
 * Evolves the reserved "Visualización neuronal" area into a component that can
 * display a set of conceptual states, always as a VISUAL/UX representation of
 * the analysis (NEVER as a medical diagnosis or lesion localization):
 *
 *   idle       -> ready / "NEURAL SYSTEM" (default)
 *   analyzing  -> animated neural scan progress
 *   result     -> "RISK VISUALIZATION" summary
 *   zone       -> "ZONA DE INTERÉS" prepared for future Grad-CAM info
 *
 * Deliberately NO Three.js / WebGL / canvas: pure SVG + CSS animation.
 * Theme-aware (light/dark) and localized (es/en). Reusable; the existing
 * NeuralVisualization placeholder remains untouched for the dashboard.
 *
 * Props:
 *   state  : 'idle' | 'analyzing' | 'result' | 'zone'
 *   label  : optional override for the headline (e.g. derived risk level)
 *   percent: 0..100 progress (only meaningful in 'analyzing')
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const props = defineProps({
  state: {
    type: String,
    default: 'idle',
    validator: (v) => ['idle', 'analyzing', 'result', 'zone'].includes(v),
  },
  label: { type: String, default: '' },
  percent: { type: Number, default: 0 },
})

const pct = computed(() => Math.max(0, Math.min(100, Math.round(props.percent))))
</script>

<template>
  <section class="brain" aria-label="Visualización neuronal Brain3D">
    <!-- Animated neural network stage (pure SVG / CSS) -->
    <div class="brain__stage" aria-hidden="true">
      <svg viewBox="0 0 300 210" class="brain__svg">
        <g
          class="brain__links"
          :class="{ 'is-active': state === 'analyzing' || state === 'result' }"
        >
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
        <g class="brain__nodes">
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
        <g class="brain__particles">
          <circle cx="150" cy="30" r="2" />
          <circle cx="240" cy="180" r="2" />
          <circle cx="28" cy="60" r="2" />
          <circle cx="175" cy="188" r="2" />
        </g>

        <!-- Zone of interest marker (only in 'zone') -->
        <g v-if="state === 'zone'" class="brain__zone">
          <circle cx="132" cy="104" r="28" />
          <circle cx="132" cy="104" r="4" />
        </g>
      </svg>
    </div>

    <!-- State-dependent copy -->
    <template v-if="state === 'idle'">
      <h3 class="brain__title">{{ t('brain.ready') }}</h3>
      <p class="brain__text">{{ t('brain.readyHint') }}</p>
    </template>

    <template v-else-if="state === 'analyzing'">
      <h3 class="brain__title brain__title--pulse">{{ t('brain.analyzing') }}</h3>
      <p class="brain__hint">{{ t('brain.analyzingHint') }}</p>
      <div class="brain__progress" role="progressbar" :aria-valuenow="pct" aria-valuemin="0" aria-valuemax="100">
        <div class="brain__progress-bar" :style="{ width: pct + '%' }"></div>
      </div>
      <span class="brain__percent">{{ pct }}%</span>
    </template>

    <template v-else-if="state === 'result'">
      <h3 class="brain__title">{{ t('brain.riskLabel') }}</h3>
      <p v-if="label" class="brain__label">{{ label }}</p>
      <p class="brain__text">{{ t('brain.riskText') }}</p>
    </template>

    <template v-else-if="state === 'zone'">
      <h3 class="brain__title">{{ t('brain.zoneLabel') }}</h3>
      <span class="brain__chip">{{ t('imageAnalysis.zoneOfInterest') }}</span>
      <p class="brain__text">{{ t('brain.zoneText') }}</p>
      <p class="brain__subtext">{{ t('brain.zoneSubtext') }}</p>
    </template>

    <p class="brain__note">{{ t('brain.noDiagnosis') }}</p>
  </section>
</template>

<style scoped>
.brain {
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  min-height: 240px;
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

:root[data-theme='dark'] .brain {
  border: 1px dashed rgba(244, 201, 93, 0.35);
  background:
    radial-gradient(120% 120% at 50% 0%, rgba(244, 201, 93, 0.14), transparent 66%),
    linear-gradient(180deg, #101f38 0%, #071426 100%);
}

.brain__stage {
  width: 100%;
  max-width: 240px;
}

.brain__svg {
  width: 100%;
  height: auto;
}

.brain__links line {
  stroke: var(--color-accent);
  stroke-width: 1.7;
  opacity: 0.4;
  stroke-linecap: round;
}

.brain__links.is-active line {
  opacity: 0.65;
}

.brain__nodes circle {
  fill: var(--color-accent-strong);
  opacity: 0.85;
  filter: drop-shadow(0 0 5px rgba(244, 201, 93, 0.55));
  animation: pulse 2.8s ease-in-out infinite;
}

.brain__nodes circle:nth-child(2n) {
  animation-delay: 0.5s;
}

.brain__nodes circle:nth-child(3n) {
  animation-delay: 1s;
}

.brain__particles circle {
  fill: var(--color-accent);
  opacity: 0.6;
  animation: floaty 3.4s ease-in-out infinite;
}

.brain__particles circle:nth-child(2n) {
  animation-delay: 0.8s;
}

.brain__zone circle:first-child {
  fill: none;
  stroke: var(--color-risk);
  stroke-width: 2;
  stroke-dasharray: 5 4;
  animation: spin 6s linear infinite;
}

.brain__zone circle:last-child {
  fill: var(--color-risk);
  filter: drop-shadow(0 0 6px rgba(224, 163, 92, 0.8));
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>