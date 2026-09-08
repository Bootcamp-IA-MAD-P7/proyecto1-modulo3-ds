<script setup>
/**
 * Análisis — multimodal analysis view (EN CONSTRUCCIÓN / UNDER CONSTRUCTION).
 *
 * Tras la reorganización de Inicio (formulario del paciente + Brain3D + resumen
 * en la vista principal), esta vista queda marcada como "EN CONSTRUCCIÓN": es
 * el espacio reservado para el futuro análisis multimodal de imágenes
 * cerebrales (CNN). La insignia lleva un icono de casco de obra (SVG inline).
 *
 * IMPORTANT:
 *   - Se conservan las tarjetas de interfaz de análisis de imagen (Usar cámara /
 *     Subir imagen), pero SIN resultados de CNN: no hay Brain3D, ni Image
 *     Analysis Result, ni Grad-CAM / Activation Map, ni zonas de interés.
 *   - El botón "Analizar imagen" está deshabilitado hasta que exista un modelo
 *     CNN real (ver ImageAnalysis.vue, CNN_READY = false).
 *   - No crea endpoints ni cambia el contrato de la API.
 *   - El flujo de predicción tabular (formulario -> predictStroke -> resultado)
 *     vive ahora en la vista Inicio, junto al Brain3D con su nivel de riesgo.
 */
import { t } from '@/store.js'
import ImageAnalysis from '@/components/ImageAnalysis.vue'
</script>

<template>
  <div class="analyse">
    <!-- Intro -->
    <div class="analyse__intro">
      <span class="analyse__kicker">{{ t('analysis.eyebrow') }}</span>
      <div class="analyse__badges">
        <span class="analyse__badge analyse__badge--wip" role="status">
          <svg class="analyse__badge-helmet" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 12.5A7 7 0 0 1 19 12.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
            <path d="M12 5.5V4.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
            <path d="M7.2 9.8h9.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            <path d="M3.5 14.6h17a1.2 1.2 0 0 1 0 2.4h-17a1.2 1.2 0 0 1 0-2.4Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
          </svg>
          {{ t('construction.badge') }}
        </span>
        <span class="analyse__badge" aria-hidden="true">{{ t('construction.badgeHint') }}</span>
      </div>
      <h1 class="analyse__title">{{ t('analysis.title') }}</h1>
      <p class="analyse__subtitle">{{ t('construction.text') }}</p>
    </div>

    <!-- IMAGE ANALYSIS (interfaz preparada, modelo CNN sin conectar) -->
    <section class="panel panel--image" aria-label="Análisis de imagen cerebral">
      <div class="card-head">
        <span class="card-head__icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path
              d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            />
            <circle cx="12" cy="13" r="3.2" fill="none" stroke="currentColor" stroke-width="1.7" />
          </svg>
        </span>
        <div class="card-head__text">
          <span class="panel__kicker">{{ t('imageAnalysis.eyebrow') }}</span>
          <h2 class="card-head__title">{{ t('imageAnalysis.title') }}</h2>
          <p class="card-head__subtitle">{{ t('imageAnalysis.subtitle') }}</p>
        </div>
      </div>

      <div class="analyse__overlay-wrap">
        <ImageAnalysis />
        <div class="analyse__overlay" aria-hidden="true">
          <span class="analyse__overlay-badge">
            <svg class="analyse__badge-helmet" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 12.5A7 7 0 0 1 19 12.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
              <path d="M12 5.5V4.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
              <path d="M7.2 9.8h9.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              <path d="M3.5 14.6h17a1.2 1.2 0 0 1 0 2.4h-17a1.2 1.2 0 0 1 0-2.4Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
            </svg>
            {{ t('construction.badge') }}
          </span>
          <span class="analyse__overlay-text">{{ t('construction.overlay') }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.analyse__intro {
  margin-bottom: 28px;
}

.analyse__kicker {
  font-size: 12px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-accent-strong);
}

.analyse__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.analyse__badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-ink-mute);
  background: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
}

.analyse__badge--wip {
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border-color: rgba(217, 169, 40, 0.35);
}

:root[data-theme='dark'] .analyse__badge--wip {
  color: var(--color-accent);
}

.analyse__badge-helmet {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--color-accent-strong);
}

.analyse__title {
  font-size: var(--fs-h1);
  margin-top: 12px;
}

.analyse__subtitle {
  margin-top: 8px;
  font-size: 15px;
  color: var(--color-ink-mute);
  max-width: 680px;
}

.panel {
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: 26px;
  box-shadow: var(--shadow-sm);
}

.panel__kicker {
  font-size: 10.5px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-accent-strong);
}

.card-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.card-head__icon {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  color: var(--color-accent-strong);
  border-radius: var(--radius-sm);
  background: rgba(217, 169, 40, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-head__icon svg {
  width: 19px;
  height: 19px;
}

.card-head__text {
  display: flex;
  flex-direction: column;
}

.card-head__title {
  font-size: 18px;
  font-weight: var(--w-700);
  color: var(--color-primary);
  letter-spacing: -0.01em;
}

.card-head__subtitle {
  font-size: 13px;
  color: var(--color-ink-mute);
}

.panel--image {
  margin-top: 24px;
}

/* ── Under-construction overlay (semi-transparent, blocks interaction) ── */
.analyse__overlay-wrap {
  position: relative;
}

.analyse__overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  background: var(--color-card-glass);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.analyse__overlay-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border: 1px solid rgba(217, 169, 40, 0.35);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
}

.analyse__overlay-text {
  font-size: 13px;
  color: var(--color-ink-mute);
  max-width: 320px;
}
</style>