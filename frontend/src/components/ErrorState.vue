<script setup>
defineProps({
  message: { type: String, default: '' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="error-state" role="alert" aria-live="assertive">
    <div class="error-state__icon" aria-hidden="true">!</div>
    <p class="error-state__message">
      {{ message || 'No se pudo conectar con el servicio de predicción.' }}
    </p>
    <button class="error-state__retry" type="button" @click="$emit('retry')">
      Reintentar
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  background: var(--color-risk-soft);
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-md);
  padding: 16px;
}

.error-state__icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-risk);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.error-state__message {
  font-size: 14px;
  color: var(--color-text);
}

.error-state__retry {
  border: none;
  background: var(--color-risk);
  color: #fff;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
}

.error-state__retry:hover {
  background: var(--color-risk);
  filter: brightness(0.95);
}
</style>