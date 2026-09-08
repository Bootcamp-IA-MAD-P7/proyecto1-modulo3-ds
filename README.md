# F5 RiskAI

Prototipo de Machine Learning para estimación de riesgo de ictus como herramienta de cribado previa a una consulta médica.

> **Aviso:** Este es un proyecto educativo y de prototipo. No está diseñado para diagnosticar, predecir ni tratar ninguna enfermedad. Los resultados generados por este sistema no deben utilizarse como base para decisiones médicas. Siempre consulte a un profesional de la salud.

## Project Overview

F5 RiskAI explora la viabilidad de utilizar técnicas de Machine Learning para estimar la probabilidad de sufrir un ictus a partir de datos clínicos y demográficos de pacientes. El proyecto se desarrolla como parte del Bootcamp de IA y Deep Learning.

El sistema se encuentra en fase de desarrollo temprano. Actualmente se ha configurado la estructura del proyecto, el entorno de Python y el flujo de trabajo con Git.

## Objective

Desarrollar un modelo de Machine Learning capaz de estimar el riesgo de ictus basándose en características como edad, género, nivel de glucosa, estado de tabaquismo y otros factores clínicos relevantes, funcionando como herramienta de apoyo al cribado.

## Technology Stack

| Componente | Tecnología |
|---|---|
| Lenguaje | Python >= 3.10 |
| Análisis de datos | pandas, numpy |
| Machine Learning | scikit-learn, imbalanced-learn, LightGBM |
| Visualización | matplotlib, seaborn |
| Backend | FastAPI + SQLAlchemy + Alembic |
| Base de datos | PostgreSQL (psycopg v3) |
| Reportes | ReportLab (PDF) |
| Frontend | Vue 3 + Vite + Vitest |
| Control de versiones | Git / GitHub |

## Project Structure

```
f5-riskai/
├── backend/            # API y lógica backend (futuro)
├── frontend/           # Aplicación Vue (futuro)
├── data/
│   ├── raw/            # Datos originales sin modificar
│   └── processed/      # Datos después del procesamiento
├── models/             # Modelos entrenados y artefactos
├── notebooks/          # Análisis exploratorio y experimentación
├── reports/            # Informes y resultados
├── scripts/            # Scripts ejecutables del proyecto
├── tests/              # Pruebas automatizadas
├── .gitignore
├── CONTRIBUTING.md     # Flujo de trabajo y convenciones
├── LICENSE             # MIT
├── pyproject.toml      # Configuración del proyecto Python
├── README.md
└── requirements.txt    # Dependencias del proyecto
```

## Development Workflow

El proyecto sigue un flujo de trabajo con tres niveles de ramas:

- **`main`** — Versión estable y lista para producción
- **`develop`** — Rama de integración para desarrollo activo
- **`feature/*`** — Ramas temporales para funcionalidades concretas

Los commits siguen la convención:

```
feat: add new feature
fix: correct a bug
docs: update documentation
refactor: restructure code
test: add or modify tests
chore: maintenance tasks
```

Para más detalles, consultar [CONTRIBUTING.md](CONTRIBUTING.md).

## Installation

### Requisitos

- Python >= 3.10

### Configuración

```bash
# Clonar el repositorio
git clone https://github.com/Bootcamp-IA-MAD-P7/proyecto1-modulo3-ds.git
cd proyecto1-modulo3-ds

# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Activar entorno (macOS/Linux)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Persistencia (PostgreSQL + API)

El backend persiste cada evaluación realizada desde el dashboard:

- **`POST /predict`** — valida los datos (HTTP 422 si son inválidos) y devuelve
  `{prediction, probability, risk_level, assessment_id}`. La evaluación se
  guarda en el mismo flujo, con los mismos valores devueltos (no hay una
  segunda predicción). Si la base de datos no está configurada o no responde,
  la predicción se devuelve igualmente con `assessment_id: null`.
- **`GET /patients`** — pacientes registrados (más recientes primero), cada
  uno con su última evaluación.
- **`GET /assessments`** — todas las evaluaciones, más recientes primero.
- **`GET /assessments/{id}`** — detalle de una evaluación con sus factores.
- **`GET /assessments/{id}/report`** — informe PDF (ReportLab) con los datos
  reales de la evaluación.
- Cuando el almacenamiento no está disponible, los endpoints de consulta
  responden `503` con un mensaje amigable (sin detalles internos).

Las evaluaciones se modelan como `patients` (1) — (N) `assessments`. Cada
paciente se identifica por sus 10 factores clínicos reales: un caso idéntico
ya registrado reutiliza la misma fila (dedupe por huella de factores).

### Variables de entorno

Copie `.env.example` a `.env` (y `frontend/.env.example` a `frontend/.env`):

```bash
DATABASE_URL=postgresql+psycopg://usuario:password@host:puerto/f5_riskai
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
VITE_API_URL=http://127.0.0.1:8000
```

No se incluyen credenciales reales en el repositorio.

### Migraciones (Alembic)

```bash
cd backend
alembic upgrade head        # aplica las migraciones a la base de DATABASE_URL
alembic revision -m "..."   # nueva migración
```

La migración inicial crea `patients` y `assessments` con claves UUID
(`gen_random_uuid()`, extensión `pgcrypto`) e índices sobre `patient_id` y
`created_at`.

### Umbrales de riesgo (única fuente)

La clasificación por probabilidad es única por lado y está especificada con
valores idénticos en `backend/risk.py` y `frontend/src/riskLevels.js`:

| Nivel | Rango |
|---|---|
| Bajo | p < 0.45 |
| Medio | 0.45 <= p < 0.72 |
| Alto | p >= 0.72 |

### Despliegue (Render)

- **Web service (API):** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, con `DATABASE_URL` y `CORS_ORIGINS` apuntando al frontend.
- **Static site (frontend):** build de Vite con `VITE_API_URL` apuntando al web service.
- Ejecutar `alembic upgrade head` en el despliegue antes del primer uso.

## Tests

```bash
python -m unittest discover -s tests -v   # backend (incluye tests de persistencia con SQLite aislado)
cd frontend && npm install && npm test    # frontend (Vitest)
cd frontend && npm run build              # build de producción
```

## Future Scope

- Exploración y análisis de datos (EDA)
- Preprocesamiento y limpieza de datos
- Entrenamiento y evaluación de modelos de Machine Learning
- API REST con FastAPI para servir predicciones
- Interfaz de usuario con Vue.js
- Tests automatizados
- Despliegue y containerización
