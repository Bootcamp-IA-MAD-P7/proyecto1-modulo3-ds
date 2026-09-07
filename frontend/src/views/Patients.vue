<script setup>
/**
 * Patients view. The registry is intentionally empty: the project has no
 * database yet, so patients are never invented. The table structure stays
 * ready to receive real records in a future phase.
 */
import { t } from '@/store.js'
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
          <tr>
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
        </tbody>
      </table>
    </div>

    <p class="view__notice">{{ t('patientsNotice') }}</p>
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

.table-wrap {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
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
}

.table td {
  padding: 0;
  border-top: var(--color-hairline);
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

.view__notice {
  margin-top: 18px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
}
</style>