<script setup>
/**
 * F5 RiskAI dashboard (content view, rendered inside AppLayout).
 * Layout:
 *   - Top row (50/50): Patient Assessment (left) | Análisis — Brain3D + risk
 *     summary (right). The panel title is simply "Análisis"; the brain reacts
 *     to the REAL model probability as a presentation-only risk level
 *     (LOW/MEDIUM/ELEVATED, see src/riskLevels.js) with green/gold/red glow.
 *   - Below:     Risk Result (full width)
 *   - Below:     Risk Analysis (factors) | Model Metrics (breathing row)
 * Prediction flow form -> service -> result is unchanged; the Brain3D state
 * and the summary BOTH derive from probability -> riskLevel() (single source).
 */
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import RiskAnalysisModal from '@/components/RiskAnalysisModal.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import FactorsCard from '@/components/FactorsCard.vue'
import ModelPerformance from '@/components/ModelPerformance.vue'
import SummaryCards from '@/components/SummaryCards.vue'
import Brain3D from '@/components/Brain3D.vue'
import AnalysisStatus from '@/components/AnalysisStatus.vue'
import { predictStroke } from '@/services/predictionService.js'
import { riskLevelFromProbability } from '@/riskLevels.js'
import { t, state, optionLabel } from '@/store.js'

const result = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const modalOpen = ref(false)
const lastPayload = ref(null)

/**
 * Incremented after every prediction that was actually persisted
 * (assessment_id from the API) so the SummaryCards statistics refresh
 * automatically — no manual page reload needed.
 */
const statsRefreshKey = ref(0)

/**
 * Visual risk level for the Brain3D + summary, derived ONLY from the real
 * probability returned by POST /predict. Unusable values (missing/out of
 * range) fall back to the neutral 'idle' state — no invented level.
 */
const riskLevel = computed(() => {
  if (!result.value) return null
  return riskLevelFromProbability(Number(result.value.probability))
})

const brainState = computed(() => {
  if (loading.value) return 'analyzing'
  if (errorMessage.value) return 'idle'
  return riskLevel.value || 'idle'
})

/** Probability expressed as a 0..100 percentage for display + percent prop.
 *  Only meaningful when a valid risk level exists (in-range number); otherwise
 *  0 — never an invented/derived value. */
const probabilityPercent = computed(() => {
  if (!riskLevel.value) return 0
  const p = Number(result.value.probability)
  if (!Number.isFinite(p)) return 0
  return Math.max(0, Math.min(100, Math.round(p * 100)))
})

/**
 * The API probability is displayable only when it is a finite 0..1 number
 * (the backend contract always satisfies this). With a malformed payload the
 * result panel stays empty instead of showing invented/NaN numbers.
 */
const hasUsableProbability = computed(() => {
  if (!result.value) return false
  const p = Number(result.value.probability)
  return Number.isFinite(p) && p >= 0 && p <= 1
})

const RISK_TONE = { low: 'success', medium: 'info', high: 'error' }

const mlStatusTone = computed(() => {
  if (loading.value) return 'active'
  if (errorMessage.value) return 'error'
  return riskLevel.value ? RISK_TONE[riskLevel.value] : 'neutral'
})

const mlStatusLabel = computed(() => {
  if (loading.value) return t('summaryEstadoLoading')
  if (errorMessage.value) return t('summaryEstadoError')
  if (riskLevel.value) {
    const key = `risk.level${riskLevel.value[0].toUpperCase()}${riskLevel.value.slice(1)}`
    return t(key)
  }
  return t('summaryEstado')
})

let progressTimer = null
const percent = ref(0)

watch(brainState, (s) => {
  if (progressTimer) clearInterval(progressTimer)
  progressTimer = null
  if (s === 'analyzing') {
    percent.value = 0
    progressTimer = setInterval(() => {
      percent.value = Math.min(100, percent.value + Math.round(Math.random() * 9))
      if (percent.value >= 100) {
        clearInterval(progressTimer)
        progressTimer = null
      }
    }, 180)
  } else if (s !== 'idle') {
    // Risk states show the REAL probability as the percentage.
    percent.value = probabilityPercent.value
  }
})

onBeforeUnmount(() => {
  if (progressTimer) clearInterval(progressTimer)
})

async function handleSubmit(payload) {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  result.value = null
  lastPayload.value = payload

  try {
    const data = await predictStroke(payload)
    result.value = { prediction: data.prediction, probability: data.probability }
    // The evaluation was stored in PostgreSQL -> refresh dashboard stats.
    if (data.assessment_id) statsRefreshKey.value += 1
  } catch (err) {
    errorMessage.value =
      (err && err.message) || t('loadErrorDefault')
  } finally {
    loading.value = false
  }
}

function retry() {
  if (lastPayload.value) handleSubmit(lastPayload.value)
}

function factorsForDisplay() {
  const p = lastPayload.value
  if (!p) return {}
  const boolTxt = (v) => (v === 1 ? t('yes') : t('no'))
  return {
    age: `${p.age}`,
    gender: optionLabel('gender', p.gender),
    hypertension: boolTxt(p.hypertension),
    heart_disease: boolTxt(p.heart_disease),
    ever_married: optionLabel('ever_married', p.ever_married),
    work_type: optionLabel('work_type', p.work_type),
    Residence_type: optionLabel('Residence_type', p.Residence_type),
    avg_glucose_level: `${p.avg_glucose_level}`,
    bmi: `${p.bmi}`,
    smoking_status: optionLabel('smoking_status', p.smoking_status),
  }
}

function openAnalysis() {
  if (result.value) modalOpen.value = true
}

function closeAnalysis() {
  modalOpen.value = false
}
</script>

<template>
  <div class="dashboard">
    <div class="dashboard__intro">
      <span class="dashboard__kicker">{{ t('kicker') }}</span>
      <h1 class="dashboard__title">{{ t('title') }}</h1>
      <p class="dashboard__subtitle">
        {{ t('subtitle') }}
      </p>
      <p class="dashboard__disclaimer">
        {{ t('disclaimer') }}
      </p>
    </div>

    <!-- SECTION 1 (top, 50/50): Patient Assessment | Brain3D + Analysis Summary -->
    <div class="dashboard__top">
      <section class="panel panel--assess" aria-label="Patient assessment">
        <div class="card-head">
          <span class="card-head__icon" aria-hidden="true">
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
          <div class="card-head__text">
            <span class="panel__kicker">{{ t('assessEyebrow') }}</span>
            <h2 class="card-head__title">{{ t('assessTitle') }}</h2>
            <p class="card-head__subtitle">
              {{ t('assessSubtitle') }}
            </p>
          </div>
        </div>
        <PatientAssessmentForm @submit="handleSubmit" />
      </section>

      <section class="panel panel--brain" aria-label="Análisis 3D">
        <Brain3D :state="brainState" :percent="percent" />

        <div class="dashboard__summary">
          <h3 class="dashboard__summary-title">{{ t('summaryTitle') }}</h3>
          <AnalysisStatus :tone="mlStatusTone" :label="mlStatusLabel" />
          <dl class="dashboard__summary-list">
            <dt class="dashboard__summary-key">{{ t('risk.probabilityLabel') }}</dt>
            <dd class="dashboard__summary-value">{{ probabilityPercent }}%</dd>
            <dt class="dashboard__summary-key">{{ t('modelLabel') }}</dt>
            <dd class="dashboard__summary-value">Logistic Regression</dd>
            <dt class="dashboard__summary-key">{{ t('inputLabel') }}</dt>
            <dd class="dashboard__summary-value">
              {{ lastPayload ? `${Object.keys(lastPayload).length} ${t('summaryEntradaOf')}` : t('summaryEntradaIdle') }}
            </dd>
          </dl>
        </div>
      </section>
    </div>

    <!-- SECTION 2: RISK RESULT (full width) -->
    <section class="panel panel--result" aria-label="Prediction result">
      <div class="card-head">
        <span class="card-head__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path
              d="M9 12l2.5 2.5L15.5 9.5M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </span>
        <div class="card-head__text">
          <span class="panel__kicker">{{ t('resultEyebrow') }}</span>
          <h2 class="card-head__title">{{ t('resultTitle') }}</h2>
          <p class="card-head__subtitle">{{ t('resultSubtitle') }}</p>
        </div>
      </div>

      <div class="panel__body">
        <LoadingState v-if="loading" />
        <ErrorState v-else-if="errorMessage" :message="errorMessage" @retry="retry" />
        <PredictionResult
          v-else-if="result && hasUsableProbability"
          :prediction="result.prediction"
          :probability="result.probability"
          @open-analysis="openAnalysis"
        />
        <div v-else class="panel__empty">
          <svg class="panel__empty-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.5" />
            <path d="M12 8v4l2.5 1.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
          <p class="panel__empty-text">
            {{ t('emptyResult') }}
          </p>
        </div>
      </div>
    </section>

    <!-- SECTION 3 (info): Risk Analysis | Model Metrics (breathing) -->
    <div class="dashboard__info">
      <FactorsCard v-if="lastPayload" :factors="factorsForDisplay()" />
      <div v-else class="panel factors-slot" aria-label="Risk analysis">
        <div class="card-head">
          <span class="card-head__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M4 9h16M4 15h16M4 6h10M4 18h10" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
            </svg>
          </span>
          <div class="card-head__text">
            <span class="panel__kicker">Risk Analysis</span>
            <h2 class="card-head__title">{{ t('impactSlotTitle') }}</h2>
            <p class="card-head__subtitle">{{ t('impactSlotSubtitle') }}</p>
          </div>
        </div>
        <p class="panel__empty-text">{{ t('impactSlotEmpty') }}</p>
      </div>

      <ModelPerformance />
    </div>

    <SummaryCards :refresh-key="statsRefreshKey" />
  </div>

  <RiskAnalysisModal
    :open="modalOpen"
    :prediction="result ? result.prediction : 0"
    :probability="result ? result.probability : 0"
    :factors="factorsForDisplay()"
    @close="closeAnalysis"
  />
</template>

<style scoped>
.dashboard__intro {
  margin-bottom: 30px;
}

.dashboard__kicker {
  font-size: 12px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-accent-strong);
}

.dashboard__title {
  font-size: 40px;
  line-height: 1.12;
  margin-top: 8px;
  letter-spacing: -0.03em;
}

.dashboard__subtitle {
  margin-top: 12px;
  font-size: 15.5px;
  color: var(--color-ink-mute);
  max-width: 680px;
}

.dashboard__disclaimer {
  margin-top: 6px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
}

/* SECTION 1 (top): Patient Assessment | Brain3D — 50/50 */
.dashboard__top {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  align-items: start;
}

/* SECTION 3 info row — breathing two-column distribution */
.dashboard__info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  align-items: start;
  margin-top: 28px;
}

.panel {
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: 26px;
  box-shadow: var(--shadow-sm);
}

.panel__kicker {
  font-size: 10.5px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-accent-strong);
}

.panel--assess .card-head {
  margin-bottom: 18px;
}

.panel--brain .card-head {
  margin-bottom: 16px;
}

.dashboard__summary {
  margin-top: 18px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  background: var(--color-card);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dashboard__summary-title {
  font-size: 12px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent-strong);
}

.dashboard__summary-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 18px;
  margin: 0;
}

.dashboard__summary-key {
  grid-column: 1;
  font-size: 12px;
  color: var(--color-ink-faint);
  margin: 0;
}

.dashboard__summary-value {
  grid-column: 2;
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  margin: 0;
  overflow-wrap: anywhere;
}

.panel--result {
  margin-top: 24px;
}

.panel--result .card-head {
  margin-bottom: 18px;
}

.panel__body {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 16px;
}

.panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 150px;
  text-align: center;
  background: var(--color-canvas-soft);
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 24px;
}

.panel__empty-icon {
  width: 34px;
  height: 34px;
  color: var(--color-accent-strong);
  opacity: 0.7;
}

.panel__empty-text {
  font-size: 13px;
  color: var(--color-ink-mute);
  max-width: 300px;
}

.factors-slot {
  min-height: 200px;
}

/* Tablet: stack sections into a single column (form -> brain -> result). */
@media (max-width: 980px) {
  .dashboard__top,
  .dashboard__info {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>