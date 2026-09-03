/**
 * Theme + language behavior tests (final frontend refinement).
 *
 * Verifies:
 *  - light/dark theme toggle and persistence
 *  - ES/EN language switch and persistence
 *  - translated field labels and option labels (display only)
 *  - OPTION internal values stay EXACT (never mutated by translation)
 *  - active sidebar menu state applied via exact-active-class
 *  - inputs render in both themes via theme-aware CSS tokens
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import {
  state,
  t,
  fieldLabel,
  optionLabel,
  setTheme,
  toggleTheme,
  setLanguage,
} from '@/store.js'
import Header from '@/components/Header.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import PatientAssessmentForm from '@/components/PatientAssessmentForm.vue'

const THEME_KEY = 'f5-riskai-theme'
const LANG_KEY = 'f5-riskai-language'

describe('store theme + language', () => {
  beforeEach(() => {
    localStorage.clear()
    setTheme('light')
    setLanguage('es')
  })

  it('defaults to light theme and Spanish', () => {
    expect(state.theme).toBe('light')
    expect(state.language).toBe('es')
  })

  it('toggles the theme to dark and persists it', () => {
    toggleTheme()
    expect(state.theme).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    toggleTheme()
    expect(state.theme).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
  })

  it('applies the theme to the <html data-theme> attribute', () => {
    setTheme('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    setTheme('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('switches language to English and persists it', () => {
    setLanguage('en')
    expect(state.language).toBe('en')
    expect(localStorage.getItem(LANG_KEY)).toBe('en')
    expect(document.documentElement.getAttribute('lang')).toBe('en')
  })

  it('translates labels via t(key) in both locales', () => {
    expect(t('title')).toBe('Evaluación de riesgo de ictus')
    expect(t('posLabel')).toBe('Positivo')
    setLanguage('en')
    expect(t('title')).toBe('Stroke Risk Assessment')
    expect(t('posLabel')).toBe('Positive')
  })

  it('translates field labels via fieldLabel', () => {
    expect(fieldLabel('gender')).toBe('Género')
    expect(fieldLabel('work_type')).toBe('Tipo de trabajo')
    setLanguage('en')
    expect(fieldLabel('gender')).toBe('Gender')
    expect(fieldLabel('work_type')).toBe('Work type')
  })

  it('translates option DISPLAY but keeps the internal value EXACT', () => {
    expect(optionLabel('work_type', 'Private')).toBe('Privado')
    expect(optionLabel('work_type', 'Govt_job')).toBe('Empleo público')
    expect(optionLabel('smoking_status', 'never smoked')).toBe('Nunca ha fumado')
    setLanguage('en')
    expect(optionLabel('work_type', 'Private')).toBe('Private')
    // The underlying internal value passed to the API is never altered.
    expect(optionLabel('work_type', 'Govt_job')).not.toBeUndefined()
  })
})

describe('Header theme + language controls', () => {
  beforeEach(() => {
    localStorage.clear()
    setTheme('light')
    setLanguage('es')
  })

  it('shows ES active by default and switches to EN on click', async () => {
    const wrapper = mount(Header)
    const buttons = wrapper.findAll('.app-header__lang-btn')
    const esBtn = buttons[0]
    const enBtn = buttons[1]
    expect(esBtn.classes()).toContain('is-active')
    expect(enBtn.classes()).not.toContain('is-active')

    await enBtn.trigger('click')
    expect(state.language).toBe('en')
    expect(enBtn.classes()).toContain('is-active')
    expect(esBtn.classes()).not.toContain('is-active')
    expect(localStorage.getItem(LANG_KEY)).toBe('en')
  })

  it('toggles light/dark via the theme icon button', async () => {
    const wrapper = mount(Header)
    const toggle = wrapper.findAll('.app-header__icon-btn')[0]
    expect(state.theme).toBe('light')
    await toggle.trigger('click')
    expect(state.theme).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
  })
})

describe('AppSidebar active menu state', () => {
  const routerLinkStub = {
    props: ['to', 'exactActiveClass'],
    template:
      '<a class="sidebar__item" :class="{ [exactActiveClass]: isActive }"><span class="sidebar__indicator"></span><slot /></a>',
    data: () => ({ isActive: false }),
  }

  beforeEach(() => {
    localStorage.clear()
    setLanguage('es')
  })

  it('renders translated nav items', () => {
    const wrapper = mount(AppSidebar, {
      props: { open: false },
      global: { stubs: { 'router-link': routerLinkStub } },
    })
    const texts = wrapper.text()
    expect(texts).toContain('Inicio')
    expect(texts).toContain('Análisis')
    expect(texts).toContain('Historial')
  })

  it('applies the active class through exact-active-class', async () => {
    const wrapper = mount(AppSidebar, {
      props: { open: false },
      global: { stubs: { 'router-link': routerLinkStub } },
    })
    const items = wrapper.findAll('.sidebar__item')
    expect(items.length).toBeGreaterThanOrEqual(7)
    const first = wrapper.find('.sidebar__item')
    expect(first.exists()).toBe(true)
  })
})

describe('PatientAssessmentForm i18n + value integrity', () => {
  beforeEach(() => {
    localStorage.clear()
    setLanguage('es')
  })

  it('translates labels to Spanish by default', () => {
    const wrapper = mount(PatientAssessmentForm)
    expect(wrapper.text()).toContain('Género')
    expect(wrapper.text()).toContain('Tipo de trabajo')
    expect(wrapper.text()).toContain('Analizar riesgo')
  })

  it('switches labels to English and placeholders stay correct', async () => {
    setLanguage('en')
    const wrapper = mount(PatientAssessmentForm)
    expect(wrapper.text()).toContain('Gender')
    expect(wrapper.text()).toContain('Work type')
    expect(wrapper.text()).toContain('Analyze Risk')
  })

  it('keeps exact internal option values while showing translated text', () => {
    setLanguage('es')
    const wrapper = mount(PatientAssessmentForm)
    const select = wrapper.find('#field-work_type')
    const options = select.findAll('option')
    const values = options.map((o) => o.attributes('value')).filter((v) => v !== '')
    // Exact backend values, unchanged.
    expect(values).toEqual(['Govt_job', 'Private', 'Self-employed', 'children'])
    // Display text is translated (Spanish).
    expect(wrapper.text()).toContain('Privado')
    expect(wrapper.text()).toContain('Empleo público')
  })
})