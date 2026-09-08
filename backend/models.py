"""SQLAlchemy ORM models for F5 RiskAI persistence (PostgreSQL).

Schema (MVP, as specified):

* PATIENTS    -- one row per real set of clinical factors submitted from the
                 dashboard. No ``stroke`` label is stored (that is the model's
                 target variable and is never part of user input).
* ASSESSMENTS -- one row per POST /predict evaluation. A patient can have many
                 assessments (relationship 1 -> N).

IDs are UUIDs generated application-side (portable across PostgreSQL and the
isolated SQLite test strategy); the Alembic migration also adds a server-side
default (``gen_random_uuid()``) for PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    """Clinical factors submitted by the user for one or more evaluations."""

    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    age: Mapped[float] = mapped_column(Float, nullable=False)
    hypertension: Mapped[int] = mapped_column(Integer, nullable=False)
    heart_disease: Mapped[int] = mapped_column(Integer, nullable=False)
    ever_married: Mapped[str] = mapped_column(String(8), nullable=False)
    work_type: Mapped[str] = mapped_column(String(24), nullable=False)
    residence_type: Mapped[str] = mapped_column(String(16), nullable=False)
    avg_glucose_level: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    smoking_status: Mapped[str] = mapped_column(String(24), nullable=False)

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Assessment.created_at.desc()",
    )


class Assessment(Base):
    """A single evaluation: model prediction + probability + risk level."""

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="assessments")