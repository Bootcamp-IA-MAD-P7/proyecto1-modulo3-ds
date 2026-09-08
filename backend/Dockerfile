# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# F5 RiskAI — backend (FastAPI) image.
#
# Serves the trained Logistics Regression Pipeline from a well-known repo
# path. Only the files the API needs are copied:
#   * backend/                 (app + Alembic migrations)
#   * scripts/{predict_cli,evaluate_baseline,preprocessing}.py (runtime chain)
#   * artifacts/logistic_regression_tuned.joblib  (the model)
#
# No .env files, no credentials, no training data are copied.
# ---------------------------------------------------------------------------
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Install Python dependencies first (better layer caching).
COPY requirements.docker.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

# 2) Copy only the runtime files.
COPY backend/ backend/
COPY scripts/predict_cli.py scripts/predict_cli.py
COPY scripts/evaluate_baseline.py scripts/evaluate_baseline.py
COPY scripts/preprocessing.py scripts/preprocessing.py
COPY artifacts/logistic_regression_tuned.joblib artifacts/logistic_regression_tuned.joblib

# 3) Entrypoint: wait for PostgreSQL -> alembic upgrade head -> uvicorn.
COPY docker/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
RUN chmod +x /usr/local/bin/backend-entrypoint.sh

# The service listens on ${PORT:-8000} (see backend-entrypoint.sh): 8000 in
# local Docker Compose, the port Render injects via `$PORT` in production.
# Never localhost: the browser and other containers reach it through the
# Compose network or a published port.
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/backend-entrypoint.sh"]