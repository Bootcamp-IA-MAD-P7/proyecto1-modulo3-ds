<script setup>
/**
 * "4. Factores de mayor impacto" card.
 * Presents the patient factors that were actually submitted (real data only).
 * No invented model weights or percentages: Impacto/Nivel is shown as a neutral
 * "Registrado" indicator, never a fabricated ranking.
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const props = defineProps({
  factors: { type: Object, default: () => ({}) },
})

const displayOrder = [
  'age',
  'gender',
  'hypertension',
  'heart_disease',
  'ever_married',
  'work_type',
  'Residence_type',
  'avg_glucose_level',
  'bmi',
  'smoking_status',
]

const labelKeys = {
  age: 'fAge',
  gender: 'fGender',
  hypertension: 'fHypertension',
  heart_disease: 'fHeartDisease',
  ever_married: 'fEverMarried',
  work_type: 'fWorkType',
  Residence_type: 'fResidence',
  avg_glucose_level: 'fGlucose',
  bmi: 'fBmi',
  smoking_status: 'fSmoking',
}

const rows = computed(() =>
  displayOrder
    .filter((key) => key in props.factors)
    .map((key) => ({
      key,
      label: labelKeys[key] ? t(labelKeys[key]) : key,
      value: props.factors[key],
    })),
)
</script>

<template>
  <section class="factors" aria-label="Factores de mayor impacto">
    <div class="card-head">
      <span class="card-head__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M4 9h16M4 15h16M4 6h10M4 18h10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
      </span>
      <div class="card-head__text">
        <span class="factors__kicker">{{ t('impactEyebrow') }}</span>
        <h2 class="card-head__title">{{ t('impactTitle') }}</h2>
        <p class="card-head__subtitle">
          {{ t('impactSubtitle') }}
        </p>
      </div>
    </div>

    <div v-if="rows.length" class="factors__table">
      <div class="factors__row factors__row--head">
        <span class="factors__cell">{{ t('factorLabel') }}</span>
        <span class="factors__cell">{{ t('valueLabel') }}</span>
        <span class="factors__cell">{{ t('levelLabel') }}</span>
      </div>
      <div v-for="row in rows" :key="row.key" class="factors__row">
        <span class="factors__cell factors__cell--label">{{ row.label }}</span>
        <span class="factors__cell">{{ row.value }}</span>
        <span class="factors__cell">
          <span class="factors__chip">{{ t('registered') }}</span>
        </span>
      </div>
    </div>
    <p v-else class="factors__empty">{{ t('impactEmpty') }}</p>
  </section>
</template>

<style scoped>
.factors {
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xl);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  min-height: 200px;
}

.factors__kicker {
  font-size: 10.5px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent-strong);
}

.factors__table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.factors__row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 0.9fr;
  gap: 12px;
  align-items: center;
  padding: 11px 16px;
  font-size: 13.5px;
}

.factors__row + .factors__row {
  border-top: 1px solid var(--color-hairline);
}

.factors__row--head {
  background: var(--color-canvas-soft);
}

.factors__row--head .factors__cell {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-faint);
}

.factors__cell {
  color: var(--color-ink-mute);
  min-width: 0;
  overflow-wrap: anywhere;
}

.factors__cell--label {
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.factors__chip {
  display: inline-block;
  font-size: 11.5px;
  font-weight: var(--w-600);
  color: var(--color-ink);
  background: var(--color-active-bg);
  border: 1px solid var(--color-active-border);
  border-radius: var(--radius-pill);
  padding: 3px 12px;
  white-space: nowrap;
}

.factors__empty {
  font-size: 13px;
  color: var(--color-ink-mute);
}

@media (max-width: 640px) {
  .factors__row {
    grid-template-columns: 1fr 1fr;
  }
  .factors__cell:nth-child(3) {
    grid-column: span 2;
  }
}
</style>