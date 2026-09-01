"""FastAPI prediction service for F5 RiskAI (Issue #026).

Exposes an HTTP backend that loads the baseline Pipeline artifact
(preprocessing + LogisticRegression) trained in Issue #017 once and serves:

* ``GET  /health``  -- liveness check.
* ``POST /predict`` -- accepts patient data, validates it, returns the
  predicted class and the probability of ``stroke=1``.

Design:
* The model is loaded at import time (once) with :func:`load_model` and reused
  across requests (no per-request reload).
* Pure prediction logic (``build_dataframe``, ``predict``) is reused from
  ``scripts/predict_cli.py`` to avoid duplicating business rules.
* Validation is declarative via Pydantic field constraints (HTTP 422 for
  schema/validation errors).
* No ``fit``/``fit_transform`` is ever executed: every request follows
  request -> validation -> DataFrame -> predict -> predict_proba -> response.
* The model is never re-trained, balanced, tuned or re-thresholded; the raw
  dataset is never modified.

Run from the repository root::

    python -m uvicorn backend.main:app --reload
"""

from __future__ import annotations

import os
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import predict_cli  # noqa: E402  (pure prediction logic from Issue #022)

# Resolve the artifact path relative to the repository root regardless of the
# directory from which uvicorn is launched.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(_REPO_ROOT, "artifacts", "logistic_regression_baseline.joblib")


def _load_model_once():
    """Load the Pipeline once at startup, raising a clear error if missing."""
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"No existe el artefacto del modelo en '{MODEL_PATH}'. "
            "Entrena antes el modelo (Issue #017)."
        )
    pipeline = joblib.load(MODEL_PATH)
    if "model" not in getattr(pipeline, "named_steps", {}):
        raise RuntimeError("El artefacto no es un Pipeline con un paso 'model'.")
    return pipeline


try:
    _MODEL = _load_model_once()
except Exception as _model_load_error:  # pragma: no cover - guarded at /health
    _MODEL = None
    _MODEL_LOAD_ERROR = str(_model_load_error)
else:
    _MODEL_LOAD_ERROR = None

app = FastAPI(
    title="F5 RiskAI Prediction API",
    description=(
        "Prototype backend for stroke risk estimation. "
        "Not a medical diagnosis."
    ),
    version="0.1.0",
)

# Minimal CORS for the Vue frontend during local development. The default dev
# origin is the Vite dev server; narrow the list (no wildcard credentials).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


class PredictionRequest(BaseModel):
    """Input schema with exactly the features used by the model (no ``stroke``)."""

    gender: Literal["Female", "Male"]
    age: float = Field(ge=0, le=130, description="Edad (0-130). Validación de entrada.")
    hypertension: Literal[0, 1]
    heart_disease: Literal[0, 1]
    ever_married: Literal["No", "Yes"]
    work_type: Literal["Govt_job", "Private", "Self-employed", "children"]
    Residence_type: Literal["Rural", "Urban"]
    avg_glucose_level: float = Field(ge=0, description="Nivel medio de glucosa (>= 0).")
    bmi: float = Field(ge=5, le=100, description="BMI (5-100). Validación de entrada.")
    smoking_status: Literal[
        "never smoked", "formerly smoked", "smokes", "Unknown"
    ]


class PredictionResponse(BaseModel):
    """Output schema: predicted class and probability of ``stroke=1``."""

    prediction: Literal[0, 1]
    probability: float = Field(ge=0, le=1)


@app.get("/health")
def health():
    """Liveness check (200 always). Reflects model availability minimally."""
    return {"status": "ok", "model_available": _MODEL is not None}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Predict stroke class and probability from validated patient data."""
    if _MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible. Entrena antes el modelo (Issue #017).",
        )

    # Build a single-row DataFrame with the exact feature columns, reusing the
    # pure logic from Issue #022. No preprocessing is done here: the Pipeline
    # applies preprocessing internally.
    data = request.model_dump()
    df = predict_cli.build_dataframe(data)
    pred = int(_MODEL.predict(df)[0])
    proba = float(_MODEL.predict_proba(df)[0][1])

    return PredictionResponse(prediction=pred, probability=proba)