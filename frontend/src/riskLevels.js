/**
 * Shared visual risk-level classification for F5 RiskAI.
 *
 * SINGLE SOURCE OF TRUTH for the presentation thresholds used by the Inicio
 * view: the Analysis Summary and the Brain3D visual state BOTH derive from
 * `riskLevelFromProbability()` so the text and the brain can never disagree.
 *
 * IMPORTANT:
 *   - These thresholds are PRESENTATION-ONLY (MVP visual categories). They are
 *     NOT clinical thresholds and NOT the model's internal decision threshold.
 *     The Logistic Regression model keeps its own prediction logic untouched.
 *   - If the thresholds change later, edit them HERE — do not hunt for magic
 *     numbers across the codebase.
 */
export const LOW_RISK_THRESHOLD = 0.3 // probability <  0.30 -> LOW
export const HIGH_RISK_THRESHOLD = 0.5 // probability >= 0.50 -> HIGH (0.30..0.50 -> MEDIUM)

/** Canonical risk levels used as Brain3D states and summary labels. */
export const RISK_LEVELS = Object.freeze({
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
})

/**
 * Map a probability to its visual risk level.
 *
 * Returns one of RISK_LEVELS, or null for values that cannot produce a safe
 * visual state (not a number, NaN, or outside 0..1) so callers can keep the
 * brain/summary neutral instead of rendering an incorrect state.
 *
 * @param {*} probability - value received from POST /predict
 * @returns {('low'|'medium'|'high'|null)}
 */
export function riskLevelFromProbability(probability) {
  if (typeof probability !== 'number' || Number.isNaN(probability)) return null
  if (probability < 0 || probability > 1) return null
  if (probability < LOW_RISK_THRESHOLD) return RISK_LEVELS.LOW
  if (probability < HIGH_RISK_THRESHOLD) return RISK_LEVELS.MEDIUM
  return RISK_LEVELS.HIGH
}