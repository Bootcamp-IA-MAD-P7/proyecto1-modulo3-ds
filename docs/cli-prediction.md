# CLI de Predicción — F5 RiskAI

## 1. Objetivo

El CLI (`scripts/predict_cli.py`) permite introducir interactivamente los datos de un paciente, validarlos, cargar el modelo baseline entrenado no alterado (#017), y mostrar la clase predicha junto con la probabilidad de `stroke=1`. Integra entrada de datos, validación, carga del modelo, preprocessing, predicción, probabilidad y presentación del resultado.

El modelo se carga tal cual; no se reentrena, ni se balancea, ni se modifica el threshold.

## 2. Cómo ejecutar la CLI

Desde la raíz del repositorio:

```
.\.venv\Scripts\python.exe scripts/predict_cli.py
```

Requiere el artefacto `artifacts/logistic_regression_baseline.joblib` (entrenado en el Issue #017). Si no existe, el CLI muestra un error claro indicando que primero debe entrenarse el modelo.

## 3. Campos solicitados

| Campo | Descripción |
|---|---|
| Gender | Sexo (`Male`/`Female`) |
| Age | Edad (numérica) |
| Hypertension | Hipertensión (`0`/`1`) |
| Heart disease | Enfermedad cardíaca (`0`/`1`) |
| Ever married | Alguna vez casado (`Yes`/`No`) |
| Work type | Tipo de trabajo |
| Residence type | Tipo de residencia (`Rural`/`Urban`) |
| Average glucose level | Nivel medio de glucosa (numérico) |
| BMI | Índice de masa corporal (numérico) |
| Smoking status | Estado de tabaquismo |

No se solicita `stroke` porque es el target.

## 4. Formatos esperados

- `gender`: `Male` | `Female`
- `age`: número
- `hypertension`: `0` | `1`
- `heart_disease`: `0` | `1`
- `ever_married`: `Yes` | `No`
- `work_type`: `Govt_job` | `Private` | `Self-employed` | `children`
- `Residence_type`: `Rural` | `Urban`
- `avg_glucose_level`: número
- `bmi`: número
- `smoking_status`: `never smoked` | `formerly smoked` | `smokes` | `Unknown`

El `gender` se solicita como `Gender [Male/Female]`.

> Los rangos de validación (edad, BMI, glucosa) son comprobaciones de entrada para evitar valores absurdos. NO son reglas médicas.

Las entradas inválidas se rechazan con un mensaje comprensible y se vuelven a solicitar; el CLI no se cierra por un error normal de entrada.

## 5. Ejemplo de ejecución

```
F5 RiskAI — Stroke Risk Prediction

Gender [Male/Female]: Female
Age [number, e.g. 45]: 45
Hypertension [0/1]: 0
Heart disease [0/1]: 1
Ever married [Yes/No]: Yes
Work type [Govt_job/Private/Self-employed/children]: Private
Residence type [Rural/Urban]: Urban
Average glucose level [number, e.g. 100]: 100
BMI [number, e.g. 25]: 25
Smoking status [never smoked/formerly smoked/smokes/Unknown]: never smoked
```

## 6. Resultado

```
-----------------------------------
F5 RiskAI — Prediction Result
-----------------------------------
Prediction: 1
Prediction: Possible positive class
Probability of stroke: 100.0%
```

La probabilidad proviene directamente del modelo (`predict_proba`), clase `stroke=1`, mostrada como porcentaje.

## 7. Advertencia de uso

Este prototipo es para análisis predictivo y **no es un diagnóstico médico**. La redacción del resultado es prudente y neutral; el modelo (baseline, sin balanceo) tiene un bajo recall de la clase minoritaria y debe interpretarse con cautela.