<script setup>
/**
 * AnalysisStatus — small reusable status chip.
 * tone: 'neutral' | 'active' | 'info' | 'success' | 'error'
 */
import { computed } from 'vue'

const props = defineProps({
  tone: {
    type: String,
    default: 'neutral',
    validator: (v) => ['neutral', 'active', 'info', 'success', 'error'].includes(v),
  },
  label: { type: String, default: '' },
})

const cls = computed(() => `astatus astatus--${props.tone}`)
</script>

<template>
  <span :class="cls" role="status">
    <span class="astatus__dot" aria-hidden="true"></span>
    <span v-if="label" class="astatus__label">{{ label }}</span>
    <slot />
  </span>
</template>

<style scoped>
.astatus {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  font-weight: var(--w-700);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--color-ink-mute);
  background: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  padding: 5px 13px;
}

.astatus__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-ink-faint);
}

/* tone modifiers */
.astatus--active .astatus__dot {
  background: var(--color-accent-strong);
  animation: blink 1.2s ease-in-out infinite;
}

.astatus--info .astatus__dot {
  background: var(--color-accent);
}

.astatus--success .astatus__dot {
  background: var(--color-positive);
}

.astatus--error .astatus__dot {
  background: var(--color-risk);
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.35;
  }
}
</style>