<script setup>
/**
 * "5. Rendimiento del modelo" card.
 * No invented metrics. Shows a visual placeholder structure ready to receive
 * real metrics once a backend endpoint exists. States "próximamente".
 */
import { t } from '@/store.js'
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
          {{ t('perfSubtitle') }}
        </p>
      </div>
    </div>

    <div class="perf__empty">
      <svg class="perf__empty-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M4 4h16v16H4zM4 10h16M4 15h16"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
      <span class="perf__empty-title">{{ t('perfEmptyTitle') }}</span>
      <span class="perf__empty-hint">
        {{ t('perfEmptyHint') }}
      </span>
    </div>
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

.perf__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 180px;
  text-align: center;
  background: var(--color-canvas-soft);
  border: 1px dashed var(--color-hairline-dark);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.perf__empty-icon {
  width: 34px;
  height: 34px;
  color: var(--color-accent-strong);
  opacity: 0.7;
}

.perf__empty-title {
  font-size: 14px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.perf__empty-hint {
  font-size: 12.5px;
  color: var(--color-ink-mute);
  max-width: 240px;
}
</style>