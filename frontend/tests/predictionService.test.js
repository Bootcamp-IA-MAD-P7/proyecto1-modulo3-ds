import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  predictStroke,
  checkHealth,
  listPatients,
  listAssessments,
  getAssessment,
  assessmentReportUrl,
  API_BASE_URL,
} from '@/services/predictionService.js'
import { VALID_PAYLOAD } from './helpers.js'

function mockFetchOnce({ ok = true, status = 200, body } = {}) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
  })
}

describe('predictionService', () => {
  beforeEach(() => {
    cleanupFetch()
    expect(API_BASE_URL).toBe('http://127.0.0.1:8000')
  })

  afterEach(() => {
    cleanupFetch()
  })

  function cleanupFetch() {
    if (global.fetch) {
      global.fetch.mockRestore && global.fetch.mockRestore()
      delete global.fetch
    }
  }

  it('posts to /predict with the payload', async () => {
    mockFetchOnce({ status: 200, body: { prediction: 0, probability: 0.018580961296622237 } })
    await predictStroke(VALID_PAYLOAD)
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/predict'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const args = global.fetch.mock.calls[0]
    expect(args[1].body).toEqual(JSON.stringify(VALID_PAYLOAD))
  })

  it('resolves a valid response', async () => {
    mockFetchOnce({ status: 200, body: { prediction: 0, probability: 0.01 } })
    const data = await predictStroke(VALID_PAYLOAD)
    expect(data).toEqual({ prediction: 0, probability: 0.01 })
  })

  it('throws a friendly message when the API is unreachable', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(predictStroke(VALID_PAYLOAD)).rejects.toMatchObject({
      message: expect.stringContaining('No se pudo conectar'),
    })
  })

  it('throws when the API returns an error status', async () => {
    mockFetchOnce({ ok: false, status: 422, body: { detail: 'Bad input' } })
    await expect(predictStroke(VALID_PAYLOAD)).rejects.toMatchObject({
      message: 'Bad input',
    })
  })

  it('throws when the response body has an unexpected shape', async () => {
    mockFetchOnce({ status: 200, body: { prediction: 7, probability: -1 } })
    await expect(predictStroke(VALID_PAYLOAD)).rejects.toMatchObject({
      code: 'BAD_RESPONSE',
    })
  })

  it('returns false from checkHealth when the API is down', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(checkHealth()).resolves.toBe(false)
  })

  it('returns true from checkHealth on a healthy API', async () => {
    mockFetchOnce({ status: 200, body: { status: 'ok', model_available: true } })
    await expect(checkHealth()).resolves.toBe(true)
  })

  it('passes through risk_level and assessment_id when the API provides them', async () => {
    mockFetchOnce({
      status: 200,
      body: {
        prediction: 1,
        probability: 0.8,
        risk_level: 'high',
        assessment_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      },
    })
    const data = await predictStroke(VALID_PAYLOAD)
    expect(data).toEqual({
      prediction: 1,
      probability: 0.8,
      risk_level: 'high',
      assessment_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    })
  })

  it('omits risk fields for older API responses (backward compatible)', async () => {
    mockFetchOnce({ status: 200, body: { prediction: 0, probability: 0.2 } })
    const data = await predictStroke(VALID_PAYLOAD)
    expect(data.risk_level).toBeUndefined()
    expect(data.assessment_id).toBeUndefined()
  })

  describe('persistence endpoints', () => {
    it('listPatients GETs /patients and returns the array', async () => {
      const body = [{ id: '11111111-1111-1111-1111-111111111111', age: 45 }]
      mockFetchOnce({ status: 200, body })
      await expect(listPatients()).resolves.toEqual(body)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/patients'),
        expect.objectContaining({ method: 'GET' }),
      )
    })

    it('listAssessments GETs /assessments and returns the array', async () => {
      const body = [{ id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', probability: 0.8 }]
      mockFetchOnce({ status: 200, body })
      await expect(listAssessments()).resolves.toEqual(body)
    })

    it('getAssessment GETs /assessments/{id} and returns the detail', async () => {
      const body = { id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', patient: { age: 45 } }
      mockFetchOnce({ status: 200, body })
      await expect(getAssessment('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')).resolves.toEqual(body)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
        expect.objectContaining({ method: 'GET' }),
      )
    })

    it('throws a friendly storage error for a 503 response', async () => {
      mockFetchOnce({
        ok: false,
        status: 503,
        body: { detail: 'No se ha podido conectar con el almacenamiento.' },
      })
      await expect(listPatients()).rejects.toMatchObject({
        message: 'No se ha podido conectar con el almacenamiento.',
      })
    })

    it('throws a friendly message when the API is unreachable', async () => {
      global.fetch = vi
        .fn()
        .mockRejectedValue(new TypeError('Failed to fetch'))
      await expect(listPatients()).rejects.toMatchObject({
        message: expect.stringContaining('No se pudieron cargar los pacientes'),
      })
    })
  })

  it('assessmentReportUrl builds the absolute PDF report URL (default ES locale)', () => {
    expect(assessmentReportUrl('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')).toBe(
      `${API_BASE_URL}/assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/report?locale=es`,
    )
    expect(assessmentReportUrl('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'en')).toBe(
      `${API_BASE_URL}/assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/report?locale=en`,
    )
  })
})