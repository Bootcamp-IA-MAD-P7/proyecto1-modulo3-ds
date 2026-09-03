<script setup>
/**
 * Prediction result display (inside "2. Resultado del análisis").
 * Shows predicted class and the stroke probability as a percentage from the
 * backend (converted only for display; the raw API value is never mutated).
 * Probability is the visual protagonist (large gauge + bar).
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const props = defineProps({
  prediction: { type: Number, required: true }, // 0 | 1
  probability: { type: Number, required: true }, // 0..1 from the API
})

defineEmits(['open-analysis'])

const percent = computed(() => {
  const pct = props.probability * 100
  return `${pct.toFixed(2)}%`
})

const positive = computed(() => props.prediction === 1)

const label = computed(() => (positive.value ? t('posLabel') : t('negLabel')))

const toneClass = computed(() =>
  positive.value ? 'result--positive' : 'result--negative',
)

const gaugeColor = computed(() =>
  positive.value ? 'var(--color-warning)' : 'var(--color-accent-strong)',
)

const interpretation = computed(() =>
  positive.value ? t('posInterpretation') : t('negInterpretation'),
)

const hint = computed(() => (positive.value ? t('posHint') : t('negHint')))
</script>

<template>
  <section class="result" :class="toneClass" aria-live="polite">
    <div class="result__kicker-line">
      <span class="result__kicker">{{ t('resultKicker') }}</span>
    </div>

    <div class="result__body">
      <!-- Resultado -->
      <div class="result__col result__col--outcome">
        <span class="result__col-title">{{ t('resultado') }}</span>
        <span class="result__label">{{ label }}</span>
        <span class="result__col-hint">
          {{ hint }}
        </span>
      </div>

      <!-- Probabilidad -->
      <div class="result__col result__col--probability">
        <span class="result__col-title">{{ t('probabilidad') }}</span>
        <div class="result__gauge-wrap">
          <div class="result__gauge" :style="{ '--gauge-color': gaugeColor }" aria-hidden="true">
            <svg viewBox="0 0 120 120" class="result__gauge-svg">
              <circle cx="60" cy="60" r="52" class="result__gauge-track" />
              <circle
                cx="60"
                cy="60"
                r="52"
                class="result__gauge-fill"
                :style="{ '--p': probability }"
              />
            </svg>
            <div class="result__gauge-center">
              <span class="result__gauge-value">{{ percent }}</span>
              <span class="result__gauge-caption">{{ t('probCaption') }}</span>
            </div>
          </div>
        </div>
        <div class="result__bar" aria-hidden="true">
          <div
            class="result__bar-fill"
            :style="{ width: percent }"
            :class="toneClass"
          ></div>
        </div>
      </div>

      <!-- Interpretación -->
      <div class="result__col result__col--interpretation">
        <span class="result__col-title">{{ t('interpretacion') }}</span>
        <p class="result__hint">
          {{ interpretation }}
        </p>
        <button class="result__btn" type="button" @click="$emit('open-analysis')">
          {{ t('verAnalisis') }}
        </button>
      </div>
    </div>

    <div class="result__disclaimer">
      <p>{{ t('resultDisclaimer1') }}</p>
      <p>{{ t('resultDisclaimer2') }}</p>
    </div>
  </section>
</template>

<style scoped>
.result {
  display: flex;
  flex-direction: column;
  gap: 22px;
  background: linear-gradient(135deg, #172033 0%, #0b1424 100%);
  border: 1px solid rgba(244, 201, 93, 0.2);
  border-radius: var(--radius-lg);
  padding: 26px 28px;
  box-shadow: var(--shadow-lg);
  color: #ffffff;
}

:root[data-theme='dark'] .result {
  background: linear-gradient(135deg, #101f38 0%, #0b1a30 100%);
  border-color: rgba(244, 201, 93, 0.18);
}

.result__kicker {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent);
}

/* Horizontal 3-part body (Resultado | Probabilidad | Interpretación) */
.result__body {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1.4fr;
  gap: 28px;
  align-items: stretch;
}

.result__col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 8px;
}

.result__col + .result__col {
  border-left: 1px solid rgba(244, 201, 93, 0.16);
}

.result__col-title {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-ink-on-dark-mute);
}

.result__label {
  font-size: 30px;
  font-weight: var(--w-700);
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.result--negative .result__label {
  color: var(--color-accent);
}

.result--positive .result__label {
  color: #e0b34c;
}

.result__col-hint {
  font-size: 13px;
  color: var(--color-ink-on-dark-mute);
}

.result__gauge-wrap {
  display: flex;
  align-items: center;
}

.result__gauge {
  position: relative;
  width: 150px;
  height: 150px;
  flex-shrink: 0;
}

.result__gauge-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.result__gauge-track {
  fill: none;
  stroke: rgba(185, 194, 208, 0.2);
  stroke-width: 10;
}

.result__gauge-fill {
  fill: none;
  stroke: var(--gauge-color);
  stroke-width: 10;
  stroke-linecap: round;
  stroke-dasharray: 326.73;
  stroke-dashoffset: calc(326.73 * (1 - var(--p)));
  transition: stroke-dashoffset 0.7s var(--ease);
  filter: drop-shadow(0 0 8px rgba(244, 201, 93, 0.5));
}

.result__gauge-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 2px;
  padding: 0 8px;
}

.result__gauge-value {
  font-size: 26px;
  font-weight: var(--w-700);
  color: #ffffff;
  line-height: 1;
  letter-spacing: -0.02em;
}

.result__gauge-caption {
  font-size: 10px;
  color: var(--color-ink-on-dark-mute);
  line-height: 1.25;
  max-width: 96px;
}

.result__bar {
  height: 10px;
  border-radius: var(--radius-pill);
  background: rgba(185, 194, 208, 0.2);
  margin-top: 4px;
  overflow: hidden;
}

.result__bar-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width 0.7s var(--ease);
}

.result--negative .result__bar-fill {
  background: linear-gradient(90deg, var(--color-accent), var(--color-accent-strong));
}

.result--positive .result__bar-fill {
  background: linear-gradient(90deg, #d9a928, #e0b34c);
}

.result__hint {
  font-size: 13.5px;
  color: var(--color-ink-on-dark-mute);
  line-height: 1.55;
  margin: 0;
  flex: 1;
}

.result__btn {
  align-self: flex-start;
  border: 1px solid rgba(244, 201, 93, 0.45);
  background: rgba(244, 201, 93, 0.14);
  color: var(--color-accent);
  border-radius: var(--radius-md);
  padding: 11px 20px;
  font-size: 13.5px;
  font-weight: var(--w-600);
  transition: background var(--dur) var(--ease), transform var(--dur) var(--ease);
}

.result__btn:hover {
  background: rgba(244, 201, 93, 0.28);
  color: #ffffff;
  transform: translateY(-1px);
}

.result__disclaimer {
  display: flex;
  flex-direction: column;
  gap: 3px;
  background: rgba(244, 201, 93, 0.08);
  border: 1px solid rgba(244, 201, 93, 0.16);
  border-radius: var(--radius-md);
  padding: 12px 16px;
}

.result__disclaimer p {
  font-size: 12px;
  color: #b9c2d0;
}

@media (max-width: 900px) {
  .result__body {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .result__col + .result__col {
    border-left: none;
    border-top: 1px solid rgba(244, 201, 93, 0.16);
    padding-top: 18px;
  }
}
</style>