<script setup>
/**
 * Issue #037 - placeholder for a future 3D brain visualization.
 * Deliberately NO real 3D model / no Three.js / no external assets.
 * The abstract node-and-links motif is pure CSS/SVG so it can be replaced
 * later without rebuilding the dashboard.
 */
</script>

<template>
  <section class="neural" aria-label="Neural visualization placeholder">
    <div class="neural__art" aria-hidden="true">
      <svg viewBox="0 0 240 160" class="neural__svg">
        <g class="neural__links">
          <line x1="120" y1="40" x2="70" y2="90" />
          <line x1="120" y1="40" x2="170" y2="90" />
          <line x1="120" y1="40" x2="120" y2="120" />
          <line x1="70" y1="90" x2="40" y2="130" />
          <line x1="170" y1="90" x2="200" y2="130" />
          <line x1="120" y1="120" x2="70" y2="130" />
          <line x1="120" y1="120" x2="170" y2="130" />
        </g>
        <g class="neural__nodes">
          <circle cx="120" cy="40" r="8" />
          <circle cx="70" cy="90" r="6" />
          <circle cx="170" cy="90" r="6" />
          <circle cx="120" cy="120" r="7" />
          <circle cx="40" cy="130" r="5" />
          <circle cx="200" cy="130" r="5" />
          <circle cx="70" cy="130" r="4" />
          <circle cx="170" cy="130" r="4" />
        </g>
      </svg>
    </div>
    <h3 class="neural__title">Neural Visualization</h3>
    <p class="neural__text">3D brain visualization coming soon</p>
  </section>
</template>

<style scoped>
.neural {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
  background: linear-gradient(180deg, rgba(14, 165, 233, 0.04), rgba(14, 165, 233, 0.01));
}

.neural__art {
  width: 200px;
  max-width: 100%;
}

.neural__svg {
  width: 100%;
  height: auto;
}

.neural__links line {
  stroke: var(--color-accent);
  stroke-width: 2;
  opacity: 0.4;
  stroke-linecap: round;
}

.neural__nodes circle {
  fill: var(--color-accent);
  opacity: 0.85;
}

/* Light animation: slight breathing on the placeholder (pure CSS). */
.neural__svg .neural__nodes circle {
  animation: pulse 2.6s ease-in-out infinite;
}

.neural__svg .neural__nodes circle:nth-child(2n) {
  animation-delay: 0.5s;
}

.neural__svg .neural__nodes circle:nth-child(3n) {
  animation-delay: 1s;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.55;
  }
  50% {
    opacity: 1;
  }
}

.neural__title {
  font-size: 15px;
  color: var(--color-text);
}

.neural__text {
  font-size: 13px;
  color: var(--color-text-soft);
}
</style>