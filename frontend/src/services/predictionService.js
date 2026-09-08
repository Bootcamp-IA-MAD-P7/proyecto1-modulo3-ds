/**
 * predictionService.js (Issue #034)
 *
 * Independent API layer for F5 RiskAI. Components never call fetch() directly;
 * they delegate to this service.
 *
 * The base URL is configurable through the VITE_API_URL environment variable so
 * it is not hardcoded across components:
 *
 *   # frontend/.env.local
 *   VITE_API_URL=http://127.0.0.1:8000
 *
 * If unset, it falls back to the FastAPI default local origin.
 */

const DEFAULT_API_URL = 'http://127.0.0.1:8000'

function resolveBaseUrl() {
  const fromEnv = import.meta.env && import.meta.env.VITE_API_URL
  return (fromEnv && fromEnv.trim()) || DEFAULT_API_URL
}

export const API_BASE_URL = resolveBaseUrl()

/**
 * Normalizes any failure into a stable, human-readable error object.
 * Never exposes stack traces to the UI.
 */
function toUserError(error, detail) {
  if (error && typeof error.isUserError === 'boolean') return error
  return {
    isUserError: true,
    code: error && error.code ? error.code : 'UNKNOWN',
    message: detail || 'Unexpected error while contacting the prediction service.',
  }
}

/** Extracts a user-safe `detail` string from an error response body, if any. */
async function readDetail(response) {
  try {
    const body = await response.json()
    if (body && typeof body.detail === 'string') return body.detail
  } catch {
    /* non-JSON error body — fall through */
  }
  return null
}

/** Throws a friendly error derived from an HTTP error response. */
async function throwForStatus(response, fallbackMessage) {
  const detail = (await readDetail(response)) || fallbackMessage
  throw toUserError({ code: `HTTP_${response.status}` }, detail)
}

/**
 * GET a JSON collection/object from the API with a unified error contract.
 * @param {string} path  e.g. '/patients'
 * @returns {Promise<any>} parsed JSON body
 */
async function getJson(path, errorMessage) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method: 'GET' })
  } catch (err) {
    // Network failure / API is down / timeout.
    throw toUserError(err, errorMessage)
  }
  if (!response.ok) {
    await throwForStatus(response, `La API respondió con un error (HTTP ${response.status}).`)
  }
  try {
    return await response.json()
  } catch {
    throw toUserError(
      { code: 'BAD_JSON' },
      'El servicio devolvió una respuesta no válida.',
    )
  }
}

/**
 * POST /predict with the patient data.
 *
 * @param {object} payload validated patient attributes (10 model features)
 * @returns {Promise<{prediction: 0|1, probability: number, risk_level?: string, assessment_id?: string|null}>}
 * @throws {object} user-facing error object
 */
export async function predictStroke(payload) {
  const url = `${API_BASE_URL}/predict`

  let response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (err) {
    // Network failure / API is down / timeout.
    throw toUserError(err, 'No se pudo conectar con el servicio de predicción.')
  }

  if (!response.ok) {
    await throwForStatus(
      response,
      `La API respondió con un error (HTTP ${response.status}).`,
    )
  }

  // Parse the JSON body defensively.
  let data
  try {
    data = await response.json()
  } catch {
    throw toUserError(
      { code: 'BAD_JSON' },
      'El servicio devolvió una respuesta no válida.',
    )
  }

  if (
    typeof data !== 'object' ||
    data === null ||
    !(data.prediction === 0 || data.prediction === 1 ||
      data.prediction === '0' || data.prediction === '1') ||
    typeof data.probability !== 'number' ||
    data.probability < 0 ||
    data.probability > 1
  ) {
    throw toUserError(
      { code: 'BAD_RESPONSE' },
      'El servicio devolvió una respuesta con formato inesperado.',
    )
  }

  // The new backend fields (risk_level, assessment_id) are passed through only
  // when the API actually provides them, so older API versions keep working.
  const result = {
    prediction: Number(data.prediction),
    probability: Number(data.probability),
  }
  if (data.risk_level !== undefined) result.risk_level = data.risk_level
  if (data.assessment_id !== undefined) result.assessment_id = data.assessment_id
  return result
}

/**
 * GET /health - lightweight availability check.
 * @returns {Promise<boolean>}
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { method: 'GET' })
    if (!response.ok) return false
    const body = await response.json()
    return body && body.status === 'ok'
  } catch {
    return false
  }
}

/**
 * GET /patients — all persisted patients (newest first) with their most
 * recent assessment.
 * @returns {Promise<Array>} e.g. [{ id, created_at, gender, age, ... , last_assessment }]
 */
export function listPatients() {
  return getJson('/patients', 'No se pudieron cargar los pacientes.')
}

/**
 * GET /assessments — all assessments, newest first (History view).
 * @returns {Promise<Array>} e.g. [{ id, patient_id, created_at, prediction, probability, risk_level }]
 */
export function listAssessments() {
  return getJson('/assessments', 'No se pudieron cargar las evaluaciones.')
}

/**
 * GET /assessments/{id} — single assessment detail with its patient snapshot.
 * @param {string} id uuid of the assessment
 * @returns {Promise<object>}
 */
export function getAssessment(id) {
  return getJson(`/assessments/${id}`, 'No se pudo cargar la evaluación.')
}

/**
 * Absolute URL of the PDF report for one assessment (download target).
 * @param {string} id uuid of the assessment
 * @param {string} [locale='es'] report language ('es' | 'en')
 * @returns {string}
 */
export function assessmentReportUrl(id, locale = 'es') {
  return `${API_BASE_URL}/assessments/${id}/report?locale=${encodeURIComponent(locale)}`
}