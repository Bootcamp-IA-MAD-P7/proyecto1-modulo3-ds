# API de Predicción — F5 RiskAI

## Objetivo

Backend HTTP de F5 RiskAI utilizando FastAPI. Expone un servicio de predicción que carga el modelo baseline (preprocessing + LogisticRegression, entrenado en el Issue #017) y responde con la clase predicha y la probabilidad de `stroke=1`. Está pensado para ser consumido posteriormente por el frontend Vue.

El modelo se carga tal cual; no se reentrena, ni se balancea, ni se modifica el threshold. La API no ejecuta `fit`/`fit_transform`: cada request sigue `request → validación → DataFrame → predict → predict_proba → response`.

## Dependencias

- **FastAPI** (incluye Pydantic y Starlette)
- **Pydantic**
- **Uvicorn**
- pandas, scikit-learn, joblib (ya existentes)

Se agregaron `fastapi` y `uvicorn` al entorno virtual (`.venv/`) y a `pyproject.toml`.

## Cómo ejecutar

Desde la raíz del repositorio:

```
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

El servidor queda disponible en `http://127.0.0.1:8000`.

Requiere el artefacto `artifacts/logistic_regression_baseline.joblib` (entrenado en el Issue #017). Si no existe, `/predict` devuelve un error 503 con mensaje claro indicando que primero debe entrenarse el modelo.

## GET /health

Devuelve el estado del servicio.

Ejemplo:

```
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "model_available": true
}
```

Código HTTP: `200`.

## POST /predict

Recibe los datos de un paciente y devuelve la predicción. Ejemplo de request:

```json
{
  "gender": "Female",
  "age": 45,
  "hypertension": 0,
  "heart_disease": 1,
  "ever_married": "Yes",
  "work_type": "Private",
  "Residence_type": "Urban",
  "avg_glucose_level": 100,
  "bmi": 25,
  "smoking_status": "never smoked"
}
```

Ejemplo con `curl`:

```
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d @- <<'EOF'
{ "gender": "Female", "age": 45, "hypertension": 0, "heart_disease": 1, "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban", "avg_glucose_level": 100, "bmi": 25, "smoking_status": "never smoked" }
EOF
```

## Response

```json
{
  "prediction": 0,
  "probability": 0.015
}
```

- `prediction`: clase predicha, `0` o `1` (de `model.predict()`).
- `probability`: probabilidad de `stroke=1` en formato decimal (de `model.predict_proba()`), entre 0 y 1. No se convierte a porcentaje; la presentación visual la hará el frontend.

Código HTTP: `200`.

## Validaciones

| Campo | Tipo | Regla |
|---|---|---|
| `gender` | categórico | `Female` \| `Male` |
| `age` | numérico | `0–130` |
| `hypertension` | binario | `0` \| `1` |
| `heart_disease` | binario | `0` \| `1` |
| `ever_married` | categórico | `Yes` \| `No` |
| `work_type` | categórico | `Govt_job` \| `Private` \| `Self-employed` \| `children` |
| `Residence_type` | categórico | `Rural` \| `Urban` |
| `avg_glucose_level` | numérico | `>= 0` |
| `bmi` | numérico | `5–100` |
| `smoking_status` | categórico | `never smoked` \| `formerly smoked` \| `smokes` \| `Unknown` |

> Los rangos numéricos (edad, BMI, glucosa) son reglas de **validación de entrada** para evitar valores absurdos. No son límites médicos.

Las categorías son las del dataset (Issue #022); no se permiten valores arbitrarios. No se incluye `stroke` porque es la variable objetivo.

## Errores

- **422** — Unprocessable Entity: el request no cumple el schema o las restricciones. La respuesta indica qué campo es inválido.
- **503** — Service Unavailable: el modelo no está disponible (falta el artefacto). Mensaje claro sin rutas internas ni stack traces.

No se muestran secretos, rutas internas ni información sensible. No se crea automáticamente otro modelo.

## Swagger / OpenAPI

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **Spec JSON:** `http://127.0.0.1:8000/openapi.json`

Ambos generados por FastAPI; muestran campos de request, campos de response, tipos y validaciones.

## Advertencia de uso

Este sistema es un **prototipo de análisis predictivo y no constituye un diagnóstico médico**. Las predicciones provienen de un modelo baseline (sin balanceo) con bajo recall de la clase minoritaria, y deben interpretarse con cautela.