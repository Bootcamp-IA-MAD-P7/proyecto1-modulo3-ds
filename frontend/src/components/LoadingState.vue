<script setup>
defineProps({
  message: { type: String, default: 'Analizando riesgo...' },
})
</script>

<template>
  <div class="loading" role="status" aria-live="polite">
    <span class="loading__spinner" aria-hidden="true"></span>
    <span class="loading__text">{{ message }}</span>
  </div>
</template>

<style scoped>
.loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-soft);
  font-size: 14px;
}

.loading__spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-accent-soft);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>