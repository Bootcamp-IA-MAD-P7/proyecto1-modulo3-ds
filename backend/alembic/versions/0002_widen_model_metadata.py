"""widen model metadata columns on assessments

Revision ID: 0002_widen_model_metadata
Revises: 0001_initial_schema
Create Date: 2026-09-08

Why: PostgreSQL enforces column widths. The real metadata values are longer
than the initial ``varchar(32)``:

* model_name    = 'Logistic Regression + RandomOverSampler'           (37 chars)
* model_version = 'final-tuned (C=0.5, lbfgs, max_iter=500)'          (44 chars)

SQLite (used by tests via create_all) silently accepts over-length strings,
so this defect only surfaced during the real PostgreSQL integration test.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_widen_model_metadata"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "assessments",
        "model_name",
        existing_type=sa.String(64),
        type_=sa.String(100),
        existing_nullable=False,
    )
    op.alter_column(
        "assessments",
        "model_version",
        existing_type=sa.String(32),
        type_=sa.String(100),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "assessments",
        "model_version",
        existing_type=sa.String(100),
        type_=sa.String(32),
        existing_nullable=False,
    )
    op.alter_column(
        "assessments",
        "model_name",
        existing_type=sa.String(100),
        type_=sa.String(64),
        existing_nullable=False,
    )