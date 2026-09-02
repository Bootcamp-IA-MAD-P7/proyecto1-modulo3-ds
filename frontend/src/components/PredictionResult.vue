<script setup>
/**
 * Issue #035 - prediction result display.
 *
 * Shows the predicted class and the stroke probability as a percentage
 * (converted only for visual display; the raw API value is never mutated).
 *
 * Uses neutral, non-medical language and always carries the disclaimer.
 */
import { computed } from 'vue'

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

const label = computed(() => (positive.value ? 'Positive' : 'Negative'))

const toneClass = computed(() =>
  positive.value ? 'result--positive' : 'result--negative',
)
</script>

<template>
  <section class="result" :class="toneClass" aria-live="polite">
    <div class="result__head">
      <div>
        <span class="result__kicker">Prediction</span>
        <span class="result__label">{{ label }}</span>
      </div>
      <div class="result__prob">
        <span class="result__kicker">Stroke probability</span>
        <span class="result__percent">{{ percent }}</span>
      </div>
    </div>

    <div class="result__bar" aria-hidden="true">
      <div
        class="result__bar-fill"
        :style="{ width: percent }"
        :class="toneClass"
      ></div>
    </div>

    <p class="result__hint">
      {{ positive ? 'The model flags this case as higher risk. Review the analysis.' : 'The model does not flag this case as elevated risk.' }}
    </p>

    <div class="result__actions">
      <button class="result__btn" type="button" @click="$emit('open-analysis')">
        Ver análisis
      </button>
    </div>

    <p class="result__disclaimer">
      This prototype is for predictive analysis and is not a medical diagnosis.
    </p>
  </section>
</template>

<style scoped>
.result {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.result__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.result__kicker {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-soft);
  margin-bottom: 4px;
}

.result__label {
  display: block;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.result__percent {
  display: block;
  font-size: 24px;
  font-weight: 700;
}

.result--negative .result__label,
.result--negative .result__percent {
  color: var(--color-positive);
}

.result--positive .result__label,
.result--positive .result__percent {
  color: var(--color-risk);
}

.result__bar {
  height: 10px;
  border-radius: 999px;
  background: var(--color-bg);
  margin: 18px 0 14px;
  overflow: hidden;
}

.result__bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease;
}

.result--negative .result__bar-fill {
  background: var(--color-positive);
}

.result--positive .result__bar-fill {
  background: var(--color-risk);
}

.result__hint {
  font-size: 14px;
  color: var(--color-text-soft);
  margin-bottom: 16px;
}

.result__actions {
  margin-bottom: 12px;
}

.result__btn {
  border: 1px solid var(--color-accent);
  background: transparent;
  color: var(--color-accent-dark);
  border-radius: 10px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
}

.result__btn:hover {
  background: var(--color-accent-soft);
}

.result__disclaimer {
  font-size: 12px;
  color: var(--color-text-soft);
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
}
</style>