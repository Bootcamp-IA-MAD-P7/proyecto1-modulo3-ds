<script setup>
/**
 * History view — real evaluation log from the persistence layer
 * (GET /assessments, newest first).
 *
 * States: LOADING / ERROR / EMPTY / SUCCESS. Each entry shows the date,
 * probability, risk level chip and result; if the API has no storage, the
 * ERROR state displays the backend's friendly message.
 */
import { computed, onMounted, ref } from 'vue'

import { riskLevelFromProbability, RISK_LEVELS } from '@/riskLevels.js'
import { listAssessments } from '@/services/predictionService.js'
import { t } from '@/store.js'

const assessments = ref([])
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

const isEmpty = computed(() => assessments.value.length === 0)

async function load() {
  loading.value = true
  error.value = null
  try {
    assessments.value = await listAssessments()
  } catch (err) {
    error.value = (err && err.message) || t('historyError')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">{{ t('historyEyebrow') }}</span>
      <h1 class="view__title">{{ t('historyTitle') }}</h1>
      <p class="view__subtitle">{{ t('historySubtitle') }}</p>
    </div>

    <div v-if="loading" class="state-box" role="status">
      <span class="state-box__icon state-box__icon--spin" aria-hidden="true">⟳</span>
      {{ t('historyLoading') }}
    </div>

    <div v-else-if="error" class="state-box">
      <span class="state-box__error">{{ error }}</span>
      <button class="state-box__retry" type="button" @click="load">
        {{ t('retry') }}
      </button>
    </div>

    <div v-else-if="isEmpty" class="empty">
      <svg class="empty__icon" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M4 4h16a2 2 0 0 1 0 4v12H4z"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linejoin="round"
        />
        <path
          d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
      <span class="empty__title">{{ t('historyEmptyTitle') }}</span>
      <span class="empty__hint">{{ t('historyEmptyHint') }}</span>
    </div>

    <ul v-else class="list">
      <li v-for="assessment in assessments" :key="assessment.id" class="item">
        <div class="item__left">
          <span class="item__title">{{ t(riskKey(riskLevelOf(assessment.probability))) }}</span>
          <span class="item__sub">{{ formatDateTime(assessment.created_at) }}</span>
        </div>
        <div class="item__center">
          <span class="item__pct">{{ (assessment.probability * 100).toFixed(1) }}%</span>
          <span
            class="chip"
            :class="`chip--${riskLevelOf(assessment.probability) || 'neutral'}`"
          >
            {{ t(riskKey(riskLevelOf(assessment.probability))) }}
          </span>
        </div>
        <div class="item__right">
          {{ assessment.prediction === 1 ? t('predictionPos') : t('predictionNeg') }}
        </div>
      </li>
    </ul>
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

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 160px;
  color: var(--color-ink-mute);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.state-box__icon {
  color: var(--color-accent-strong);
  font-size: 18px;
}

.state-box__icon--spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.state-box__error {
  color: var(--color-danger);
}

.state-box__retry {
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
  min-height: 260px;
  max-width: 720px;
  text-align: center;
  background: var(--color-card-glass);
  border: 1px dashed var(--color-hairline-dark);
  border-radius: var(--radius-lg);
  padding: 32px 24px;
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

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  list-style: none;
}

.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 16px 18px;
}

.item__left {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.item__title {
  font-size: 14.5px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.item__sub {
  font-size: 12.5px;
  color: var(--color-ink-faint);
}

.item__center {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.item__pct {
  font-size: 15px;
  font-weight: var(--w-700);
  color: var(--color-accent-strong);
}

.item__right {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--color-ink-mute);
  text-align: right;
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
</style>