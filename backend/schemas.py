"""Pydantic response schemas for the persistence endpoints (Issue: DB layer).

Only presentation-shaped models live here: they describe what the API returns
for patients and assessments. The input schema for ``POST /predict`` stays in
``backend/main.py`` next to the endpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentSummary(BaseModel):
    """Lightweight assessment summary embedded in patient rows."""

    id: uuid.UUID
    created_at: datetime
    prediction: int
    probability: float
    risk_level: str


class PatientOut(BaseModel):
    """A patient row with its most recent assessment (for the table UX)."""

    id: uuid.UUID
    created_at: datetime
    gender: str
    age: float
    hypertension: int
    heart_disease: int
    ever_married: str
    work_type: str
    residence_type: str
    avg_glucose_level: float
    bmi: float
    smoking_status: str
    last_assessment: AssessmentSummary | None = None


class AssessmentOut(BaseModel):
    """An evaluation row as shown in the History view."""

    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    prediction: int
    probability: float
    risk_level: str
    model_name: str
    model_version: str


class AssessmentDetailOut(AssessmentOut):
    """Full evaluation detail (patient data + result) for reports/future use."""

    patient: PatientOut = Field(description="Patient snapshot (without last_assessment recursion)")