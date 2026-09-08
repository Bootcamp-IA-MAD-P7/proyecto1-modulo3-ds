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

Ver [Despliegue en Render (DEPLOYMENT WITH RENDER)](#despliegue-en-render-deployment-with-render):
la rama incluye `render.yaml` (Blueprint) con la base de datos, el backend y
el frontend listos para crear con un solo push.

## Docker

El proyecto está dockerizado (frontend + backend + PostgreSQL) mediante
`docker-compose.yml` en la raíz. No se introducen credenciales reales en el
repositorio: todos los valores de entorno son inyectados en tiempo de
ejecución (con defaults de desarrollo en `docker-compose.yml`).

### Desarrollo local sin Docker

```bash
# Backend (desde la raíz del repo, con el entorno .venv activo)
python -m uvicorn backend.main:app --reload          # http://127.0.0.1:8000

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev                                           # http://localhost:5173
```

Necesitas un PostgreSQL alcanzable y `DATABASE_URL` definida (copia
`.env.example` a `.env`); sin base de datos la API sigue respondiendo
predicciones pero no persiste.

### Desarrollo con Docker

```bash
# Construir las imágenes
docker compose build

# Levantar los tres servicios (PostgreSQL -> backend -> frontend)
docker compose up            # en primer plano, logs visibles
# o en segundo plano:
docker compose up -d

# Detener (conserva el volumen de PostgreSQL)
docker compose down

# Detener y borrar la base de datos (volumen pgdata)
docker compose down -v
```

El primer `up` tarda unos segundos de más: el backend espera a que
PostgreSQL esté sano, aplica las migraciones y solo entonces arranca
Uvicorn. Puedes seguir el estado con `docker compose ps` y los logs con
`docker compose logs -f backend`.

### Migraciones

Las migraciones se aplican automáticamente en cada arranque del contenedor
backend (entrypoint idempotente: espera a PostgreSQL → `alembic upgrade head`
→ uvicorn). Para ejecutarlas a mano:

```bash
# Dentro del contenedor backend en marcha:
docker compose exec backend sh -c "cd /app/backend && alembic upgrade head"

# O en un contenedor efímero (útil si el backend aún no arranca):
docker compose run --rm backend alembic upgrade head
```

Desarrollando en local sin Docker:

```bash
cd backend
alembic upgrade head        # usa DATABASE_URL del entorno/.env
```

Las migraciones existentes (`backend/alembic/versions/0001_initial_schema.py`
y `0002_widen_model_metadata.py`) funcionan sobre un PostgreSQL limpio: se
aplican desde cero en el volumen recién creado del contenedor.

### URLs locales (Docker)

| Servicio | URL |
|---|---|
| Frontend (Nginx) | http://localhost:8080 |
| Backend (FastAPI) | http://localhost:8000 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |
| PostgreSQL | no expuesto al host (solo red interna). Consola: `docker compose exec postgres psql -U riskai -d f5_riskai` |

### Cómo se comunican los tres servicios

- Dentro de la red de Compose los nombres de servicio son los hostnames:
  `postgres:5432`, `backend:8000`, `frontend:80`. **Nada usa `localhost`
  entre contenedores.**
- **Frontend → Backend:** el navegador del usuario (en la máquina host)
  llama a la API por su puerto publicado `http://localhost:8000`; ese valor se
  hornea en el bundle porque `VITE_API_URL` es **variable de build de Vite**
  (ARG `VITE_API_URL` en `frontend/Dockerfile`). En Render se reconstruye la
  imagen con `VITE_API_URL=https://<api>.onrender.com`. CORS se controla con
  `CORS_ORIGINS` (default en Docker: `http://localhost:8080`).
- **Backend → PostgreSQL:** `DATABASE_URL` apunta al hostname `postgres`

### Variables de entorno

| Variable | Para quién | Ejemplo (Docker) | Notas |
|---|---|---|---|
| `POSTGRES_USER` | postgres | `riskai` | default de compose |
| `POSTGRES_PASSWORD` | postgres | `riskai_dev_password` | solo desarrollo; en Render usa la cadena de Render |
| `POSTGRES_DB` | postgres | `f5_riskai` | default de compose |
| `DATABASE_URL` | backend | `postgresql+psycopg://riskai:riskai_dev_password@postgres:5432/f5_riskai` | la da Render en producción |
| `CORS_ORIGINS` | backend | `http://localhost:8080,http://127.0.0.1:8080` | separadas por comas |
| `VITE_API_URL` | frontend (build) | `http://localhost:8000` | se hornea en el bundle en `npm run build` |
| `FRONTEND_PORT` | host (opcional) | `8080` | puerto local del frontend |

Los valores se interpolan desde un archivo `.env` local si existe (copia
`.env.example`). No hace falta `.env` para levantar el stack: los defaults
son de desarrollo.

### Preparación para Render (DEPLOYMENT WITH RENDER)

La rama incluye `render.yaml` (Blueprint de Render): un solo push crea la
base de datos, el backend y el frontend. Las dos variables que dependen de
las URL públicas que Render asigna (`CORS_ORIGINS`, `VITE_API_URL`) se piden
durante la creación del Blueprint (`sync: false`); en el repositorio no se
inventa ningún dominio ni credencial.

#### Arquitectura en Render

| Servicio | Tipo | Imagen / entrypoint | Healthcheck |
|---|---|---|---|
| `f5-riskai-db` | PostgreSQL administrada (privada) | instancia Render | — |
| `f5-riskai-backend` | Web Service (Docker) | `backend/Dockerfile` → espera PG → `alembic upgrade head` → uvicorn en `$PORT` | `/health` |
| `f5-riskai-frontend` | Web Service (Docker) | `frontend/Dockerfile` → renderiza nginx en `$PORT` → sirve el SPA | `/healthz` |

Los entrypoints ya ejecutan todo en el arranque del contenedor; los
comandos equivalentes en Render serían:

- **Backend:** espera de PostgreSQL, `alembic upgrade head` y
  `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend:** Nginx sirviendo `dist/` con fallback SPA, escuchando en
  `$PORT`. `VITE_API_URL` se hornea en el build (Render traduce las
  variables de entorno del servicio a *build args* del Dockerfile; el
  Dockerfile ya la consume como `ARG VITE_API_URL`).

#### Variables de entorno en Render

| Variable | Servicio | Origen | Ejemplo |
|---|---|---|---|
| `DATABASE_URL` | backend | `fromDatabase` (automática) | la cadena `Internal Database URL` de la instancia |
| `CORS_ORIGINS` | backend | manual (`sync: false`) | `https://f5-riskai-frontend.onrender.com` |
| `VITE_API_URL` | frontend (build) | manual (`sync: false`) | `https://f5-riskai-backend.onrender.com` |

> Las URL de ejemplo son las que Render asigna por defecto a partir del
> `name` de cada servicio. Si usas un dominio personalizado, pon ese dominio
> en `CORS_ORIGINS` y `VITE_API_URL`. Varios orígenes CORS se separan con
> comas, sin espacios.

#### Pasos (13)

1. **Push de la rama** con `render.yaml` al repositorio de GitHub (por
   ejemplo `feature/docker-deployment`, o `main` tras el merge).
2. **PostgreSQL:** el Blueprint crea `f5-riskai-db` automáticamente (plan
   free, solo red interna, `ipAllowList` vacío). Si prefieres una instancia
   creada a mano en el Dashboard, sustituye el `name` en `render.yaml`.
3. **Backend:** el Blueprint crea el Web Service `f5-riskai-backend` desde
   `backend/Dockerfile` (no hace falta comando: usa el entrypoint de la
   imagen).
4. **DATABASE_URL:** Render la completa automáticamente desde la base de
   datos (`fromDatabase` → `connectionString`). No la rellenes a mano.
5. **CORS_ORIGINS:** durante la creación del Blueprint, Render pide el
   valor: escribe la URL pública del frontend (por defecto
   `https://f5-riskai-frontend.onrender.com`).
6. **Frontend:** el Blueprint crea el Web Service `f5-riskai-frontend`
   desde `frontend/Dockerfile`.
7. **VITE_API_URL:** Render la pide durante la creación: la URL pública del
   backend (por defecto `https://f5-riskai-backend.onrender.com`), sin
   barra final. Al ser variable de build, cambiarla después → Render
   reconstruye la imagen automáticamente.
8. **Migraciones:** el entrypoint del backend ejecuta `alembic upgrade head`
   en cada arranque (idempotente). Revisa en los logs del primer deploy que
   aparece `[entrypoint] Applying Alembic migrations ...` sin errores.
9. **Healthcheck API:** abre `https://f5-riskai-backend.onrender.com/health`
   → debe responder `{"status":"ok","model_available":true}`.
10. **Abrir la aplicación:** `https://f5-riskai-frontend.onrender.com`.
11. **Probar una predicción** en el dashboard (cualquier caso de ejemplo).
12. **Revisar Pacientes:** el paciente del caso probado debe aparecer con su
    última evaluación.
13. **Revisar Historial** y descargar el **PDF** del detalle: el informe se
    abre con los datos reales de la evaluación.

#### Notas

- El modelo se carga desde `artifacts/logistic_regression_tuned.joblib` al
  arrancar el backend; Render no entrena nada (solo sirve).
- PostgreSQL no queda expuesta a Internet: los servicios de Render la
  alcanzan por la red interna de la cuenta.
- Sin secretos en el repositorio: `render.yaml` declara únicamente
  `sync: false` para los dos valores manuales; `.env` está en `.gitignore`.
- Cambiar de plan (free → paid) o de dominio no requiere cambios de código:
  se actualizan `CORS_ORIGINS` y `VITE_API_URL` en el Dashboard y Render
  reconstruye.

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
