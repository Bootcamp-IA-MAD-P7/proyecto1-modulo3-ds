<script setup>
/**
 * ImageResult — prepared component to display a future CNN image result.
 *
 * Accepted props (for future wiring):
 *   result: null | { stroke: number(0..1), noStroke: number(0..1), model: string }
 *
 * IMPORTANT: No CNN is connected yet. When `result` is null the component shows
 * a clean "prepared / not connected" state — it NEVER invents numbers. Once a
 * real endpoint exists, the parent can pass the true probabilities.
 */
import { computed } from 'vue'
import { t } from '@/store.js'

const props = defineProps({
  result: {
    type: Object,
    default: null,
    validator: (v) => v === null || (typeof v === 'object' && 'stroke' in v),
  },
})

const hasResult = computed(() => props.result !== null && props.result !== undefined)

const strokePct = computed(() =>
  hasResult.value ? Math.round((props.result.stroke || 0) * 100) : 0,
)
const noStrokePct = computed(() =>
  hasResult.value ? Math.round((props.result.noStroke || 0) * 100) : 0,
)
</script>

<template>
  <section class="iresult" aria-label="Resultado del modelo de imagen">
    <p v-if="!hasResult" class="iresult__empty">
      {{ t('imageResult.noResult') }}
    </p>

    <template v-else>
      <div class="iresult__bar" role="img" aria-label="Ictus vs no ictus">
        <div
          class="iresult__bar-seg iresult__bar-seg--stroke"
          :style="{ width: strokePct + '%' }"
        >
          <span v-if="strokePct >= 12" class="iresult__bar-label">{{ t('imageResult.strokeHigh') }}</span>
        </div>
        <div
          class="iresult__bar-seg iresult__bar-seg--no"
          :style="{ width: noStrokePct + '%' }"
        >
          <span v-if="noStrokePct >= 12" class="iresult__bar-label">{{ t('imageResult.strokeLow') }}</span>
        </div>
      </div>

      <div class="iresult__rows">
        <div class="iresult__row">
          <span class="iresult__key">
            <span class="iresult__dot" aria-hidden="true"></span>
            {{ t('imageResult.strokeHigh') }}
          </span>
          <span class="iresult__num">{{ strokePct }}%</span>
        </div>
        <div class="iresult__row">
          <span class="iresult__key">
            <span class="iresult__dot iresult__dot--no" aria-hidden="true"></span>
            {{ t('imageResult.strokeLow') }}
          </span>
          <span class="iresult__num">{{ noStrokePct }}%</span>
        </div>
      </div>

      <span class="iresult__chip">{{ t('imageResult.modelCnn') }}</span>
    </template>

    <p class="iresult__note">{{ t('imageResult.notConnected') }}</p>
  </section>
</template>

<style scoped>
.iresult {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 160px;
}

.iresult__empty {
  font-size: 13.5px;
  color: var(--color-ink-mute);
  text-align: center;
  border: 1px dashed var(--color-hairline);
  border-radius: var(--radius-md);
  padding: 26px 18px;
}

.iresult__bar {
  display: flex;
  height: 30px;
  width: 100%;
  border-radius: var(--radius-pill);
  overflow: hidden;
  background: var(--color-canvas-soft);
  border: 1px solid var(--color-hairline);
}

.iresult__bar-seg {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.4s var(--ease);
}

.iresult__bar-seg--stroke {
  background: linear-gradient(90deg, var(--color-risk), var(--color-risk-soft));
}

.iresult__bar-seg--no {
  background: linear-gradient(90deg, var(--color-positive-soft), var(--color-positive));
}

.iresult__bar-label {
  font-size: 11px;
  font-weight: var(--w-700);
  color: var(--color-ink);
}

.iresult__rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.iresult__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.iresult__key {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.iresult__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-risk);
}

.iresult__dot--no {
  background: var(--color-positive);
}

.iresult__num {
  font-size: 14px;
  font-weight: var(--w-700);
  color: var(--color-primary);
}

.iresult__chip {
  align-self: flex-start;
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-accent-strong);
  background: rgba(217, 169, 40, 0.12);
  border: 1px solid rgba(217, 169, 40, 0.28);
  border-radius: var(--radius-pill);
  padding: 5px 14px;
}

.iresult__note {
  font-size: 12px;
  color: var(--color-ink-faint);
}
</style>