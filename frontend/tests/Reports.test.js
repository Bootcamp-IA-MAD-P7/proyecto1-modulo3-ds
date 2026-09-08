import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Reports from '@/views/Reports.vue'

// Mock the service so the view tests exercise the state flow without a backend.
vi.mock('@/services/predictionService.js', () => ({
  listAssessments: vi.fn(),
  assessmentReportUrl: vi.fn(
    (id, locale = 'es') => `http://127.0.0.1:8000/assessments/${id}/report?locale=${locale}`,
  ),
}))

import { assessmentReportUrl, listAssessments } from '@/services/predictionService.js'
import { setLanguage } from '@/store.js'

const ASSESSMENT = {
  id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  patient_id: '11111111-1111-1111-1111-111111111111',
  created_at: '2026-09-07T15:00:00Z',
  prediction: 1,
  probability: 0.8,
  risk_level: 'high',
  model_name: 'Logistic Regression + RandomOverSampler',
  model_version: 'final-tuned',
}

describe('Reports view', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    setLanguage('es')
    // Re-establish the default mock implementation after resetAllMocks.
    assessmentReportUrl.mockImplementation(
      (id, locale = 'es') => `http://127.0.0.1:8000/assessments/${id}/report?locale=${locale}`,
    )
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows LOADING while fetching, then the list of downloadable reports', async () => {
    let resolveRequest
    listAssessments.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )
    const wrapper = mount(Reports)
    expect(wrapper.text()).toContain('Cargando informes…')

    resolveRequest([ASSESSMENT])
    await flushPromises()
    expect(wrapper.text()).not.toContain('Cargando informes…')
    expect(wrapper.text()).toContain('Descargar informe PDF')
  })

  it('links each assessment to its real PDF report URL (with current locale)', async () => {
    listAssessments.mockResolvedValue([ASSESSMENT])
    const wrapper = mount(Reports)
    await flushPromises()

    const link = wrapper.find('.item__action')
    expect(link.exists()).toBe(true)
    expect(link.attributes('href')).toBe(
      'http://127.0.0.1:8000/assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/report?locale=es',
    )
    expect(link.attributes('download')).toContain('informe_riskai_')
    expect(assessmentReportUrl).toHaveBeenCalledWith(ASSESSMENT.id, 'es')
  })

  it('passes the current app locale to the report URL (EN)', async () => {
    setLanguage('en')
    listAssessments.mockResolvedValue([ASSESSMENT])
    const wrapper = mount(Reports)
    await flushPromises()

    expect(
      wrapper.find('.item__action').attributes('href'),
    ).toBe(
      'http://127.0.0.1:8000/assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/report?locale=en',
    )
    expect(assessmentReportUrl).toHaveBeenCalledWith(ASSESSMENT.id, 'en')
  })

  it('shows the EMPTY state when no reports are available', async () => {
    listAssessments.mockResolvedValue([])
    const wrapper = mount(Reports)
    await flushPromises()
    expect(wrapper.text()).toContain('Sin informes disponibles')
  })

  it('shows the ERROR state with a friendly message when the API fails', async () => {
    listAssessments.mockRejectedValue({
      message: 'No se ha podido conectar con el almacenamiento.',
    })
    const wrapper = mount(Reports)
    await flushPromises()
    expect(wrapper.text()).toContain('No se ha podido conectar con el almacenamiento.')
    expect(wrapper.text()).toContain('Reintentar')
  })

  it('reloads reports when Retry is clicked after an error', async () => {
    listAssessments.mockRejectedValueOnce({
      message: 'No se ha podido conectar con el almacenamiento.',
    })
    listAssessments.mockResolvedValueOnce([ASSESSMENT])
    const wrapper = mount(Reports)
    await flushPromises()
    expect(wrapper.text()).toContain('Reintentar')

    await wrapper.find('.state-box__retry').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Descargar informe PDF')
    expect(listAssessments).toHaveBeenCalledTimes(2)
  })
})