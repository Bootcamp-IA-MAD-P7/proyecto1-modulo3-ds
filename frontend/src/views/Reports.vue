<script setup>
/**
 * Reports view (mock). Cards describing future report types. No real data.
 */
const reports = [
  {
    key: 'modelo',
    icon: 'cpu',
    label: 'Evaluación del modelo',
    desc: 'Métricas globales del baseline: accuracy, recall, AUC y matriz de confusión.',
    estado: 'Próximamente',
  },
  {
    key: 'riesgo',
    icon: 'gauge',
    label: 'Análisis de riesgo',
    desc: 'Resumen agregado del riesgo estimado sobre los casos evaluados.',
    estado: 'Próximamente',
  },
  {
    key: 'preds',
    icon: 'list',
    label: 'Reporte de predicciones',
    desc: 'Historial exportable de predicciones y factores asociados.',
    estado: 'Próximamente',
  },
]
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">Reports</span>
      <h1 class="view__title">Reportes</h1>
      <p class="view__subtitle">Informes generados por el sistema. Vista de demostración.</p>
    </div>

    <div class="grid">
      <section v-for="r in reports" :key="r.key" class="panel">
        <span class="panel__icon" aria-hidden="true">
          <svg v-if="r.icon === 'cpu'" viewBox="0 0 24 24">
            <rect x="7" y="7" width="10" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.8" />
            <path d="M12 4V2m0 20v-2M4 12H2m20 0h-2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          <svg v-else-if="r.icon === 'gauge'" viewBox="0 0 24 24">
            <path d="M5.7 16.5a8 8 0 1 1 12.6 0M12 9l-2.5 4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          <svg v-else viewBox="0 0 24 24">
            <path d="M8 6h8M8 10h8M8 14h5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            <rect x="4" y="3" width="16" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </span>
        <div class="panel__body">
          <h2 class="panel__title">{{ r.label }}</h2>
          <p class="panel__desc">{{ r.desc }}</p>
          <span class="panel__chip">{{ r.estado }}</span>
        </div>
      </section>
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

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

.panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 22px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.panel__icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--color-active-bg);
  color: var(--color-accent-strong);
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel__icon svg {
  width: 22px;
  height: 22px;
}

.panel__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel__title {
  font-size: 17px;
  color: var(--color-primary);
}

.panel__desc {
  font-size: 13px;
  color: var(--color-ink-mute);
  line-height: 1.45;
}

.panel__chip {
  align-self: flex-start;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-ink);
  background: var(--color-active-bg);
  border-radius: var(--radius-pill);
  padding: 4px 13px;
}
</style>