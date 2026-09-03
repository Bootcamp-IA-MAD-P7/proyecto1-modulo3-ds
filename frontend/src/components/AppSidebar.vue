<script setup>
/**
 * App sidebar navigation.
 * Links to real routes; active item gets a soft-yellow glow + small indicator.
 * F5 RiskAI / Health Intelligence brand identity. Theme-aware (light/dark)
 * and localized (es/en). Collapses to an off-canvas drawer on tablet/mobile.
 */
import logoUrl from '@/assets/logomedic.png'
import { t } from '@/store.js'

defineProps({
  open: { type: Boolean, default: false },
})

defineEmits(['close'])

const navItems = [
  { key: 'inicio', to: '/', icon: 'home' },
  { key: 'analisis', to: '/analysis', icon: 'chart' },
  { key: 'pacientes', to: '/patients', icon: 'users' },
  { key: 'informes', to: '/reports', icon: 'doc' },
  { key: 'historial', to: '/history', icon: 'clock' },
  { key: 'ajustes', to: '/settings', icon: 'settings' },
  { key: 'ayuda', to: '/help', icon: 'help' },
]
</script>

<template>
  <div
    v-if="open"
    class="sidebar__overlay"
    data-testid="sidebar-overlay"
    @click.self="$emit('close')"
  ></div>

  <aside class="sidebar" :class="{ 'sidebar--open': open }" aria-label="Main navigation">
    <div class="sidebar__head">
      <img :src="logoUrl" alt="" class="sidebar__logo" aria-hidden="true" />
      <div class="sidebar__brand">
        <span class="sidebar__name">F5 RiskAI</span>
        <span class="sidebar__tag">{{ t('health') }}</span>
      </div>
      <button
        class="sidebar__close"
        type="button"
        aria-label="Cerrar menú"
        @click="$emit('close')"
      >
        &times;
      </button>
    </div>

    <nav class="sidebar__nav">
      <router-link
        v-for="item in navItems"
        :key="item.key"
        :to="item.to"
        class="sidebar__item"
        exact-active-class="sidebar__item--active"
        @click="$emit('close')"
      >
        <span class="sidebar__indicator" aria-hidden="true"></span>
        <svg
          v-if="item.icon === 'home'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <svg
          v-else-if="item.icon === 'chart'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M4 20V10m6 10V4m6 16v-7m4 7H2"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <svg
          v-else-if="item.icon === 'users'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="9" cy="8" r="3.1" fill="none" stroke="currentColor" stroke-width="1.7" />
          <path
            d="M2.8 19c.6-3 3.2-4.4 6.2-4.4s5.6 1.4 6.2 4.4M15.5 5.3a3.1 3.1 0 1 1 0 5.4M17 14.9c1.7.7 3.1 2 3.7 4.1"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
          />
        </svg>
        <svg
          v-else-if="item.icon === 'doc'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            d="M7 3h7l4 4v14H7V3Zm7 0v4h4M10 12h5m-5 4h5"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <svg
          v-else-if="item.icon === 'clock'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7" />
          <path d="M12 7v5l3.5 2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
        </svg>
        <svg
          v-else-if="item.icon === 'settings'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.7" />
          <path
            d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1m0-12.8-2.1 2.1M7.7 16.3l-2.1 2.1"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
          />
        </svg>
        <svg
          v-else-if="item.icon === 'help'"
          class="sidebar__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7" />
          <path
            d="M9.2 9.2a2.8 2.8 0 1 1 3.8 3.6c-.7.4-1 .8-1 1.7M12 17.2h.01"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
          />
        </svg>
        <span class="sidebar__label">{{ t('nav.' + item.key) }}</span>
      </router-link>
    </nav>

    <div class="sidebar__foot">
      <span class="sidebar__tagline">{{ t('tagline') }}</span>
      <span class="sidebar__version">{{ t('version') }}</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  --w: var(--sidebar-width);
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--w);
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 2px solid #f4c95d;
  padding: 20px 14px;
  z-index: 40;
  transition: transform var(--dur) var(--ease), background 0.25s var(--ease);
}

:root[data-theme='dark'] .sidebar {
  background: rgba(16, 31, 56, 0.88);
  border-right: 2px solid #f4c95d;
}

.sidebar__head {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 10px 18px;
  border-bottom: 1px solid
    var(--color-hairline);
  margin-bottom: 16px;
}

.sidebar__logo {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.sidebar__brand {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.sidebar__name {
  font-weight: var(--w-700);
  font-size: 16px;
  letter-spacing: -0.02em;
  color: var(--color-primary);
}

.sidebar__tag {
  font-size: 11px;
  color: var(--color-ink-mute);
}

.sidebar__close {
  display: none;
  margin-left: auto;
  font-size: 26px;
  line-height: 1;
  color: var(--color-ink-mute);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  padding-top: 4px;
}

.sidebar__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  color: var(--color-ink);
  font-size: 14px;
  font-weight: var(--w-500);
  transition: background 180ms ease, color 180ms ease, border-color 180ms ease;
}

.sidebar__indicator {
  position: absolute;
  left: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 999px;
  background: transparent;
  box-shadow: none;
  transition: background 180ms ease, box-shadow 180ms ease;
}

.sidebar__icon {
  width: 19px;
  height: 19px;
  flex-shrink: 0;
  color: var(--color-ink-mute);
  transition: color 180ms ease;
}

.sidebar__item:hover {
  background: rgba(244, 201, 93, 0.07);
  color: var(--color-primary);
}

.sidebar__item:hover .sidebar__icon {
  color: var(--color-accent-strong);
}

:root[data-theme='dark'] .sidebar__item:hover {
  background: rgba(244, 201, 93, 0.06);
  color: var(--color-ink-on-dark);
}

/* Active menu: elegant yellow glow */
.sidebar__item--active {
  background: rgba(244, 201, 93, 0.18);
  border: 1px solid rgba(217, 169, 40, 0.25);
  color: var(--color-primary);
  font-weight: var(--w-600);
}

.sidebar__item--active .sidebar__icon {
  color: var(--color-accent-strong);
}

.sidebar__item--active .sidebar__indicator {
  background: var(--color-accent);
  box-shadow: var(--active-glow);
}

:root[data-theme='dark'] .sidebar__item--active {
  background: rgba(244, 201, 93, 0.12);
  border: 1px solid rgba(244, 201, 93, 0.2);
  color: #ffffff;
}

:root[data-theme='dark'] .sidebar__item--active .sidebar__icon {
  color: var(--color-accent);
}

.sidebar__foot {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 10px 0;
  border-top: 1px solid var(--color-hairline);
}

.sidebar__tagline {
  font-size: 11px;
  font-weight: var(--w-600);
  letter-spacing: 0.02em;
  color: var(--color-accent-strong);
}

.sidebar__version {
  font-size: 11px;
  color: var(--color-ink-faint);
}

:root[data-theme='dark'] .sidebar__tagline {
  color: var(--color-accent);
}

:root[data-theme='dark'] .sidebar__version {
  color: var(--color-ink-faint);
}

/* Mobile overlay */
.sidebar__overlay {
  position: fixed;
  inset: 0;
  background: rgba(7, 20, 38, 0.5);
  z-index: 35;
}

@media (min-width: 1081px) {
  .sidebar__overlay {
    display: none;
  }
}

/* Tablet + mobile: off-canvas drawer. */
@media (max-width: 1080px) {
  .sidebar {
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
  }
  .sidebar--open {
    transform: translateX(0);
  }
  .sidebar__close {
    display: block;
  }
}
</style>