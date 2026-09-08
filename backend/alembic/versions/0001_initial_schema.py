"""initial schema: patients and assessments

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-07

Tables created:

* patients    -- one row per set of clinical factors (10 features), UUID id.
* assessments -- one row per POST /predict evaluation; FK to patients with
                 ON DELETE CASCADE; UUID id; indexes on patient_id and
                 created_at (History view is ordered by created_at DESC).

Both use ``gen_random_uuid()`` as the server-side default on PostgreSQL
(requires the ``pgcrypto`` extension, enabled below).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # gen_random_uuid() lives in the pgcrypto extension (PostgreSQL).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("gender", sa.String(16), nullable=False),
        sa.Column("age", sa.Float, nullable=False),
        sa.Column("hypertension", sa.Integer, nullable=False),
        sa.Column("heart_disease", sa.Integer, nullable=False),
        sa.Column("ever_married", sa.String(8), nullable=False),
        sa.Column("work_type", sa.String(24), nullable=False),
        sa.Column("residence_type", sa.String(16), nullable=False),
        sa.Column("avg_glucose_level", sa.Float, nullable=False),
        sa.Column("bmi", sa.Float, nullable=False),
        sa.Column("smoking_status", sa.String(24), nullable=False),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "patient_id",
            sa.Uuid,
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("prediction", sa.Integer, nullable=False),
        sa.Column("probability", sa.Float, nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
    )
    op.create_index("ix_assessments_patient_id", "assessments", ["patient_id"])
    op.create_index("ix_assessments_created_at", "assessments", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_assessments_created_at", table_name="assessments")
    op.drop_index("ix_assessments_patient_id", table_name="assessments")
    op.drop_table("assessments")
    op.drop_table("patients")