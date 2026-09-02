<script setup>
/**
 * Issue #036 - risk analysis modal.
 *
 * Shows an expanded, non-medical explanation of the prediction. It deliberately
 * does NOT claim causality: it only describes what "the model gave more weight
 * to" based on the input factors, which is safe, user-facing language.
 */
import { computed } from 'vue'

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
  positive.value
    ? 'Riesgo elevado según el modelo'
    : 'Riesgo no elevado según el modelo',
)

const explanation = computed(() =>
  positive.value
    ? 'El modelo baseline ha dado un mayor peso a los factores de este caso, indicando una asociación importante entre ellos y el riesgo de ictus en los datos de entrenamiento.'
    : 'El modelo baseline no detecta una asociación importante que eleve el riesgo en este caso, según los datos de entrenamiento.',
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
          <h2 id="risk-modal-title" class="modal-panel__title">{{ headline }}</h2>
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
          <div class="modal-panel__fact">
            <span class="modal-panel__kicker">Stroke probability</span>
            <span class="modal-panel__value" :class="{ 'is-positive': positive }">
              {{ percent }}
            </span>
          </div>

          <p class="modal-panel__explanation">{{ explanation }}</p>

          <div class="modal-panel__factors">
            <h3 class="modal-panel__subtitle">Factores relevantes introducidos</h3>
            <ul class="modal-panel__list" v-if="relevantFactors.length">
              <li v-for="item in relevantFactors" :key="item.key" class="modal-panel__row">
                <span class="modal-panel__row-label">{{ item.label }}</span>
                <span class="modal-panel__row-value">{{ item.value }}</span>
              </li>
            </ul>
            <p v-else class="modal-panel__empty">No hay factores disponibles.</p>
          </div>

          <p class="modal-panel__disclaimer">
            El modelo ha dado mayor peso a estas variables dentro del modelo
            baseline. Esta herramienta es solo análisis predictivo y no
            constituye un diagnóstico médico.
          </p>
        </div>

        <div class="modal-panel__foot">
          <button class="modal-panel__close-btn" type="button" @click="handleClose">
            Cerrar
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
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}

.modal-panel {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-md);
}

.modal-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 12px;
  border-bottom: 1px solid var(--color-border);
}

.modal-panel__title {
  font-size: 17px;
}

.modal-panel__close {
  border: none;
  background: var(--color-bg);
  border-radius: 8px;
  width: 32px;
  height: 32px;
  font-size: 22px;
  line-height: 1;
  color: var(--color-text-soft);
}

.modal-panel__close:hover {
  background: var(--color-border);
}

.modal-panel__body {
  padding: 18px 20px;
}

.modal-panel__fact {
  margin-bottom: 14px;
}

.modal-panel__kicker {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-soft);
  margin-bottom: 4px;
}

.modal-panel__value {
  font-size: 26px;
  font-weight: 700;
}

.modal-panel__value.is-positive {
  color: var(--color-risk);
}

.modal-panel__explanation {
  font-size: 14px;
  color: var(--color-text);
  margin-bottom: 18px;
}

.modal-panel__subtitle {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.modal-panel__list {
  list-style: none;
  margin: 0 0 16px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.modal-panel__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  font-size: 14px;
}

.modal-panel__row + .modal-panel__row {
  border-top: 1px solid var(--color-border);
}

.modal-panel__row-label {
  color: var(--color-text-soft);
}

.modal-panel__row-value {
  font-weight: 600;
}

.modal-panel__empty {
  font-size: 14px;
  color: var(--color-text-soft);
  margin-bottom: 16px;
}

.modal-panel__disclaimer {
  font-size: 12px;
  color: var(--color-text-soft);
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
}

.modal-panel__foot {
  padding: 12px 20px 16px;
  border-top: 1px solid var(--color-border);
}

.modal-panel__close-btn {
  width: 100%;
  border: none;
  background: var(--color-accent);
  color: #fff;
  border-radius: 10px;
  padding: 11px;
  font-size: 15px;
  font-weight: 600;
}

.modal-panel__close-btn:hover {
  background: var(--color-accent-dark);
}
</style>