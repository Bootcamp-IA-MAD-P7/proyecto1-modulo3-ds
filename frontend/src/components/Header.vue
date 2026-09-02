<script setup>
import logoUrl from '@/assets/logo.svg'
</script>

<template>
  <header class="app-header">
    <div class="container app-header__inner">
      <div class="brand">
        <img :src="logoUrl" alt="" class="brand__logo" aria-hidden="true" />
        <div class="brand__text">
          <span class="brand__title">F5 RiskAI</span>
          <span class="brand__subtitle">AI Stroke Risk Assessment</span>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand__logo {
  width: 36px;
  height: 36px;
}

.brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand__title {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.01em;
  color: var(--color-text);
}

.brand__subtitle {
  font-size: 12px;
  color: var(--color-text-soft);
}
</style>