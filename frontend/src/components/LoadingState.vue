<script setup>
import { t } from '@/store.js'

defineProps({
  message: { type: String, default: () => t('loading') },
})
</script>

<template>
  <div class="loading card" role="status" aria-live="polite">
    <span class="loading__spinner" aria-hidden="true"></span>
    <span class="loading__text">{{ message }}</span>
  </div>
</template>

<style scoped>
.loading {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-ink);
  font-size: 14px;
  font-weight: 550;
  padding: 18px 22px;
  background: var(--color-card-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(217, 169, 40, 0.35);
  box-shadow: 0 0 0 1px rgba(23, 32, 51, 0.04);
  animation: glowPulse 1.8s ease-in-out infinite;
}

.loading__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(217, 169, 40, 0.3);
  border-top-color: var(--color-accent-strong);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes glowPulse {
  0%,
  100% {
    box-shadow: 0 0 0 1px rgba(23, 32, 51, 0.04), 0 0 0 0 rgba(244, 201, 93, 0);
  }
  50% {
    box-shadow: 0 0 0 1px rgba(23, 32, 51, 0.04), 0 0 22px rgba(244, 201, 93, 0.32);
  }
}
</style>