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
| Machine Learning | scikit-learn |
| Visualización | matplotlib, seaborn |
| Backend | FastAPI (futuro) |
| Frontend | Vue.js (futuro) |
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

## Future Scope

- Exploración y análisis de datos (EDA)
- Preprocesamiento y limpieza de datos
- Entrenamiento y evaluación de modelos de Machine Learning
- API REST con FastAPI para servir predicciones
- Interfaz de usuario con Vue.js
- Tests automatizados
- Despliegue y containerización
