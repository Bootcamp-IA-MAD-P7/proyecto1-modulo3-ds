<script setup>
/**
 * F5 RiskAI dashboard (content view, rendered inside AppLayout).
 * Layout:
 *   - Patient Assessment (full width) — the 3D brain lives in the Análisis view.
 *   - Below:     Risk Result (full width)
 *   - Below:     Risk Analysis (factors) | Model Metrics (breathing row)
 * Prediction flow form -> service -> result/analysis is unchanged.
 */
import { ref } from 'vue'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import RiskAnalysisModal from '@/components/RiskAnalysisModal.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import FactorsCard from '@/components/FactorsCard.vue'
import ModelPerformance from '@/components/ModelPerformance.vue'
import SummaryCards from '@/components/SummaryCards.vue'
import { predictStroke } from '@/services/predictionService.js'
import { t, state, optionLabel } from '@/store.js'

const result = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const modalOpen = ref(false)
const lastPayload = ref(null)

async function handleSubmit(payload) {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  result.value = null
  lastPayload.value = payload

  try {
    const data = await predictStroke(payload)
    result.value = { prediction: data.prediction, probability: data.probability }
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

    <!-- SECTION 1 (top): Patient Assessment (full width) -->
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
          v-else-if="result"
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

    <SummaryCards />
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

/* SECTION 1: Patient Assessment (full width) */
.dashboard__top {
  display: grid;
  grid-template-columns: 1fr;
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

/* Tablet: stack sections into a single column; result stays full width. */
@media (max-width: 980px) {
  .dashboard__info {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>