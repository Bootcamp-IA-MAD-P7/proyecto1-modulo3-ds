<script setup>
/**
 * Settings view (UI only). Toggles are frontend state only — no persistence.
 * Deliberately not wired to any backend.
 */
import { ref } from 'vue'

const notifications = ref(true)
const temaOscuro = ref(false)

const sections = [
  { key: 'perfil', title: 'Perfil', items: ['Nombre de usuario', 'Correo electrónico', 'Rol'] },
  { key: 'recursos', title: 'Modelo y recursos', items: ['Versión del modelo', 'Fuente de datos', 'Canal de predicción'] },
]
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">Preferences</span>
      <h1 class="view__title">Ajustes</h1>
      <p class="view__subtitle">Preferencias de la aplicación. Cambios de interfaz únicamente.</p>
    </div>

    <div class="layout">
      <section v-for="s in sections" :key="s.key" class="panel">
        <h2 class="panel__title">{{ s.title }}</h2>
        <ul class="panel__list">
          <li v-for="(item, i) in s.items" :key="i" class="panel__row">
            <span>{{ item }}</span>
            <span class="panel__placeholder">—</span>
          </li>
        </ul>
      </section>

      <section class="panel">
        <h2 class="panel__title">Preferencias</h2>
        <div class="switch-row">
          <div class="switch-row__text">
            <span class="switch-row__label">Notificaciones</span>
            <span class="switch-row__hint">Avisos sobre predicciones y estado del servicio</span>
          </div>
          <button
            class="switch"
            :class="{ 'switch--on': notifications }"
            type="button"
            role="switch"
            :aria-checked="notifications"
            @click="notifications = !notifications"
          >
            <span class="switch__thumb"></span>
          </button>
        </div>

        <div class="switch-row">
          <div class="switch-row__text">
            <span class="switch-row__label">Tema oscuro</span>
            <span class="switch-row__hint">No disponible en esta versión</span>
          </div>
          <button
            class="switch"
            type="button"
            role="switch"
            :aria-checked="temaOscuro"
            @click="temaOscuro = !temaOscuro"
          >
            <span class="switch__thumb"></span>
          </button>
        </div>
      </section>
    </div>

    <p class="view__notice">Algunos ajustes requieren integración con el backend.</p>
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

.layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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
}

.panel__title {
  font-size: 16px;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: var(--color-hairline);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.panel__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  font-size: 14px;
  color: var(--color-ink);
}

.panel__row + .panel__row {
  border-top: var(--color-hairline);
}

.panel__placeholder {
  color: var(--color-ink-faint);
}

.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
}

.switch-row + .switch-row {
  border-top: var(--color-hairline);
}

.switch-row__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.switch-row__label {
  font-size: 14px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.switch-row__hint {
  font-size: 12px;
  color: var(--color-ink-mute);
}

.switch {
  position: relative;
  width: 46px;
  height: 26px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-hairline);
  background: var(--color-canvas-soft);
  transition: background var(--dur) var(--ease), border-color var(--dur) var(--ease);
  flex-shrink: 0;
}

.switch.switch--on {
  background: var(--color-accent-strong);
  border-color: var(--color-accent-strong);
}

.switch__thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur) var(--ease);
}

.switch--on .switch__thumb {
  transform: translateX(20px);
}

.view__notice {
  margin-top: 22px;
  font-size: 12.5px;
  color: var(--color-ink-faint);
}
</style>