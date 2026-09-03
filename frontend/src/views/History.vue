<script setup>
/**
 * History view (mock). Timeline of demo activity. No real data.
 */
const history = [
  { fecha: '2026-09-01', evento: 'Evaluación de riesgo completada', detalle: 'Paciente Ana Martínez · prob. 1.9%' },
  { fecha: '2026-08-28', evento: 'Evaluación de riesgo completada', detalle: 'Paciente Luis Fernández · prob. 12.4%' },
  { fecha: '2026-08-25', evento: 'Evaluación del modelo actualizada', detalle: 'Baseline Logistic Regression' },
  { fecha: '2026-08-22', evento: 'Evaluación de riesgo completada', detalle: 'Paciente Pedro Sánchez · prob. 9.7%' },
]
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">Activity Log</span>
      <h1 class="view__title">Historial</h1>
      <p class="view__subtitle">Actividad reciente del sistema. Vista de demostración.</p>
    </div>

    <ol class="timeline">
      <li v-for="(h, i) in history" :key="i" class="timeline__item">
        <div class="timeline__dot" aria-hidden="true"></div>
        <div class="timeline__card">
          <span class="timeline__date">{{ h.fecha }}</span>
          <span class="timeline__evento">{{ h.evento }}</span>
          <span class="timeline__detalle">{{ h.detalle }}</span>
        </div>
      </li>
    </ol>

    <p class="view__notice">Registros de ejemplo con fines de demostración.</p>
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

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 720px;
}

.timeline__item {
  position: relative;
  display: flex;
  gap: 16px;
}

.timeline__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-accent-strong);
  box-shadow: 0 0 0 4px var(--color-active-bg);
  margin-top: 6px;
  flex-shrink: 0;
}

.timeline__item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 5.5px;
  top: 24px;
  bottom: -14px;
  width: 1.5px;
  background: var(--color-hairline);
}

.timeline__card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.timeline__date {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-ink-faint);
}

.timeline__evento {
  font-size: 14px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.timeline__detalle {
  font-size: 13px;
  color: var(--color-ink-mute);
}

.view__notice {
  margin-top: 22px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
}
</style>