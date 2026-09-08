"""FastAPI prediction service for F5 RiskAI (Issue #026).

Exposes an HTTP backend that loads the final optimised Pipeline artifact
(LogisticRegression + RandomOverSampler, C=0.5) once and serves:

* ``GET  /health``                       -- liveness check.
* ``POST /predict``                      -- validates patient data, returns the
   predicted class, probability of ``stroke=1`` and the canonical risk level,
   persisting the evaluation (Patient + Assessment) when storage is available.
* ``GET  /patients``                     -- all patients, newest first.
* ``GET  /assessments``                  -- all assessments, newest first.
* ``GET  /assessments/{id}``             -- single assessment + patient data.
* ``GET  /assessments/{id}/report``      -- PDF report (ReportLab, real data).

Design:
* The model is loaded at import time (once) with :func:`load_model` and reused
  across requests (no per-request reload).
* Pure prediction logic (``build_dataframe``, ``predict``) is reused from
  ``scripts/predict_cli.py`` to avoid duplicating business rules.
* Validation is declarative via Pydantic field constraints (HTTP 422 for
  schema/validation errors).
* Persistence is best-effort: with no ``DATABASE_URL`` (or an unreachable
  database) the prediction is STILL returned with ``assessment_id=None``; only
  the storage endpoints answer 503 (friendly message, no internals leaked).
* Storage configuration lives in ``backend/database.py`` (reads ``DATABASE_URL``
  and a local ``.env``); migrations are managed with Alembic (``backend/alembic/``).
* No ``fit``/``fit_transform`` is ever executed: every request follows
  request -> validation -> DataFrame -> predict -> predict_proba -> response.
* The model is never re-trained, balanced, tuned or re-thresholded; the raw
  dataset is never modified.

Run from the repository root::

    python -m uvicorn backend.main:app --reload
"""

from __future__ import annotations

import os
import uuid
from typing import Literal

import joblib
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import predict_cli  # noqa: E402  (pure prediction logic from Issue #022)

from backend import persistence, reports  # noqa: E402
from backend.database import get_db, get_db_optional  # noqa: E402
from backend.models import Assessment, Patient  # noqa: E402
from backend.risk import risk_level_from_probability  # noqa: E402
from backend.schemas import (  # noqa: E402
    AssessmentDetailOut,
    AssessmentOut,
    PatientOut,
)

# Resolve the artifact path relative to the repository root regardless of the
# directory from which uvicorn is launched. The API uses the FINAL tuned model
# (LogisticRegression + RandomOverSampler, C=0.5), NOT the training baseline.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(_REPO_ROOT, "artifacts", "logistic_regression_tuned.joblib")


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

# CORS for the Vue frontend. Origins come from the CORS_ORIGINS environment
# variable (comma-separated) so the same app works locally and on Render;
# the local Vite dev origins are the defaults (no wildcard credentials).
_DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
_CORS_ENV = os.getenv("CORS_ORIGINS", "").strip()
_CORS_ORIGINS = (
    [origin.strip() for origin in _CORS_ENV.split(",") if origin.strip()]
    if _CORS_ENV
    else _DEFAULT_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
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
    """Output schema: predicted class, probability of ``stroke=1`` and the
    canonical risk level. ``assessment_id`` is present when the evaluation was
    persisted (storage configured + available); None otherwise."""

    prediction: Literal[0, 1]
    probability: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high"]
    assessment_id: uuid.UUID | None = None


@app.get("/health")
def health():
    """Liveness check (200 always). Reflects model availability minimally."""
    return {"status": "ok", "model_available": _MODEL is not None}


@app.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest, db: Session | None = Depends(get_db_optional)
) -> PredictionResponse:
    """Predict stroke class and probability from validated patient data.

    The evaluation is persisted (Patient + Assessment) with the EXACT same
    values returned to the user. If storage is unavailable the prediction is
    still returned (assessment_id=None) — persistence never blocks a result.
    """
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
    risk_level = risk_level_from_probability(proba)

    # Persist best-effort: DB down -> prediction still returned (degraded).
    assessment_id = None
    if db is not None:
        try:
            assessment = persistence.save_assessment(db, data, pred, proba, risk_level)
            db.commit()
            assessment_id = assessment.id
        except Exception:
            # NEVER leak connection/SQL internals and never log clinical payloads.
            db.rollback()
            assessment_id = None

    return PredictionResponse(
        prediction=pred,
        probability=proba,
        risk_level=risk_level,
        assessment_id=assessment_id,
    )


def _patient_out(patient: Patient) -> PatientOut:
    """Serialize a patient with its most recent assessment (or None)."""
    last = patient.assessments[0] if patient.assessments else None
    return PatientOut(
        **{
            "id": patient.id,
            "created_at": patient.created_at,
            "gender": patient.gender,
            "age": patient.age,
            "hypertension": patient.hypertension,
            "heart_disease": patient.heart_disease,
            "ever_married": patient.ever_married,
            "work_type": patient.work_type,
            "residence_type": patient.residence_type,
            "avg_glucose_level": patient.avg_glucose_level,
            "bmi": patient.bmi,
            "smoking_status": patient.smoking_status,
        },
        last_assessment=(
            {
                "id": last.id,
                "created_at": last.created_at,
                "prediction": last.prediction,
                "probability": last.probability,
                "risk_level": last.risk_level,
            }
            if last is not None
            else None
        ),
    )


_STORAGE_503_MESSAGE = "No se ha podido conectar con el almacenamiento."


@app.get("/patients", response_model=list[PatientOut])
def list_patients(db: Session = Depends(get_db)) -> list[PatientOut]:
    """All patients (most recent first) with their latest assessment."""
    try:
        patients = (
            db.execute(select(Patient).order_by(Patient.created_at.desc()))
            .scalars()
            .all()
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=503, detail=_STORAGE_503_MESSAGE) from None
    return [_patient_out(p) for p in patients]


@app.get("/assessments", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db)) -> list[AssessmentOut]:
    """All assessments, newest first (History view)."""
    try:
        rows = db.execute(
            select(Assessment).order_by(Assessment.created_at.desc())
        ).scalars().all()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=503, detail=_STORAGE_503_MESSAGE) from None
    return [
        AssessmentOut(
            id=a.id,
            patient_id=a.patient_id,
            created_at=a.created_at,
            prediction=a.prediction,
            probability=a.probability,
            risk_level=a.risk_level,
            model_name=a.model_name,
            model_version=a.model_version,
        )
        for a in rows
    ]


def _get_assessment_or_404(db: Session, assessment_id: uuid.UUID) -> Assessment:
    try:
        assessment = db.get(Assessment, assessment_id)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=503, detail=_STORAGE_503_MESSAGE) from None
    if assessment is None:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    return assessment


@app.get("/assessments/{assessment_id}", response_model=AssessmentDetailOut)
def get_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db)) -> AssessmentDetailOut:
    """Single assessment detail, including the associated patient snapshot."""
    assessment = _get_assessment_or_404(db, assessment_id)
    return AssessmentDetailOut(
        id=assessment.id,
        patient_id=assessment.patient_id,
        created_at=assessment.created_at,
        prediction=assessment.prediction,
        probability=assessment.probability,
        risk_level=assessment.risk_level,
        model_name=assessment.model_name,
        model_version=assessment.model_version,
        patient=_patient_out(assessment.patient),
    )


@app.get("/assessments/{assessment_id}/report")
def get_assessment_report(
    assessment_id: uuid.UUID,
    locale: str = Query("es", pattern=r"^(es|en)$"),
    db: Session = Depends(get_db),
) -> Response:
    """PDF report for one stored assessment (real data only, with i18n support)."""
    assessment = _get_assessment_or_404(db, assessment_id)
    pdf_bytes = reports.generate_assessment_pdf(
        assessment, assessment.patient, locale=locale,
    )
    filename = f"informe_riskai_{assessment_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )