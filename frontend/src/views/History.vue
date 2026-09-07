<script setup>
/**
 * History view. No evaluations are stored yet (the project has no database),
 * so the view shows an honest, professional empty state instead of invented
 * records. The layout is ready to receive real entries in a future phase.
 */
import { t } from '@/store.js'
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">{{ t('historyEyebrow') }}</span>
      <h1 class="view__title">{{ t('historyTitle') }}</h1>
      <p class="view__subtitle">{{ t('historySubtitle') }}</p>
    </div>

    <div class="empty">
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
</style>