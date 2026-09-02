<script setup>
/**
 * Issue #032 - F5 RiskAI dashboard.
 * Orchestrates: form -> service -> result/modal, plus the neural placeholder.
 */
import { ref } from 'vue'
import Header from '@/components/Header.vue'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'
import NeuralVisualization from '@/components/NeuralVisualization.vue'
import PredictionResult from '@/components/PredictionResult.vue'
import RiskAnalysisModal from '@/components/RiskAnalysisModal.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import { predictStroke } from '@/services/predictionService.js'

const result = ref(null) // { prediction, probability }
const loading = ref(false)
const errorMessage = ref('')
const modalOpen = ref(false)

// Last valid payload, reused for the "Retry" action and for the modal factors.
const lastPayload = ref(null)

async function handleSubmit(payload) {
  // Avoid multiple concurrent requests.
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
      (err && err.message) || 'No se pudo conectar con el servicio de predicción.'
  } finally {
    loading.value = false
  }
}

// "Retry" re-submits the last valid payload only if one exists.
function retry() {
  if (lastPayload.value) handleSubmit(lastPayload.value)
}

// Human-readable factors passed to the modal for display.
function factorsForModal() {
  const p = lastPayload.value
  if (!p) return {}
  return {
    gender: p.gender,
    age: `${p.age}`,
    hypertension: p.hypertension === 1 ? 'Yes' : 'No',
    heart_disease: p.heart_disease === 1 ? 'Yes' : 'No',
    ever_married: p.ever_married,
    work_type: p.work_type,
    Residence_type: p.Residence_type,
    avg_glucose_level: `${p.avg_glucose_level}`,
    bmi: `${p.bmi}`,
    smoking_status: p.smoking_status,
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
    <Header />

    <main class="container dashboard__main">
      <div class="dashboard__grid">
        <section class="panel" aria-label="Patient assessment">
          <h2 class="panel__title">Patient Assessment</h2>
          <p class="panel__subtitle">
            Introduce los datos del paciente para estimar el riesgo de ictus.
          </p>
          <PatientAssessmentForm @submit="handleSubmit" />
        </section>

        <section class="panel" aria-label="Neural visualization">
          <h2 class="panel__title">Neural Visualization</h2>
          <NeuralVisualization />
        </section>
      </div>

      <section class="result-area" aria-label="Prediction result">
        <LoadingState v-if="loading" />
        <ErrorState
          v-else-if="errorMessage"
          :message="errorMessage"
          @retry="retry"
        />
        <PredictionResult
          v-else-if="result"
          :prediction="result.prediction"
          :probability="result.probability"
          @open-analysis="openAnalysis"
        />
      </section>
    </main>
  </div>

  <RiskAnalysisModal
    :open="modalOpen"
    :prediction="result ? result.prediction : 0"
    :probability="result ? result.probability : 0"
    :factors="factorsForModal()"
    @close="closeAnalysis"
  />
</template>

<style scoped>
.dashboard__main {
  padding-top: 28px;
  padding-bottom: 40px;
}

.dashboard__grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
  align-items: start;
}

.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.panel__title {
  font-size: 18px;
  margin-bottom: 4px;
}

.panel__subtitle {
  font-size: 13px;
  color: var(--color-text-soft);
  margin-bottom: 16px;
}

.result-area {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 16px;
}

/* Tablet: stack into one column but keep panels readable. */
@media (max-width: 900px) {
  .dashboard__grid {
    grid-template-columns: 1fr;
  }
}
</style>