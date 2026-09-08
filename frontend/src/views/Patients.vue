<script setup>
/**
 * Patients view — real registry from the persistence layer (GET /patients).
 *
 * States: LOADING / ERROR / EMPTY / SUCCESS. Rows link each patient to its
 * most recent assessment (risk chip + probability + result), newest first.
 * No data is ever invented: without stored assessments the EMPTY state shows.
 */
import { computed, onMounted, ref } from 'vue'

import { riskLevelFromProbability, RISK_LEVELS } from '@/riskLevels.js'
import { listPatients } from '@/services/predictionService.js'
import { t } from '@/store.js'

const patients = ref([])
const loading = ref(true)
const error = ref(null)

const riskLevels = RISK_LEVELS

function riskLevelOf(prob) {
  return riskLevelFromProbability(typeof prob === 'number' ? prob : null)
}

function riskKey(level) {
  if (!level) return null
  return `risk.level${level[0].toUpperCase()}${level.slice(1)}`
}

function formatDateTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/**
 * Short, neutral identifier derived from the real patient UUID (no invented
 * names): the first 8 hex chars of the persisted id, e.g. "a55736ec".
 */
function shortId(id) {
  return String(id || '').slice(0, 8)
}

async function load() {
  loading.value = true
  error.value = null
  try {
    patients.value = await listPatients()
  } catch (err) {
    error.value = (err && err.message) || t('patientsError')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">{{ t('patientsEyebrow') }}</span>
      <h1 class="view__title">{{ t('patientsTitle') }}</h1>
      <p class="view__subtitle">{{ t('patientsSubtitle') }}</p>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>{{ t('patientsTablePaciente') }}</th>
            <th>{{ t('patientsTableEdad') }}</th>
            <th>{{ t('patientsTableRiesgo') }}</th>
            <th>{{ t('patientsTableProbabilidad') }}</th>
            <th>{{ t('patientsTableFecha') }}</th>
            <th>{{ t('patientsTableEstado') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6">
              <div class="state-row" role="status">{{ t('patientsLoading') }}</div>
            </td>
          </tr>

          <tr v-else-if="error">
            <td colspan="6">
              <div class="state-row">
                <span class="state-row__error">{{ error }}</span>
                <button class="state-row__retry" type="button" @click="load">
                  {{ t('retry') }}
                </button>
              </div>
            </td>
          </tr>

          <tr v-else-if="patients.length === 0">
            <td colspan="6">
              <div class="empty">
                <svg class="empty__icon" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="9" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.6" />
                  <path
                    d="M2.8 19c.6-3 3.2-4.4 6.2-4.4s5.6 1.4 6.2 4.4"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                  />
                </svg>
                <span class="empty__title">{{ t('patientsEmptyTitle') }}</span>
                <span class="empty__hint">{{ t('patientsEmptyHint') }}</span>
              </div>
            </td>
          </tr>

          <tr v-else v-for="(patient, index) in patients" :key="patient.id">
            <td class="cell cell--id">
              <span class="cell__name">{{ t('patientsIdPrefix') }} #{{ index + 1 }}</span>
              <span class="cell__sub">{{ shortId(patient.id) }}</span>
            </td>
            <td class="cell">{{ Number(patient.age).toFixed(0) }}</td>
            <td class="cell">
              <span
                v-if="patient.last_assessment"
                class="chip"
                :class="`chip--${riskLevelOf(patient.last_assessment.probability) || 'neutral'}`"
              >
                {{ t(riskKey(riskLevelOf(patient.last_assessment.probability))) }}
              </span>
              <span v-else class="chip chip--neutral">—</span>
            </td>
            <td class="cell">
              <template v-if="patient.last_assessment">
                {{ (patient.last_assessment.probability * 100).toFixed(1) }}%
              </template>
              <span v-else class="cell__muted">—</span>
            </td>
            <td class="cell">{{ formatDateTime(patient.last_assessment ? patient.last_assessment.created_at : patient.created_at) }}</td>
            <td class="cell">
              <template v-if="patient.last_assessment">
                {{ patient.last_assessment.prediction === 1 ? t('predictionPos') : t('predictionNeg') }}
              </template>
              <span v-else class="cell__muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.view__intro {
  margin-bottom: 22px;
}

.view__kicker {
  font-size: 12px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--color-accent-strong);
}

.view__title {
  font-size: var(--fs-h1);
  margin-top: 6px;
}

.view__subtitle {
  margin-top: 8px;
  font-size: 15px;
  color: var(--color-ink-mute);
}

/* Center the page intro content on wide screens. */
.view__intro {
  max-width: 920px;
}

/* Full-width table, centered in the shell with balanced side margins. */
.table-wrap {
  margin: 0 auto;
  width: 100%;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  box-shadow: var(--shadow-sm);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th {
  text-align: left;
  padding: 14px 18px;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-faint);
  background: var(--color-canvas-soft);
  white-space: nowrap;
  vertical-align: middle;
}

.table td {
  padding: 0;
  border-top: var(--color-hairline);
  white-space: nowrap;
}

/* Data cells: neutral internal padding declared on the `td` selector so it
   wins over the structural `.table td { padding: 0 }` rule (specificity
   (0,2,1) vs (0,1,1)). Without this the first column sticks to the table
   edge — the header (th) kept its padding but every body cell lost it. */
.table td.cell {
  padding: 14px 18px;
  vertical-align: middle;
}

.cell--id {
  min-width: 168px;
}

.cell__name {
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.cell__sub {
  display: block;
  font-size: 12px;
  color: var(--color-ink-faint);
  margin-top: 2px;
}

.cell__muted {
  color: var(--color-ink-faint);
}

.chip {
  display: inline-block;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: var(--radius-pill);
  padding: 4px 13px;
}

.chip--low {
  color: var(--color-success);
  background: var(--color-success-bg);
}

.chip--medium {
  color: var(--color-accent-strong);
  background: var(--color-active-bg);
}

.chip--high {
  color: var(--color-danger);
  background: var(--color-danger-bg);
}

.chip--neutral {
  color: var(--color-ink-faint);
  background: var(--color-canvas-soft);
}

.state-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 24px;
  color: var(--color-ink-mute);
  font-size: 14px;
}

.state-row__error {
  color: var(--color-danger);
}

.state-row__retry {
  font-size: 12.5px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  background: var(--color-active-bg);
  border: var(--color-hairline);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
  cursor: pointer;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 56px 24px;
  text-align: center;
}

.empty__icon {
  width: 36px;
  height: 36px;
  color: var(--color-accent-strong);
  opacity: 0.7;
}

.empty__title {
  font-size: 15px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.empty__hint {
  font-size: 13px;
  color: var(--color-ink-mute);
  max-width: 320px;
}

/* Small screens: keep ONE record per row — the wrapper scrolls horizontally
   instead of letting long values wrap into neighbouring columns. */
@media (max-width: 720px) {
  .table td.cell {
    padding: 12px 12px;
  }

  .table th {
    padding: 12px 12px;
  }

  .cell--id {
    min-width: 148px;
  }
}
</style>