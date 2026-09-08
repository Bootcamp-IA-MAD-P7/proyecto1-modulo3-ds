"""Database configuration for F5 RiskAI (PostgreSQL via SQLAlchemy).

Design:
* The connection string is read ONLY from the ``DATABASE_URL`` environment
  variable (Render provides it automatically; locally it is set in a
  ``.env`` file next to the provided ``.env.example``). No credentials are
  hardcoded in the repository.
* If ``DATABASE_URL`` is absent, the app still boots: ``storage_available``
  is False, ``POST /predict`` degrades gracefully (the prediction is still
  returned, nothing to persist) and the storage endpoints answer a friendly
  503 instead of leaking internal errors.
* SQLite is NEVER the production target; it only appears in tests through a
  dependency override of :func:`get_db` (isolated in-memory strategy).
"""

from __future__ import annotations

import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Optional: read a local .env (the repository only ships .env.example).
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:  # pragma: no cover - dotenv is a dependency, keep it optional
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

_engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False) if _engine else None

#: True when a real storage backend is configured via DATABASE_URL.
storage_available: bool = _engine is not None


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session.

    Raises HTTP 503 (friendly message, no internal details) when storage is
    not configured or a connection cannot be established.
    """
    if _SessionLocal is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="No se ha podido conectar con el almacenamiento.",
        )
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_optional() -> Iterator[Session | None]:
    """Like :func:`get_db` but yields ``None`` when storage is unavailable.

    Used by ``POST /predict`` so the prediction is ALWAYS returned (the model
    is the product); persistence degrades gracefully when no database exists.
    """
    if _SessionLocal is None:
        yield None
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()