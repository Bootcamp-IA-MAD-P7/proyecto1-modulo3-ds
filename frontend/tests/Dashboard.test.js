import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dashboard from '@/views/Dashboard.vue'
import Brain3D from '@/components/Brain3D.vue'
import NeuralVisualization from '@/components/NeuralVisualization.vue'

// Mock the service so tests exercise the component orchestration without a backend.
vi.mock('@/services/predictionService.js', () => ({
  predictStroke: vi.fn(),
}))

import { predictStroke } from '@/services/predictionService.js'

const VALID = {
  gender: 'Female',
  age: 45,
  hypertension: 0,
  heart_disease: 1,
  ever_married: 'Yes',
  work_type: 'Private',
  Residence_type: 'Urban',
  avg_glucose_level: 100,
  bmi: 25,
  smoking_status: 'never smoked',
}

function fillValidForm(wrapper) {
  const form = wrapper.findComponent({ name: 'PatientAssessmentForm' })
  // Mutate each reactive property (the model is a `const reactive(...)`).
  for (const [k, v] of Object.entries(VALID)) {
    form.vm.model[k] = String(v)
  }
  return form
}

async function submitForm(wrapper) {
  await fillValidForm(wrapper)
    .find('form')
    .trigger('submit')
  await flushPromises()
}

describe('Dashboard', () => {
  let wrapper

  beforeEach(() => {
    vi.resetAllMocks()
    document.body.innerHTML = ''
  })

  it('mounts and renders the intro + patient assessment + Brain3D neural visualization', () => {
    wrapper = mount(Dashboard)
    expect(wrapper.text()).toContain('F5 RISKAI')
    expect(wrapper.text()).toContain('Evaluación de riesgo de ictus')
    expect(wrapper.text()).toContain('Patient Assessment')
    // The 3D brain now lives on the Inicio view (replacing the SVG placeholder).
    expect(wrapper.findComponent(Brain3D).exists()).toBe(true)
    expect(wrapper.findComponent(NeuralVisualization).exists()).toBe(false)
  })

  it('renders the Análisis panel (Brain3D) with the analysis summary on the Inicio view', () => {
    wrapper = mount(Dashboard)
    // Right column panel is simply titled "Análisis" — no NEURAL VISUALIZATION
    // eyebrow, no "Cerebro 3D" title, no NEURAL SYSTEM text anymore.
    expect(wrapper.find('.panel--brain .card-head__title').text()).toBe('Análisis')
    expect(wrapper.text()).not.toContain('Neural Visualization')
    expect(wrapper.text()).not.toContain('Cerebro 3D')
    expect(wrapper.text()).not.toContain('NEURAL SYSTEM')
    // Analysis summary block: risk + probability + model + input labels
    expect(wrapper.text()).toContain('Resumen del análisis')
    expect(wrapper.text()).toContain('Logistic Regression')
    expect(wrapper.text()).toContain('Modelo')
    expect(wrapper.text()).toContain('Entrada')
    // The old abstract SVG placeholder copy is gone from Inicio.
    expect(wrapper.text()).not.toContain('coming soon')
    expect(wrapper.text()).not.toContain('Integración futura')
  })

  it('shows the loading state during the prediction request', async () => {
    // Deterministic deferred promise: loading stays true until we resolve it.
    let resolveRequest
    predictStroke.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )
    wrapper = mount(Dashboard)
    await fillValidForm(wrapper).find('form').trigger('submit')
    // Wait for the submit -> handleSubmit -> loading=true flush.
    await nextTicks()

    expect(predictStroke).toHaveBeenCalled()

    // The result area should show the loading state, not a result yet.
    const loadingEl = wrapper.find('.loading')
    expect(loadingEl.exists()).toBe(true)
    expect(loadingEl.find('.loading__text').text()).toContain('Analizando riesgo...')
    expect(wrapper.find('.result').exists()).toBe(false)

    // Resolve so the dashboard settles.
    resolveRequest({ prediction: 0, probability: 0.02 })
    await flushPromises()
  })

async function nextTicks(n = 3) {
  for (let i = 0; i < n; i += 1) {
    // eslint-disable-next-line no-await-in-loop
    await new Promise((r) => setTimeout(r, 0))
  }
}

  it('does not issue a request when the form is invalid', async () => {
    wrapper = mount(Dashboard)
    // Submit with the default (empty) model -> invalid
    await wrapper.findComponent({ name: 'PatientAssessmentForm' }).find('form').trigger('submit')
    await flushPromises()
    expect(predictStroke).not.toHaveBeenCalled()
  })

  it('displays the prediction result with probability as percentage', async () => {
    predictStroke.mockResolvedValue({ prediction: 0, probability: 0.018580961296622237 })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.text()).toContain('Negativo')
    expect(wrapper.text()).toContain('1.86%')
  })

  it('displays positive prediction for prediction=1', async () => {
    predictStroke.mockResolvedValue({ prediction: 1, probability: 0.85 })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.text()).toContain('Positivo')
    expect(wrapper.text()).toContain('85.00%')
  })

  it('shows an error message when the API fails', async () => {
    predictStroke.mockRejectedValue({
      message: 'No se pudo conectar con el servicio de predicción.',
    })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.text()).toContain('No se pudo conectar')
  })

  it('opens and closes the risk analysis modal from the result', async () => {
    predictStroke.mockResolvedValue({ prediction: 0, probability: 0.02 })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)

    // The modal is Teleported to <body>, so assert against the document.
    expect(document.body.textContent).not.toContain('Factores relevantes')

    // Open via "Ver análisis"
    const openBtn = wrapper
      .findAll('button')
      .find((b) => b.text() === 'Ver análisis')
    expect(openBtn).toBeTruthy()
    await openBtn.trigger('click')
    await flushPromises()

    expect(document.body.textContent).toContain('Factores relevantes introducidos')

    // Close via "Cerrar"
    const closeBtn = [
      ...document.querySelectorAll('button'),
    ].find((b) => b.textContent.trim() === 'Cerrar')
    expect(closeBtn).toBeTruthy()
    closeBtn.click()
    await flushPromises()
    expect(document.body.textContent).not.toContain('Factores relevantes')
  })

  it('renders the responsive dashboard layout (top row + full-width result + info row)', () => {
    wrapper = mount(Dashboard)
    expect(wrapper.find('.dashboard__top').exists()).toBe(true)
    expect(wrapper.find('.panel--result').exists()).toBe(true)
    expect(wrapper.find('.dashboard__info').exists()).toBe(true)
  })
})

describe('Dashboard brain risk levels (driven by the REAL model probability)', () => {
  let wrapper

  beforeEach(() => {
    vi.resetAllMocks()
    document.body.innerHTML = ''
  })

  async function submitWithProbability(p) {
    predictStroke.mockResolvedValue({
      prediction: p >= 0.5 ? 1 : 0,
      probability: p,
    })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
  }

  it('mapping: 0.20 -> LOW risk (green) in both Brain3D and summary', async () => {
    await submitWithProbability(0.2)
    const brain = wrapper.findComponent(Brain3D)
    expect(brain.props('state')).toBe('low')
    expect(brain.props('percent')).toBe(20)
    expect(brain.find('.brain__chip--low').exists()).toBe(true)
    // Summary status shows the same level with a text label (not just color).
    expect(wrapper.text()).toContain('RIESGO BAJO')
    expect(wrapper.find('.dashboard__summary .dashboard__summary-value').text()).toBe('20%')
  })

  it('mapping: 0.30 -> MEDIUM risk', async () => {
    await submitWithProbability(0.3)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('medium')
    expect(wrapper.text()).toContain('RIESGO MEDIO')
  })

  it('mapping: 0.45 -> MEDIUM risk', async () => {
    await submitWithProbability(0.45)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('medium')
    expect(wrapper.text()).toContain('RIESGO MEDIO')
  })

  it('mapping: 0.50 -> HIGH risk (boundary)', async () => {
    await submitWithProbability(0.5)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('high')
    expect(wrapper.text()).toContain('RIESGO ELEVADO')
  })

  it('mapping: 0.72 -> HIGH risk with the real 72% probability', async () => {
    await submitWithProbability(0.72)
    const brain = wrapper.findComponent(Brain3D)
    expect(brain.props('state')).toBe('high')
    expect(brain.props('percent')).toBe(72)
    expect(wrapper.find('.dashboard__summary .dashboard__summary-value').text()).toBe('72%')
    expect(wrapper.text()).toContain('RIESGO ELEVADO')
  })

  it('summary tone and Brain3D state always share the same risk level (single source)', async () => {
    await submitWithProbability(0.72)
    const brainState = wrapper.findComponent(Brain3D).props('state')
    const tone = wrapper.find('.astatus').classes().find((c) => c.startsWith('astatus--'))
    const toneByState = { low: 'astatus--success', medium: 'astatus--info', high: 'astatus--error' }
    expect(tone).toBe(toneByState[brainState])
  })

  it('issues exactly one prediction request for the whole flow (no duplicates)', async () => {
    await submitWithProbability(0.72)
    expect(predictStroke).toHaveBeenCalledTimes(1)
  })

  it('stays neutral (no risk level, no invented probability) when the API fails', async () => {
    predictStroke.mockRejectedValue({
      message: 'No se pudo conectar con el servicio de predicción.',
    })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('idle')
    expect(wrapper.text()).not.toContain('RIESGO')
  })

  it('stays neutral when the probability is missing or out of range', async () => {
    // Out of 0..1 range.
    predictStroke.mockResolvedValue({ prediction: 0, probability: 1.5 })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('idle')
    expect(wrapper.find('.dashboard__summary .dashboard__summary-value').text()).toBe('0%')

    // Missing probability.
    predictStroke.mockResolvedValue({ prediction: 1 })
    wrapper = mount(Dashboard)
    await submitForm(wrapper)
    expect(wrapper.findComponent(Brain3D).props('state')).toBe('idle')
    expect(wrapper.text()).not.toContain('RIESGO')
  })
})