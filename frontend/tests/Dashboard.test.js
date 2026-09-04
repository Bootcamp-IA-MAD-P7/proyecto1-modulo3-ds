import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dashboard from '@/views/Dashboard.vue'
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

  it('mounts and renders the dashboard intro + patient assessment (no neural visualization)', () => {
    wrapper = mount(Dashboard)
    expect(wrapper.text()).toContain('F5 RISKAI')
    expect(wrapper.text()).toContain('Evaluación de riesgo de ictus')
    expect(wrapper.text()).toContain('Patient Assessment')
    // The 3D brain lives in the Análisis view; the placeholder is gone from Inicio.
    expect(wrapper.findComponent(NeuralVisualization).exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Neural Visualization')
  })

  it('does not render any neural placeholder text on the Inicio view', () => {
    wrapper = mount(Dashboard)
    expect(wrapper.text()).not.toContain('coming soon')
    expect(wrapper.text()).not.toContain('Brain3D')
    expect(wrapper.text()).not.toContain('Integración futura')
    expect(wrapper.text()).not.toContain('Compatible con Vue')
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