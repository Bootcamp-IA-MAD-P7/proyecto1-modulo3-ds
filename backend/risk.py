"""Canonical risk-level classification for F5 RiskAI (backend).

SINGLE SOURCE OF TRUTH for turning a ``probability`` (of ``stroke=1``) into a
risk level. The same classification is used by the API response, the database
persistence, the Dashboard/Brain3D front-end state and the PDF reports.

Thresholds (project specification, ticket "último ajuste de interfaz"):

* LOW    -> probability <  0.45
* MEDIUM -> 0.45 <= probability <  0.72
* HIGH   -> probability >= 0.72

The frontend mirror of this module lives in ``frontend/src/riskLevels.js`` and
keeps the exact same values; do NOT duplicate the numbers anywhere else.
"""

from __future__ import annotations

from typing import Literal

RiskLevel = Literal["low", "medium", "high"]

LOW_RISK_THRESHOLD = 0.45
HIGH_RISK_THRESHOLD = 0.72


def risk_level_from_probability(probability: float) -> RiskLevel:
    """Classify ``probability`` into its canonical risk level.

    ``probability`` is expected to be a float from ``predict_proba`` (0..1).
    Values outside 0..1 are clamped into the closest level rather than being
    silently trusted, so a corrupted payload can never produce an invalid
    stored level.
    """
    if probability < LOW_RISK_THRESHOLD:
        return "low"
    if probability < HIGH_RISK_THRESHOLD:
        return "medium"
    return "high"