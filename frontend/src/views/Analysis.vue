<script setup>
/**
 * Análisis — multimodal analysis view.
 *
 * The "Análisis" page of F5 RiskAI. It hosts the full multimodal flow:
 *
 *   DATOS DEL PACIENTE ─► MODELO ML ─► RESULTADO IA ─► BRAIN 3D (visual)
 *   IMAGEN CEREBRAL   ─► MODELO CNN ─► (preparado, futura conexión)
 *
 * IMPORTANT:
 *   - The tabular prediction flow (form -> predictStroke -> result) is reused
 *     from the existing components/services and is UNCHANGED.
 *   - The Brain3D and ImageAnalysis areas are VISUAL/UX only; no CNN, no
 *     Grad-CAM, no invented results, no medical localization claims.
 *   - It never creates endpoints or changes the API contract.
 */
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import RiskAnalysisModal from '@/components/RiskAnalysisModal.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import FactorsCard from '@/components/FactorsCard.vue'
import Brain3D from '@/components/Brain3D.vue'
import ImageAnalysis from '@/components/ImageAnalysis.vue'
import AnalysisStatus from '@/components/AnalysisStatus.vue'
import { predictStroke } from '@/services/predictionService.js'
import { t, optionLabel } from '@/store.js'

const result = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const modalOpen = ref(false)
const lastPayload = ref(null)

// Brain3D presents the analysis as a visual/UX state; it never claims to
// locate a lesion. Mapping is EXPLICITLY a representation of the flow.
const brainState = computed(() => {
  if (loading.value) return 'analyzing'
  if (result.value) return 'result'
  return 'idle'
})

const brainLabel = computed(() => {
  if (!result.value) return ''
  return result.value.prediction === 1 ? t('posHint') : t('negHint')
})

const mlStatusTone = computed(() => {
  if (loading.value) return 'active'
  if (errorMessage.value) return 'error'
  if (result.value) return 'success'
  return 'neutral'
})

const mlStatusLabel = computed(() => {
  if (loading.value) return t('summaryEstadoLoading')
  if (errorMessage.value) return t('summaryEstadoError')
  if (result.value) return t('summaryEstadoDone')
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
  } else if (s === 'result') {
    percent.value = 100
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
  } catch (err) {
    errorMessage.value = (err && err.message) || t('loadErrorDefault')
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
  <div class="analyse">
    <!-- Intro -->
    <div class="analyse__intro">
      <span class="analyse__kicker">{{ t('analysis.eyebrow') }}</span>
      <h1 class="analyse__title">{{ t('analysis.title') }}</h1>
      <p class="analyse__subtitle">{{ t('analysis.subtitle') }}</p>
      <span class="analyse__flow">{{ t('analysis.flowNote') }}</span>
    </div>

    <!-- TOP ROW: Patient data (ML) | Brain 3D -->
    <div class="analyse__top">
      <section class="panel panel--data" aria-label="Datos del paciente">
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
            <p class="card-head__subtitle">{{ t('assessSubtitle') }}</p>
          </div>
        </div>
        <PatientAssessmentForm @submit="handleSubmit" />
      </section>

      <section class="panel panel--brain" aria-label="Cerebro 3D">
        <div class="card-head">
          <span class="card-head__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <circle cx="5" cy="19" r="1.6" fill="currentColor" />
              <circle cx="12" cy="6" r="1.6" fill="currentColor" />
              <circle cx="19" cy="19" r="1.6" fill="currentColor" />
              <path d="M6 18.5 11 7m8 12-3-6M5 19l4-3m11 3-5-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </span>
          <div class="card-head__text">
            <span class="panel__kicker">{{ t('brain.eyebrow') }}</span>
            <h2 class="card-head__title">{{ t('brain.title') }}</h2>
            <p class="card-head__subtitle">{{ t('brain.subtitle') }}</p>
          </div>
        </div>

        <Brain3D :state="brainState" :label="brainLabel" :percent="percent" />

        <div class="dashboard__summary">
          <h3 class="dashboard__summary-title">{{ t('summaryTitle') }}</h3>
          <AnalysisStatus :tone="mlStatusTone" :label="mlStatusLabel" />
          <dl class="dashboard__summary-list">
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

    <!-- RESULT: ML (full width) -->
    <section class="panel panel--result" aria-label="Resultado del análisis de datos">
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
          <p class="panel__empty-text">{{ t('emptyResult') }}</p>
        </div>
      </div>
    </section>

    <!-- Factors row (if a case has been analyzed) -->
    <div class="analyse__info">
      <FactorsCard v-if="lastPayload" :factors="factorsForDisplay()" />
    </div>

    <!-- IMAGE ANALYSIS -->
    <section class="panel panel--image" aria-label="Análisis de imagen cerebral">
      <div class="card-head">
        <span class="card-head__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path
              d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <circle cx="12" cy="13" r="3.2" fill="none" stroke="currentColor" stroke-width="1.7" />
          </svg>
        </span>
        <div class="card-head__text">
          <span class="panel__kicker">{{ t('imageAnalysis.eyebrow') }}</span>
          <h2 class="card-head__title">{{ t('imageAnalysis.title') }}</h2>
          <p class="card-head__subtitle">{{ t('imageAnalysis.subtitle') }}</p>
        </div>
      </div>

      <ImageAnalysis />
    </section>
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
.analyse__intro {
  margin-bottom: 28px;
}

.analyse__kicker {
  font-size: 12px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-accent-strong);
}

.analyse__title {
  font-size: var(--fs-h1);
  margin-top: 6px;
}

.analyse__subtitle {
  margin-top: 8px;
  font-size: 15px;
  color: var(--color-ink-mute);
  max-width: 680px;
}

.analyse__flow {
  display: inline-block;
  margin-top: 14px;
  font-size: 12px;
  font-weight: var(--w-600);
  color: var(--color-ink-faint);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  background: var(--color-canvas-soft);
  padding: 7px 16px;
}

.analyse__top {
  display: grid;
  grid-template-columns: 58% 42%;
  gap: 28px;
  align-items: start;
}

.analyse__info {
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

.card-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.card-head__icon {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  color: var(--color-accent-strong);
  border-radius: var(--radius-sm);
  background: rgba(217, 169, 40, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-head__icon svg {
  width: 19px;
  height: 19px;
}

.card-head__text {
  display: flex;
  flex-direction: column;
}

.card-head__title {
  font-size: 18px;
  font-weight: var(--w-700);
  color: var(--color-primary);
  letter-spacing: -0.01em;
}

.card-head__subtitle {
  font-size: 13px;
  color: var(--color-ink-mute);
}

.panel--brain .card-head {
  margin-bottom: 16px;
}

.panel--result {
  margin-top: 24px;
}

.panel--image {
  margin-top: 24px;
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

@media (max-width: 980px) {
  .analyse__top {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>