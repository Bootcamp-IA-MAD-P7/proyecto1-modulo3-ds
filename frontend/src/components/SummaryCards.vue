<script setup>
/**
 * Bottom summary row cards inspired by the reference.
 *
 * Real data, straight from the persistence layer:
 *   - PACIENTES ANALIZADOS  -> GET /patients (distinct patients count)
 *   - RIESGO PROMEDIO       -> GET /assessments (mean of stored probability)
 *   - MODELO                -> the model actually connected (Logistic Regression)
 *   - ESTADO DEL SISTEMA    -> GET /health (existing liveness check)
 *
 * States: LOADING (discreet '…') / SUCCESS / EMPTY / ERROR (brief, professional
 * message — the dashboard never breaks). Incrementing the `refreshKey` prop
 * (e.g. after a persisted assessment) refetches the statistics without a page
 * reload. Only real API data is ever shown; no invented numbers.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { t } from '@/store.js'
import {
  checkHealth,
  listAssessments,
  listPatients,
} from '@/services/predictionService.js'

const props = defineProps({
  /** Increment to force a statistics refresh (e.g. after a new persisted assessment). */
  refreshKey: { type: Number, default: 0 },
})

const loading = ref(true)
const pacientesError = ref(false)
const riesgoError = ref(false)
const patientsCount = ref(0)
/** Mean of the stored assessment probabilities in 0..1, or null when none. */
const averageRisk = ref(null)
const systemOnline = ref(true)

async function loadStats() {
  loading.value = true
  pacientesError.value = false
  riesgoError.value = false

  // Independent parallel checks: statistics depend on the storage endpoints,
  // the system card on the existing /health liveness probe.
  const [patientsRes, assessmentsRes, healthRes] = await Promise.allSettled([
    listPatients(),
    listAssessments(),
    checkHealth(),
  ])

  if (patientsRes.status === 'fulfilled' && Array.isArray(patientsRes.value)) {
    patientsCount.value = patientsRes.value.length
  } else {
    pacientesError.value = true
  }

  if (assessmentsRes.status === 'fulfilled' && Array.isArray(assessmentsRes.value)) {
    // Guarded mapping: `Number(null)` is 0 (not NaN), so null/undefined must be
    // excluded explicitly — otherwise a missing probability would skew the mean.
    const probabilities = assessmentsRes.value
      .map((a) => (a && a.probability != null ? Number(a.probability) : NaN))
      .filter((p) => Number.isFinite(p) && p >= 0 && p <= 1)
    averageRisk.value = probabilities.length
      ? probabilities.reduce((sum, p) => sum + p, 0) / probabilities.length
      : null
  } else {
    riesgoError.value = true
  }

  systemOnline.value = healthRes.status === 'fulfilled' && healthRes.value === true
  loading.value = false
}

onMounted(loadStats)
watch(() => props.refreshKey, loadStats)

const cards = computed(() => {
  const pacientes = loading.value
    ? { value: '…', hint: '' }
    : pacientesError.value
      ? { value: '—', hint: t('cardsError') }
      : {
          value: String(patientsCount.value),
          hint:
            patientsCount.value > 0
              ? t('cardsPacientesReal')
              : t('cardsPacientesEmpty'),
        }

  const riesgo = loading.value
    ? { value: '…', hint: '' }
    : riesgoError.value
      ? { value: '—', hint: t('cardsError') }
      : averageRisk.value === null
        ? { value: '—', hint: t('cardsRiesgoEmpty') }
        : {
            value: `${(averageRisk.value * 100).toFixed(1)}%`,
            hint: t('cardsRiesgoReal'),
          }

  const sistema = loading.value
    ? { value: '…', hint: '' }
    : {
        value: systemOnline.value ? t('enLinea') : t('cardsSistemaOffline'),
        hint: '',
        tone: systemOnline.value ? 'positive' : 'accent',
      }

  return [
    {
      key: 'pacientes',
      label: t('cardsPacientes'),
      ...pacientes,
      icon: 'users',
      tone: 'accent',
    },
    {
      key: 'riesgo',
      label: t('cardsRiesgo'),
      ...riesgo,
      icon: 'gauge',
      tone: 'accent',
    },
    {
      key: 'modelo',
      label: t('cardsModelo'),
      value: 'Logistic Regression',
      hint: t('cardsModeloHint'),
      icon: 'cpu',
      tone: 'accent',
    },
    {
      key: 'sistema',
      label: t('cardsSistema'),
      ...sistema,
      icon: 'pulse',
    },
  ]
})
</script>

<template>
  <div class="summary">
    <div v-for="card in cards" :key="card.key" class="summary__card">
      <span class="summary__icon" :class="`summary__icon--${card.tone}`" aria-hidden="true">
        <svg v-if="card.icon === 'users'" viewBox="0 0 24 24" class="summary__svg">
          <circle cx="9" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.8" />
          <path d="M2.8 19c.6-3 3.2-4.4 6.2-4.4s5.6 1.4 6.2 4.4M15.5 5.3a3.2 3.2 0 1 1 0 5.4M17 14.9c1.7.7 3.1 2 3.7 4.1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        <svg v-else-if="card.icon === 'gauge'" viewBox="0 0 24 24" class="summary__svg">
          <path d="M5.7 16.5a8 8 0 1 1 12.6 0M12 9l-2.5 4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        <svg v-else-if="card.icon === 'cpu'" viewBox="0 0 24 24" class="summary__svg">
          <rect x="7" y="7" width="10" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.8" />
          <path d="M12 4V2m0 20v-2M4 12H2m20 0h-2M7 4V2m10 2V2M7 22v-2m10 2v-2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        <svg v-else viewBox="0 0 24 24" class="summary__svg">
          <path d="M3 12h4l2.5-6 3 12 2.5-6H21" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      <div class="summary__body">
        <span class="summary__label">{{ card.label }}</span>
        <span class="summary__value">{{ card.value }}</span>
        <span class="summary__hint">{{ card.hint }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-top: 24px;
}

.summary__card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xl);
  padding: 18px;
  box-shadow: var(--shadow-sm);
}

.summary__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.summary__icon--accent {
  background: var(--color-active-bg);
  color: var(--color-accent-strong);
}

.summary__icon--positive {
  background: var(--color-positive-soft);
  color: var(--color-positive);
}

.summary__svg {
  width: 20px;
  height: 20px;
}

.summary__body {
  display: flex;
  flex-direction: column;
}

.summary__label {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-ink-faint);
}

.summary__value {
  font-size: 17px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  margin-top: 1px;
}

.summary__hint {
  font-size: 11.5px;
  color: var(--color-ink-mute);
  margin-top: 2px;
}

@media (max-width: 1080px) {
  .summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .summary {
    grid-template-columns: 1fr;
  }
}
</style>