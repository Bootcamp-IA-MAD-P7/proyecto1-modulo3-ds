"""Persistence helpers: store a prediction as a Patient + Assessment pair.

Design:
* One prediction -> ONE write path. The same prediction/probability computed
  for the response is the exact value persisted (no second prediction call).
* Patients are de-duplicated by their exact clinical fingerprint (the ten
  fields the user submits). If an identical patient already exists, the new
  assessment is linked to it; otherwise a new patient row is created. This
  keeps the Patients view meaningful without inventing identities.
* Nothing here logs clinical data.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Assessment, Patient

MODEL_NAME = "Logistic Regression + RandomOverSampler"
MODEL_VERSION = "final-tuned (C=0.5, lbfgs, max_iter=500)"


def _fingerprint(payload: dict) -> dict:
    """Normalise the submitted factors to the patient column names."""
    return {
        "gender": payload["gender"],
        "age": float(payload["age"]),
        "hypertension": int(payload["hypertension"]),
        "heart_disease": int(payload["heart_disease"]),
        "ever_married": payload["ever_married"],
        "work_type": payload["work_type"],
        "residence_type": payload["Residence_type"],
        "avg_glucose_level": float(payload["avg_glucose_level"]),
        "bmi": float(payload["bmi"]),
        "smoking_status": payload["smoking_status"],
    }


def _find_or_create_patient(db: Session, payload: dict) -> Patient:
    """Return the existing patient with the same factors, or create one."""
    fp = _fingerprint(payload)
    existing = db.execute(select(Patient).filter_by(**fp)).scalars().first()
    if existing is not None:
        return existing
    patient = Patient(**fp)
    db.add(patient)
    db.flush()
    return patient


def save_assessment(
    db: Session,
    payload: dict,
    prediction: int,
    probability: float,
    risk_level: str,
) -> Assessment:
    """Persist one evaluation (patient + assessment) and return the row.

    ``db.commit`` is intentionally left to the caller so one request commits
    exactly once (prediction endpoint).
    """
    patient = _find_or_create_patient(db, payload)
    assessment = Assessment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        prediction=int(prediction),
        probability=float(probability),
        risk_level=risk_level,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
    )
    db.add(assessment)
    db.flush()
    return assessment