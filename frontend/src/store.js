/**
 * F5 RiskAI - reactive UI store: theme (light/dark) + language (es/en).
 *
 * - Theme persisted in localStorage under "f5-riskai-theme" (default "light").
 * - Language persisted under "f5-riskai-language" (default "es").
 * - Changing theme/language updates the document immediately (no reload).
 * - Provides t(key) for UI copy, fieldLabel(key) and optionLabel(field, value)
 *   that translate ONLY presentation while preserving API internal values.
 */
import { reactive, computed } from 'vue'
import {
  translations,
  fieldLabels,
  optionLabels,
} from './i18n/translations.js'

const THEME_KEY = 'f5-riskai-theme'
const LANG_KEY = 'f5-riskai-language'

function read(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* storage unavailable: keep in-memory state */
  }
}

const state = reactive({
  theme: read(THEME_KEY, 'light') === 'dark' ? 'dark' : 'light',
  language: read(LANG_KEY, 'es') === 'en' ? 'en' : 'es',
})

export { state }

/** Framework translations for the active locale. */
const bundle = computed(() => translations[state.language])

/** Resolve a dotted/nested key from the active bundle. */
export function t(key) {
  return key.split('.').reduce((acc, part) => (acc ? acc[part] : undefined), bundle.value) ?? key
}

/** Translate a field label (by field definition key). */
export function fieldLabel(fieldKey) {
  const map = fieldLabels[fieldKey]
  return (map && map[state.language]) || fieldKey
}

/**
 * Translate a select option for display. `fieldKey` targets the option map,
 * `value` is the exact internal value the API expects.
 * Always returns a display string; the internal `value` is never changed.
 */
export function optionLabel(fieldKey, value) {
  const map = optionLabels[fieldKey] && optionLabels[fieldKey][value]
  return (map && map[state.language]) ?? value
}

/** Toggle theme and persist. */
export function setTheme(theme) {
  const next = theme === 'dark' ? 'dark' : 'light'
  state.theme = next
  write(THEME_KEY, next)
  applyTheme()
}

export function toggleTheme() {
  setTheme(state.theme === 'dark' ? 'light' : 'dark')
}

/** Toggle language (es/en) and persist. */
export function setLanguage(lang) {
  const next = lang === 'en' ? 'en' : 'es'
  state.language = next
  write(LANG_KEY, next)
  applyLanguage()
}

export function toggleLanguage() {
  setLanguage(state.language === 'en' ? 'es' : 'en')
}

/** Apply current theme to <html data-theme>. */
export function applyTheme() {
  document.documentElement.setAttribute('data-theme', state.theme)
}

/** Apply current language to <html lang>. */
export function applyLanguage() {
  document.documentElement.setAttribute('lang', state.language)
}

/** Apply both on boot (avoids a flash on reload). */
export function initThemeAndLanguage() {
  applyTheme()
  applyLanguage()
}

export function useStore() {
  return { state, t, fieldLabel, optionLabel }
}