/**
 * Shared risk-level classification for F5 RiskAI (frontend).
 *
 * SINGLE SOURCE OF TRUTH for the presentation thresholds: the Dashboard
 * Analysis Summary, the Brain3D visual state and the Patients/History chips
 * ALL derive from `riskLevelFromProbability()` so text and visuals can never
 * disagree.
 *
 * These thresholds are the project-specified canonical split (spec examples:
 * 0.26 -> low, 0.60 -> medium, 0.80 -> high) and mirror the backend module
 * `backend/risk.py` — the values MUST stay identical in both places:
 *
 *   LOW    -> probability <  0.45
 *   MEDIUM -> 0.45 <= probability <  0.72
 *   HIGH   -> probability >= 0.72
 *
 * IMPORTANT:
 *   - The thresholds are PRESENTATION-ONLY risk categories, NOT clinical
 *     thresholds and NOT the model's internal decision threshold. The
 *     Logistic Regression model keeps its own prediction logic untouched.
 *   - If the thresholds change later, edit them HERE and in backend/risk.py —
 *     do not hunt for magic numbers across the codebase.
 */
export const LOW_RISK_THRESHOLD = 0.45 // probability <  0.45 -> LOW
export const HIGH_RISK_THRESHOLD = 0.72 // probability >= 0.72 -> HIGH (0.45..0.72 -> MEDIUM)

/** Canonical risk levels used as Brain3D states and summary labels. */
export const RISK_LEVELS = Object.freeze({
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
})

/**
 * Map a probability to its risk level.
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