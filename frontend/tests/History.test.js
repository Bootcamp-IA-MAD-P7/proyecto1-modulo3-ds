import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import History from '@/views/History.vue'

// Mock the service so the view tests exercise the state flow without a backend.
vi.mock('@/services/predictionService.js', () => ({
  listAssessments: vi.fn(),
}))

import { listAssessments } from '@/services/predictionService.js'

const ASSESSMENTS = [
  {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    patient_id: '11111111-1111-1111-1111-111111111111',
    created_at: '2026-09-07T15:00:00Z',
    prediction: 1,
    probability: 0.8,
    risk_level: 'high',
    model_name: 'Logistic Regression + RandomOverSampler',
    model_version: 'final-tuned',
  },
  {
    id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    patient_id: '11111111-1111-1111-1111-111111111111',
    created_at: '2026-09-07T09:00:00Z',
    prediction: 0,
    probability: 0.2,
    risk_level: 'low',
    model_name: 'Logistic Regression + RandomOverSampler',
    model_version: 'final-tuned',
  },
]

describe('History view', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows LOADING while fetching, then the evaluations list', async () => {
    let resolveRequest
    listAssessments.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )
    const wrapper = mount(History)
    expect(wrapper.text()).toContain('Cargando evaluaciones…')

    resolveRequest(ASSESSMENTS)
    await flushPromises()
    expect(wrapper.text()).not.toContain('Cargando evaluaciones…')
  })

  it('renders every stored assessment with its real probability and level', async () => {
    listAssessments.mockResolvedValue(ASSESSMENTS)
    const wrapper = mount(History)
    await flushPromises()

    expect(wrapper.text()).toContain('RIESGO ELEVADO')
    expect(wrapper.text()).toContain('80.0%')
    expect(wrapper.text()).toContain('Riesgo estimado')
    expect(wrapper.text()).toContain('RIESGO BAJO')
    expect(wrapper.text()).toContain('20.0%')
    expect(wrapper.text()).toContain('Sin indicios de riesgo')
  })

  it('shows the EMPTY state when no evaluations are stored', async () => {
    listAssessments.mockResolvedValue([])
    const wrapper = mount(History)
    await flushPromises()
    expect(wrapper.text()).toContain('Sin evaluaciones registradas')
  })

  it('shows the ERROR state with a friendly message when the API fails', async () => {
    listAssessments.mockRejectedValue({
      message: 'No se ha podido conectar con el almacenamiento.',
    })
    const wrapper = mount(History)
    await flushPromises()
    expect(wrapper.text()).toContain('No se ha podido conectar con el almacenamiento.')
    expect(wrapper.text()).toContain('Reintentar')
  })
})