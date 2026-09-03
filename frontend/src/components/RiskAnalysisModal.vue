<script setup>
/**
 * Issue #036 - risk analysis modal.
 *
 * Shows an expanded, non-medical explanation of the prediction. It deliberately
 * does NOT claim causality: it only describes what "the model gave more weight
 * to" based on the input factors, which is safe, user-facing language.
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const emit = defineEmits(['close'])

const props = defineProps({
  open: { type: Boolean, default: false },
  prediction: { type: Number, default: 0 },
  probability: { type: Number, default: 0 },
  factors: { type: Object, default: () => ({}) }, // labeled patient inputs
})

defineOptions({ inheritAttrs: false })

const percent = computed(() => `${(props.probability * 100).toFixed(2)}%`)
const positive = computed(() => props.prediction === 1)

const headline = computed(() =>
  positive.value ? t('modalPosHeadline') : t('modalNegHeadline'),
)

const explanation = computed(() =>
  positive.value ? t('modalPosExplanation') : t('modalNegExplanation'),
)

const badge = computed(() =>
  positive.value ? t('modalPosBadge') : t('modalNegBadge'),
)

/**
 * Factors the model showed the strongest association with in Issue #021.
 * These are the top coefficients by absolute value (non-causal framing).
 */
const strongestFactors = ['age', 'work_type', 'hypertension', 'avg_glucose_level', 'bmi']

const relevantFactors = computed(() => {
  return strongestFactors
    .filter((key) => key in props.factors)
    .map((key) => ({ key, label: key, value: props.factors[key] }))
})

function onBackdropClick(event) {
  // Only close when clicking the backdrop itself, not the panel (mobile-safe).
  if (event.target === event.currentTarget) {
    handleClose()
  }
}

function handleClose() {
  document.body.style.overflow = ''
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="modal-backdrop"
      data-testid="modal-backdrop"
      @click="onBackdropClick"
    >
      <div
        class="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="risk-modal-title"
        data-testid="risk-modal"
      >
        <div class="modal-panel__head">
          <div class="modal-panel__heading">
            <span class="modal-panel__eyebrow">{{ t('modalEyebrow') }}</span>
            <h2 id="risk-modal-title" class="modal-panel__title">{{ headline }}</h2>
          </div>
          <button
            class="modal-panel__close"
            type="button"
            aria-label="Close analysis"
            @click="handleClose"
          >
            &times;
          </button>
        </div>

        <div class="modal-panel__body">
          <div class="modal-panel__fact" :class="{ 'is-positive': positive }">
            <span class="modal-panel__kicker">{{ t('modalStrokeProb') }}</span>
            <span class="modal-panel__value">
              {{ percent }}
            </span>
            <span class="modal-panel__badge" :class="{ 'is-positive': positive }">
              {{ badge }}
            </span>
          </div>

          <p class="modal-panel__explanation">{{ explanation }}</p>

          <div class="modal-panel__factors">
            <h3 class="modal-panel__subtitle">{{ t('modalFactors') }}</h3>
            <ul class="modal-panel__list" v-if="relevantFactors.length">
              <li v-for="item in relevantFactors" :key="item.key" class="modal-panel__row">
                <span class="modal-panel__row-label">{{ item.label }}</span>
                <span class="modal-panel__row-value">{{ item.value }}</span>
              </li>
            </ul>
            <p v-else class="modal-panel__empty">{{ t('modalNoFactors') }}</p>
          </div>

          <p class="modal-panel__disclaimer">
            {{ t('modalDisclaimer') }}
          </p>
        </div>

        <div class="modal-panel__foot">
          <button class="modal-panel__close-btn" type="button" @click="handleClose">
            {{ t('modalClose') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(7, 20, 38, 0.55);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
  animation: fadeBackdrop 0.18s var(--ease);
}

.modal-panel {
  background: var(--color-card);
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.28s var(--ease);
}

.modal-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 22px 14px;
  border-bottom: var(--color-hairline);
}

.modal-panel__heading {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.modal-panel__eyebrow {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent-strong);
}

.modal-panel__title {
  font-size: 17px;
  letter-spacing: -0.01em;
  color: var(--color-primary);
}

.modal-panel__close {
  border: none;
  background: var(--color-canvas-soft);
  border-radius: var(--radius-sm);
  width: 32px;
  height: 32px;
  font-size: 22px;
  line-height: 1;
  color: var(--color-ink-mute);
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}

.modal-panel__close:hover {
  background: var(--color-hover-bg);
  color: var(--color-primary);
}

.modal-panel__body {
  padding: 18px 22px;
}

.modal-panel__fact {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 16px;
  background: var(--color-canvas-soft);
  border: var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 14px 16px;
}

.modal-panel__kicker {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-ink-mute);
}

.modal-panel__value {
  font-size: 28px;
  font-weight: var(--w-700);
  color: var(--color-accent-strong);
  line-height: 1.1;
}

.modal-panel__fact.is-positive .modal-panel__value {
  color: #b45309;
}

.modal-panel__badge {
  align-self: flex-start;
  font-size: 11px;
  font-weight: var(--w-600);
  border-radius: var(--radius-pill);
  padding: 3px 11px;
  background: rgba(217, 169, 40, 0.14);
  color: var(--color-accent-strong);
}

.modal-panel__badge.is-positive {
  background: rgba(180, 83, 9, 0.12);
  color: #b45309;
}

.modal-panel__explanation {
  font-size: 14px;
  color: var(--color-ink);
  margin-bottom: 18px;
}

.modal-panel__subtitle {
  font-size: 14px;
  font-weight: var(--w-600);
  margin-bottom: 12px;
  color: var(--color-primary);
}

.modal-panel__list {
  list-style: none;
  margin: 0 0 16px;
  padding: 0;
  border: var(--color-hairline);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.modal-panel__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  font-size: 14px;
}

.modal-panel__row + .modal-panel__row {
  border-top: var(--color-hairline);
}

.modal-panel__row-label {
  color: var(--color-ink-mute);
}

.modal-panel__row-value {
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.modal-panel__empty {
  font-size: 14px;
  color: var(--color-ink-mute);
  margin-bottom: 16px;
}

.modal-panel__disclaimer {
  font-size: 12px;
  color: var(--color-ink-mute);
  border-top: var(--color-hairline);
  padding-top: 12px;
}

.modal-panel__foot {
  padding: 12px 22px 18px;
  border-top: var(--color-hairline);
}

.modal-panel__close-btn {
  width: 100%;
  border: none;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  padding: 12px;
  font-size: 15px;
  font-weight: var(--w-600);
  box-shadow: var(--shadow-sm);
  transition: background var(--dur) var(--ease);
}

.modal-panel__close-btn:hover {
  background: var(--color-primary-deep);
}

@keyframes fadeBackdrop {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>