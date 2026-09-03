<script setup>
import { t } from '@/store.js'

defineProps({
  message: { type: String, default: '' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="error-state card" role="alert" aria-live="assertive">
    <div class="error-state__head">
      <div class="error-state__icon" aria-hidden="true">!</div>
      <p class="error-state__message">
        {{ message || t('loadErrorDefault') }}
      </p>
    </div>
    <button class="error-state__retry" type="button" @click="$emit('retry')">
      {{ t('retry') }}
    </button>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: flex-start;
  background: var(--color-card);
  border: 1px solid rgba(216, 57, 46, 0.35);
  border-radius: var(--radius-xl);
  padding: 18px 22px;
}

.error-state__head {
  display: flex;
  gap: 12px;
  align-items: center;
}

.error-state__icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-risk);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.error-state__message {
  font-size: 14px;
  color: var(--color-ink);
}

.error-state__retry {
  border: none;
  background: var(--color-risk);
  color: #fff;
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  transition: filter var(--dur) var(--ease);
}

.error-state__retry:hover {
  filter: brightness(0.96);
}
</style>