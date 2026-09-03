<script setup>
/**
 * App header: F5 RiskAI identity, current module, theme toggle, language
 * selector (ES|EN), notifications and a visual user avatar/dropdown (UI only).
 * Theme + language are global (store.js) and persist across reloads.
 */
import { ref } from 'vue'
import { t, state, toggleTheme, setLanguage } from '@/store.js'

defineEmits(['toggle-sidebar'])

const moduleName = ref(t('module'))
const userName = 'Dra. M. Ruiz'
const notificationDot = true

const profileOpen = ref(false)

function switchLang(lang) {
  setLanguage(lang)
}
</script>

<template>
  <header class="app-header">
    <div class="app-header__inner">
      <div class="app-header__left">
        <button
          class="app-header__menu"
          type="button"
          :aria-label="t('notifications')"
          @click="$emit('toggle-sidebar')"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" class="app-header__menu-icon">
            <path
              d="M3 6h18M3 12h18M3 18h18"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>

        <div class="app-header__module">
          <span class="app-header__brand">F5 RISKAI</span>
          <span class="app-header__title">{{ t('module') }}</span>
        </div>
      </div>

      <div class="app-header__right">
        <!-- Language selector: ES | EN -->
        <div class="app-header__lang" role="group" aria-label="Language">
          <button
            type="button"
            class="app-header__lang-btn"
            :class="{ 'is-active': state.language === 'es' }"
            @click="switchLang('es')"
          >
            ES
          </button>
          <span class="app-header__lang-sep" aria-hidden="true">|</span>
          <button
            type="button"
            class="app-header__lang-btn"
            :class="{ 'is-active': state.language === 'en' }"
            @click="switchLang('en')"
          >
            EN
          </button>
        </div>

        <!-- Theme toggle: light / dark -->
        <button
          class="app-header__icon-btn"
          type="button"
          :aria-label="state.theme === 'dark' ? 'Light mode' : 'Dark mode'"
          :title="state.theme === 'dark' ? 'Light mode' : 'Dark mode'"
          @click="toggleTheme"
        >
          <svg v-if="state.theme === 'dark'" viewBox="0 0 24 24" aria-hidden="true" class="app-header__icon">
            <circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="1.7" />
            <path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m9.9 9.9 1.4 1.4m0-12.8-1.4 1.4M7 16.4l-1.4 1.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
          </svg>
          <svg v-else viewBox="0 0 24 24" aria-hidden="true" class="app-header__icon">
            <path d="M12 3a9 9 0 1 0 9 9c0-.5-.4-1-1-1h-1a4 4 0 0 1-4-4V6a5 5 0 0 1 5-5h1a1 1 0 0 0 0-2 9 9 0 0 0-9 0h-1Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
          </svg>
        </button>

        <button class="app-header__icon-btn" type="button" :aria-label="t('notifications')">
          <svg viewBox="0 0 24 24" aria-hidden="true" class="app-header__icon">
            <path
              d="M12 3a5.5 5.5 0 0 0-5.5 5.5v2.6L5 15h14l-1.5-3.9V8.5A5.5 5.5 0 0 0 12 3Zm-2.5 13.5a2.5 2.5 0 0 0 5 0"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span v-if="notificationDot" class="app-header__dot" aria-hidden="true"></span>
        </button>

        <div class="app-header__profile">
          <button
            class="app-header__profile-btn"
            type="button"
            aria-haspopup="true"
            :aria-expanded="profileOpen"
            @click="profileOpen = !profileOpen"
          >
            <span class="app-header__avatar" aria-hidden="true">MR</span>
            <span class="app-header__profile-name">{{ userName }}</span>
            <svg viewBox="0 0 24 24" aria-hidden="true" class="app-header__chevron">
              <path
                d="M6 9l6 6 6-6"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>

          <div v-if="profileOpen" class="app-header__dropdown" data-testid="profile-dropdown">
            <div class="app-header__dropdown-head">
              <span class="app-header__dropdown-name">{{ userName }}</span>
              <span class="app-header__dropdown-role">{{ t('profileRole') }}</span>
            </div>
            <hr class="app-header__divider" />
            <button type="button" class="app-header__dropdown-item">{{ t('profilePerfil') }}</button>
            <button type="button" class="app-header__dropdown-item">{{ t('profileAjustes') }}</button>
            <button type="button" class="app-header__dropdown-item">{{ t('cerrarSesion') }}</button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--color-hairline);
  position: sticky;
  top: 0;
  z-index: 30;
  height: var(--header-height);
  transition: background 0.25s var(--ease);
}

:root[data-theme='dark'] .app-header {
  background: rgba(7, 20, 38, 0.9);
}

.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 30px;
  gap: 16px;
}

.app-header__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.app-header__menu {
  display: none;
  color: var(--color-ink-mute);
  padding: 6px;
  border-radius: var(--radius-sm);
}

.app-header__menu:hover {
  background: rgba(244, 201, 93, 0.1);
  color: var(--color-primary);
}

.app-header__menu-icon {
  width: 22px;
  height: 22px;
}

.app-header__module {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}

.app-header__brand {
  font-size: 11px;
  font-weight: var(--w-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent-strong);
}

.app-header__title {
  font-size: 15px;
  font-weight: var(--w-600);
  color: var(--color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-header__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Language selector ES | EN */
.app-header__lang {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  background: var(--color-card);
}

.app-header__lang-btn {
  font-size: 12px;
  font-weight: var(--w-700);
  letter-spacing: 0.02em;
  color: var(--color-ink-mute);
  padding: 3px 6px;
  border-radius: var(--radius-sm);
  transition: color 180ms ease, background 180ms ease;
}

.app-header__lang-btn.is-active {
  color: var(--color-on-accent);
  background: var(--color-accent);
}

.app-header__lang-sep {
  color: var(--color-ink-faint);
  font-size: 12px;
}

.app-header__icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--color-ink-mute);
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}

.app-header__icon-btn:hover {
  background: rgba(244, 201, 93, 0.12);
  color: var(--color-accent-strong);
}

.app-header__icon {
  width: 21px;
  height: 21px;
}

.app-header__dot {
  position: absolute;
  top: 9px;
  right: 10px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-accent);
  border: 2px solid var(--color-card);
}

.app-header__profile {
  position: relative;
}

.app-header__profile-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 8px;
  border-radius: var(--radius-pill);
  transition: background var(--dur) var(--ease);
}

.app-header__profile-btn:hover {
  background: rgba(244, 201, 93, 0.1);
}

.app-header__avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #172033 0%, var(--color-accent-strong) 100%);
  color: #fff;
  font-size: 13px;
  font-weight: var(--w-600);
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-header__profile-name {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.app-header__chevron {
  width: 15px;
  height: 15px;
  color: var(--color-ink-faint);
}

.app-header__dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  min-width: 190px;
  background: var(--color-card);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 8px;
  z-index: 50;
  animation: fadeIn 0.16s var(--ease);
}

.app-header__dropdown-head {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
}

.app-header__dropdown-name {
  font-size: 13px;
  font-weight: var(--w-600);
  color: var(--color-primary);
}

.app-header__dropdown-role {
  font-size: 12px;
  color: var(--color-ink-mute);
}

.app-header__divider {
  border: none;
  border-top: 1px solid var(--color-hairline);
  margin: 6px 0;
}

.app-header__dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--color-primary);
  transition: background var(--dur) var(--ease);
}

.app-header__dropdown-item:hover {
  background: rgba(244, 201, 93, 0.12);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1080px) {
  .app-header__menu {
    display: flex;
  }
}

@media (max-width: 640px) {
  .app-header__inner {
    padding: 0 16px;
  }
  .app-header__profile-name,
  .app-header__chevron {
    display: none;
  }
  .app-header__profile-btn {
    padding: 4px;
  }
  .app-header__brand {
    display: none;
  }
}
</style>