<script setup>
/**
 * Patients view (mock). Demo table only, no real data. Clearly labeled.
 */
const patients = [
  { id: 1, nombre: 'Ana Martínez', edad: 58, riesgo: 'Negativo', prob: '1.9%', fecha: '2026-09-01', estado: 'Completo' },
  { id: 2, nombre: 'Luis Fernández', edad: 71, riesgo: 'Positivo', prob: '12.4%', fecha: '2026-08-28', estado: 'Completo' },
  { id: 3, nombre: 'Carmen Ruiz', edad: 45, riesgo: 'Negativo', prob: '0.8%', fecha: '2026-08-25', estado: 'En revisión' },
  { id: 4, nombre: 'Pedro Sánchez', edad: 64, riesgo: 'Positivo', prob: '9.7%', fecha: '2026-08-22', estado: 'Completo' },
]
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">Patient Registry</span>
      <h1 class="view__title">Pacientes</h1>
      <p class="view__subtitle">Registro de casos evaluados. Vista de demostración.</p>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Paciente</th>
            <th>Edad</th>
            <th>Riesgo</th>
            <th>Probabilidad</th>
            <th>Fecha</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in patients" :key="p.id">
            <td class="table__name">{{ p.nombre }}</td>
            <td>{{ p.edad }}</td>
            <td>
              <span class="badge" :class="p.riesgo === 'Positivo' ? 'badge--positive' : 'badge--negative'">
                {{ p.riesgo }}
              </span>
            </td>
            <td>{{ p.prob }}</td>
            <td>{{ p.fecha }}</td>
            <td>{{ p.estado }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="view__notice">Datos de ejemplo con fines de demostración — no son pacientes reales.</p>
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
  padding: 13px 18px;
  color: var(--color-ink);
  border-top: var(--color-hairline);
}

.table__name {
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.badge {
  display: inline-block;
  font-size: 11.5px;
  font-weight: var(--w-600);
  border-radius: var(--radius-pill);
  padding: 3px 12px;
}

.badge--negative {
  background: var(--color-positive-soft);
  color: var(--color-positive);
}

.badge--positive {
  background: var(--color-risk-soft);
  color: var(--color-risk);
}

.view__notice {
  margin-top: 18px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
}
</style>