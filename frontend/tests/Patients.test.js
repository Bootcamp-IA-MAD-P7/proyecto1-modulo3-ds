import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Patients from '@/views/Patients.vue'

// Mock the service so the view tests exercise the state flow without a backend.
vi.mock('@/services/predictionService.js', () => ({
  listPatients: vi.fn(),
}))

import { listPatients } from '@/services/predictionService.js'

const PATIENT = {
  id: '11111111-1111-1111-1111-111111111111',
  created_at: '2026-09-07T12:30:00Z',
  gender: 'Female',
  age: 45,
  hypertension: 0,
  heart_disease: 1,
  ever_married: 'Yes',
  work_type: 'Private',
  residence_type: 'Urban',
  avg_glucose_level: 100,
  bmi: 25,
  smoking_status: 'never smoked',
  last_assessment: {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    created_at: '2026-09-07T12:30:00Z',
    prediction: 1,
    probability: 0.8,
    risk_level: 'high',
  },
}

function mountView() {
  return mount(Patients)
}

describe('Patients view', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows LOADING while fetching patients, then the table', async () => {
    let resolveRequest
    listPatients.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Cargando pacientes…')

    resolveRequest([PATIENT])
    await flushPromises()
    expect(wrapper.text()).not.toContain('Cargando pacientes…')
    expect(wrapper.text()).toContain('Paciente #1')
  })

  it('renders each patient in EXACTLY ONE row with its real last assessment (SUCCESS)', async () => {
    listPatients.mockResolvedValue([PATIENT])
    const wrapper = mountView()
    await flushPromises()

    const rows = wrapper.findAll('tbody tr')
    // One registered patient -> exactly one data row (no factor stacking).
    expect(rows).toHaveLength(1)

    const cells = rows[0].findAll('td')
    expect(cells).toHaveLength(6) // Paciente | Edad | Riesgo | Probabilidad | Fecha | Estado

    // Neutral, real identifier — NOT gender/marital-status factors stacked.
    expect(cells[0].text()).toContain('Paciente #1')
    expect(cells[0].text()).toContain('11111111') // short id derived from the uuid
    expect(cells[0].text()).not.toContain('Mujer')
    expect(cells[0].text()).not.toContain('Sí')

    expect(cells[1].text()).toBe('45')
    expect(cells[2].text()).toContain('RIESGO ELEVADO')
    expect(cells[3].text()).toContain('80.0%')
    expect(cells[5].text()).toContain('Riesgo estimado')
  })

  it('renders two patients as two rows, each with its own risk level', async () => {
    const second = {
      ...PATIENT,
      id: '22222222-2222-2222-2222-222222222222',
      last_assessment: {
        ...PATIENT.last_assessment,
        probability: 0.2,
        risk_level: 'low',
      },
    }
    listPatients.mockResolvedValue([PATIENT, second])
    const wrapper = mountView()
    await flushPromises()

    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Paciente #1')
    expect(rows[1].text()).toContain('Paciente #2')
    // Every cell keeps its own value inside its own row (no cross-row drift);
    // the first column holds the neutral id + the short uuid fragment.
    const firstCells = rows.map((r) => r.find('td.cell--id').text())
    expect(firstCells[0]).toContain('Paciente #1')
    expect(firstCells[0]).toContain('11111111')
    expect(firstCells[1]).toContain('Paciente #2')
    expect(firstCells[1]).toContain('22222222')
  })

  it('maps risk probability to the canonical chips (medium below 0.72)', async () => {
    const medium = {
      ...PATIENT,
      id: '22222222-2222-2222-2222-222222222222',
      last_assessment: {
        ...PATIENT.last_assessment,
        probability: 0.5,
        risk_level: 'medium',
      },
    }
    listPatients.mockResolvedValue([medium])
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('RIESGO MEDIO')
    expect(wrapper.text()).toContain('50.0%')
  })

  it('shows the EMPTY state when there are no patients', async () => {
    listPatients.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Sin pacientes registrados')
  })

  it('shows the ERROR state with a friendly message when the API fails', async () => {
    listPatients.mockRejectedValue({
      message: 'No se ha podido conectar con el almacenamiento.',
    })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('No se ha podido conectar con el almacenamiento.')
    expect(wrapper.text()).toContain('Reintentar')
  })

  it('reloads patients when Retry is clicked after an error', async () => {
    listPatients.mockRejectedValueOnce({
      message: 'No se ha podido conectar con el almacenamiento.',
    })
    listPatients.mockResolvedValueOnce([PATIENT])
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Reintentar')

    await wrapper.find('.state-row__retry').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Paciente #1')
    expect(listPatients).toHaveBeenCalledTimes(2)
  })
})