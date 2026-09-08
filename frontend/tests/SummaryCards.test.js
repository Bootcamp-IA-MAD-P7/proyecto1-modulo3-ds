import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SummaryCards from '@/components/SummaryCards.vue'
import { setLanguage } from '@/store.js'

// Mock the service: SummaryCards reads real API data (patients, assessments,
// health); tests drive the states without a backend.
vi.mock('@/services/predictionService.js', () => ({
  listPatients: vi.fn(),
  listAssessments: vi.fn(),
  checkHealth: vi.fn(),
}))

import {
  listPatients,
  listAssessments,
  checkHealth,
} from '@/services/predictionService.js'

const PATIENTS = [
  { id: '11111111-1111-1111-1111-111111111111', last_assessment: { probability: 0.154 } },
  { id: '22222222-2222-2222-2222-222222222222', last_assessment: { probability: 0.524 } },
]

const ASSESSMENTS = [
  { id: 'a1', probability: 0.154 },
  { id: 'a2', probability: 0.524 },
  { id: 'a3', probability: 0.26 },
]

function values(wrapper) {
  return wrapper.findAll('.summary__value').map((el) => el.text())
}

function hints(wrapper) {
  return wrapper.findAll('.summary__hint').map((el) => el.text())
}

describe('SummaryCards', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    setLanguage('es')
  })

  it('shows a discreet loading state while the statistics are being fetched', async () => {
    let resolvePatients
    listPatients.mockReturnValue(
      new Promise((resolve) => {
        resolvePatients = resolve
      }),
    )
    listAssessments.mockResolvedValue(ASSESSMENTS)
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    const vals = values(wrapper)
    // LOADING: discreet '…' on the three dynamic cards; model stays static.
    expect(vals[0]).toBe('…')
    expect(vals[1]).toBe('…')
    expect(vals[2]).toBe('Logistic Regression')
    expect(vals[3]).toBe('…')

    resolvePatients(PATIENTS)
    await flushPromises()
    expect(values(wrapper)[0]).toBe('2')
  })

  it('shows the REAL patient count and REAL average risk (SUCCESS)', async () => {
    listPatients.mockResolvedValue(PATIENTS)
    listAssessments.mockResolvedValue(ASSESSMENTS)
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()

    const vals = values(wrapper)
    expect(vals[0]).toBe('2') // distinct patients from GET /patients
    expect(vals[1]).toBe('31.3%') // (15.4 + 52.4 + 26.0) / 3 = 31.266… -> 31.3
    expect(vals[2]).toBe('Logistic Regression')
    expect(vals[3]).toBe('En línea')

    const h = hints(wrapper)
    expect(h[0]).toBe('Pacientes registrados')
    expect(h[1]).toBe('Promedio de las evaluaciones')
    expect(h[2]).toBe('Modelo final optimizado')
    expect(h[3]).toBe('')
  })

  it('shows the EMPTY state with zero patients and no assessments', async () => {
    listPatients.mockResolvedValue([])
    listAssessments.mockResolvedValue([])
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()

    const vals = values(wrapper)
    expect(vals[0]).toBe('0')
    expect(vals[1]).toBe('—')

    const h = hints(wrapper)
    expect(h[0]).toBe('Sin pacientes registrados')
    expect(h[1]).toBe('Sin evaluaciones registradas')

    // The old placeholder texts are gone for good.
    expect(wrapper.text()).not.toContain('Sin base de datos')
    expect(wrapper.text()).not.toContain('Sin datos históricos')
  })

  it('shows a brief, professional error without breaking the dashboard (ERROR)', async () => {
    listPatients.mockRejectedValue({ message: 'Almacenamiento no disponible' })
    listAssessments.mockRejectedValue({ message: 'Almacenamiento no disponible' })
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()

    const vals = values(wrapper)
    expect(vals[0]).toBe('—')
    expect(vals[1]).toBe('—')
    expect(hints(wrapper)[0]).toBe('No se pudieron cargar las estadísticas.')
    expect(hints(wrapper)[1]).toBe('No se pudieron cargar las estadísticas.')
    // The system card is independent: the API is alive even if storage is down.
    expect(vals[3]).toBe('En línea')
  })

  it('marks the system as unavailable when the existing health check fails', async () => {
    listPatients.mockResolvedValue([])
    listAssessments.mockResolvedValue([])
    checkHealth.mockResolvedValue(false)

    const wrapper = mount(SummaryCards)
    await flushPromises()
    expect(values(wrapper)[3]).toBe('No disponible')
  })

  it('averages only valid stored probabilities (defensive filtering)', async () => {
    listPatients.mockResolvedValue([])
    listAssessments.mockResolvedValue([
      { probability: 0.5 },
      { probability: 0.25 },
      { probability: null },
      { probability: 'n/a' },
      {},
    ])
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()
    expect(values(wrapper)[1]).toBe('37.5%') // (0.50 + 0.25) / 2
    expect(hints(wrapper)[1]).toBe('Promedio de las evaluaciones')
  })

  it('refetches the statistics when refreshKey changes (auto-update, no reload)', async () => {
    listPatients.mockResolvedValue(PATIENTS)
    listAssessments.mockResolvedValue(ASSESSMENTS)
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()
    expect(values(wrapper)[0]).toBe('2')
    expect(values(wrapper)[1]).toBe('31.3%')

    // A new persisted assessment arrives: patient 3 with a low-risk evaluation.
    listPatients.mockResolvedValue([
      ...PATIENTS,
      { id: '33333333-3333-3333-3333-333333333333', last_assessment: { probability: 0.05 } },
    ])
    listAssessments.mockResolvedValue([...ASSESSMENTS, { id: 'a4', probability: 0.05 }])

    await wrapper.setProps({ refreshKey: 1 })
    await flushPromises()

    expect(listPatients).toHaveBeenCalledTimes(2)
    expect(listAssessments).toHaveBeenCalledTimes(2)
    expect(values(wrapper)[0]).toBe('3')
    // (15.4 + 52.4 + 26.0 + 5.0) / 4 = 24.7
    expect(values(wrapper)[1]).toBe('24.7%')
  })

  it('keeps the cards translated in EN', async () => {
    setLanguage('en')
    listPatients.mockResolvedValue(PATIENTS)
    listAssessments.mockResolvedValue(ASSESSMENTS)
    checkHealth.mockResolvedValue(true)

    const wrapper = mount(SummaryCards)
    await flushPromises()

    const h = hints(wrapper)
    expect(h[0]).toBe('Registered patients')
    expect(h[1]).toBe('Average of assessments')
    expect(values(wrapper)[0]).toBe('2')
    expect(values(wrapper)[1]).toBe('31.3%')

    // EMPTY copies in EN too.
    listPatients.mockResolvedValue([])
    listAssessments.mockResolvedValue([])
    await wrapper.setProps({ refreshKey: 1 })
    await flushPromises()
    expect(hints(wrapper)[0]).toBe('No patients registered')
    expect(hints(wrapper)[1]).toBe('No assessments registered')
  })
})