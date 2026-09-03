<script setup>
/**
 * Help view. Static FAQ Q/A + medical disclaimer. No data.
 */
const faqs = [
  {
    q: '¿Qué hace F5 RiskAI?',
    a: 'Estimada el riesgo de ictus a partir de los factores clínicos y demográficos ingresados, mediante un modelo de machine learning.',
  },
  {
    q: '¿Es un diagnóstico médico?',
    a: 'No. Es una herramienta de apoyo a la decisión. El resultado debe ser interpretado siempre por un profesional sanitario.',
  },
  {
    q: '¿Qué datos se usan?',
    a: 'Únicamente los factores introducidos en el formulario de evaluación (edad, género, hipertensión, etc.).',
  },
  {
    q: '¿Dónde está la visualización Brain3D?',
    a: 'El área de visualización neuronal está reservada para una futura integración 3D.',
  },
]
</script>

<template>
  <div class="view">
    <div class="view__intro">
      <span class="view__kicker">Support</span>
      <h1 class="view__title">Ayuda</h1>
      <p class="view__subtitle">Preguntas frecuentes sobre la aplicación.</p>
    </div>

    <div class="faq">
      <details v-for="(f, i) in faqs" :key="i" class="faq__item">
        <summary class="faq__question">{{ f.q }}</summary>
        <p class="faq__answer">{{ f.a }}</p>
      </details>
    </div>

    <div class="medical-note">
      <h2 class="medical-note__title">Aviso médico</h2>
      <p class="medical-note__text">
        Esta aplicación ofrece estimaciones estadísticas y no sustituye la valoración de un
        profesional de la salud. Ante cualquier duda, consulte siempre con su médico.
      </p>
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

.faq {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 720px;
}

.faq__item {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--color-hairline);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: 16px 20px;
}

.faq__question {
  font-size: 15px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  cursor: pointer;
  list-style: none;
}

.faq__question::-webkit-details-marker {
  display: none;
}

.faq__answer {
  font-size: 13.5px;
  color: var(--color-ink-mute);
  margin: 10px 0 0;
  line-height: 1.5;
}

.medical-note {
  margin-top: 26px;
  max-width: 720px;
  border: 1px solid rgba(27, 25, 56, 0.1);
  background: var(--color-canvas-soft);
  border-radius: var(--radius-lg);
  padding: 18px 22px;
}

.medical-note__title {
  font-size: 15px;
  font-weight: var(--w-700);
  color: var(--color-ink);
  margin-bottom: 6px;
}

.medical-note__text {
  font-size: 13px;
  color: var(--color-ink-mute);
  line-height: 1.5;
}
</style>