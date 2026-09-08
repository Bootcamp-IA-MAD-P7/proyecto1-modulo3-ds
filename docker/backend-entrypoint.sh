#!/bin/sh
# F5 RiskAI backend entrypoint (Docker).
#
# Responsibilities, in order:
#   1. Wait until PostgreSQL is reachable (DATABASE_URL must be set).
#   2. Apply Alembic migrations: `alembic upgrade head` (idempotent).
#   3. Start Uvicorn bound to 0.0.0.0:${PORT:-8000}.
#
# The port honours the `PORT` variable injected by Render for web services
# (default 10000 there); local Docker Compose does not set it, so the
# fallback 8000 keeps the existing compose layout unchanged.
#
# No secrets are baked into the image: DATABASE_URL and CORS_ORIGINS are
# provided at runtime through the container environment.
set -e

echo "[entrypoint] Waiting for PostgreSQL (DATABASE_URL=${DATABASE_URL:-<not set>}) ..."

python - <<'PY'
import os
import time

from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL", "").strip()
if not url:
    raise SystemExit("DATABASE_URL is not set. Cannot start without a database.")

engine = create_engine(url, pool_pre_ping=True)
attempts = 30
for i in range(attempts):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] PostgreSQL is ready.")
        break
    except Exception as exc:  # noqa: BLE001 - any connectivity error is retried
        print(f"[entrypoint] waiting for PostgreSQL ({i + 1}/{attempts}): {type(exc).__name__}")
        time.sleep(2)
else:
    raise SystemExit(f"PostgreSQL not reachable after {attempts * 2}s. Aborting.")
PY

echo "[entrypoint] Applying Alembic migrations (alembic upgrade head) ..."
cd /app/backend
alembic upgrade head
cd /app

echo "[entrypoint] Starting Uvicorn on 0.0.0.0:${PORT:-8000} ..."
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"