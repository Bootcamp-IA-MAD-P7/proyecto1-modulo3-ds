<script setup>
/**
 * "5. Rendimiento del modelo" card.
 * Real metrics of the FINAL tuned model (LogisticRegression + RandomOverSampler,
 * C=0.5, solver=lbfgs, max_iter=500, random_state=42) evaluated exclusively on
 * the reserved Test set (997 cases).
 * Source: reports/final-model-evaluation.md (ticket #052). The values below are
 * displayed exactly as reported — never computed or invented in the frontend.
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const metrics = computed(() => [
  { key: 'accuracy', label: t('perfAccuracy'), value: '75.33%' },
  { key: 'recall', label: t('perfRecall'), value: '82.00%' },
  { key: 'f1', label: t('perfF1'), value: '25.00%' },
  { key: 'auc', label: t('perfAuc'), value: '83.95%' },
])
</script>

<template>
  <section class="perf" aria-label="Rendimiento del modelo">
    <div class="card-head">
      <span class="card-head__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path
            d="M4 20V10m6 10V4m6 16v-7m4 7H2"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </span>
      <div class="card-head__text">
        <span class="perf__kicker">{{ t('perfEyebrow') }}</span>
        <h2 class="card-head__title">{{ t('perfTitle') }}</h2>
        <p class="card-head__subtitle">
          <span class="perf__note-label">{{ t('perfNote') }}</span>
        </p>
      </div>
    </div>

    <div class="perf__grid">
      <div v-for="m in metrics" :key="m.key" class="perf__metric">
        <span class="perf__metric-label">{{ m.label }}</span>
        <span class="perf__metric-value">{{ m.value }}</span>
      </div>
    </div>

    <p class="perf__source">
      {{ t('perfSource') }}
    </p>
  </section>
</template>

<style scoped>
.perf {
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xl);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  min-height: 200px;
}

.perf__kicker {
  font-size: 10.5px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent-strong);
}

.perf__note-label {
  display: inline-block;
  font-size: 12px;
  font-weight: var(--w-600);
  color: var(--color-accent-strong);
  background: var(--color-active-bg);
  border: 1px solid var(--color-active-border);
  border-radius: var(--radius-pill);
  padding: 3px 12px;
  margin-top: 6px;
}

.perf__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 18px;
}

.perf__metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: 16px 14px;
}

.perf__metric-label {
  font-size: 10.5px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink-faint);
}

.perf__metric-value {
  font-size: 24px;
  font-weight: var(--w-700);
  color: var(--color-primary);
  letter-spacing: -0.01em;
}

.perf__source {
  margin-top: 14px;
  font-size: 12px;
  color: var(--color-ink-mute);
}

@media (max-width: 640px) {
  .perf__grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>