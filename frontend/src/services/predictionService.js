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

/**
 * POST /predict with the patient data.
 *
 * @param {object} payload validated patient attributes (10 model features)
 * @returns {Promise<{prediction: 0|1, probability: number}>}
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
    let detail = null
    try {
      const body = await response.json()
      detail =
        body && typeof body.detail === 'string'
          ? body.detail
          : `La API respondió con un error (HTTP ${response.status}).`
    } catch {
      detail = `La API respondió con un error (HTTP ${response.status}).`
    }
    throw toUserError(
      { code: `HTTP_${response.status}` },
      detail || 'La API respondió con un error inesperado.',
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

  return {
    prediction: Number(data.prediction),
    probability: Number(data.probability),
  }
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