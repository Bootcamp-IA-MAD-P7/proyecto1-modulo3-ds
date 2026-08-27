# Informe Técnico — Inspección del Dataset

**Proyecto:** F5 RiskAI
**Etapa:** Inspección de estructura del dataset
**Fuente:** `data/raw/stroke_dataset.csv`
**Fecha:** 2026-08-27

---

## 1. Dimensiones

| Característica | Valor |
|---|---|
| Número de filas | 4.981 |
| Número de columnas | 11 |

## 2. Columnas y tipos de datos

| Columna | Tipo de dato | Descripción |
|---|---|---|
| `gender` | `str` | Género del paciente |
| `age` | `float64` | Edad del paciente |
| `hypertension` | `int64` | Hipertensión (0 = No, 1 = Sí) |
| `heart_disease` | `int64` | Enfermedad cardíaca (0 = No, 1 = Sí) |
| `ever_married` | `str` | Si ha estado casado (Yes/No) |
| `work_type` | `str` | Tipo de trabajo |
| `Residence_type` | `str` | Tipo de residencia (Urban/Rural) |
| `avg_glucose_level` | `float64` | Nivel promedio de glucosa |
| `bmi` | `float64` | Índice de masa corporal |
| `smoking_status` | `str` | Estado de tabaquismo |
| `stroke` | `int64` | **Variable objetivo** (0 = No ictus, 1 = Ictus) |

## 3. Variables numéricas (6)

- `age`
- `hypertension`
- `heart_disease`
- `avg_glucose_level`
- `bmi`
- `stroke` (objetivo)

## 4. Variables categóricas (5)

- `gender`
- `ever_married`
- `work_type`
- `Residence_type`
- `smoking_status`

## 5. Variable objetivo

- **`stroke`** — variable binaria (0/1)
- Distribución:
  - `0` (No ictus): 4.733 (95.02%)
  - `1` (Ictus): 248 (4.98%)

## 6. Valores nulos

| Columna | Nulos |
|---|---|
| Todas | 0 |

No se detectaron valores nulos en ninguna columna.

## 7. Duplicados

- Total de filas duplicadas: **0**

## 8. Valores únicos de variables categóricas

| Columna | Conteo | Valores |
|---|---|---|
| `gender` | 2 | Female, Male |
| `ever_married` | 2 | No, Yes |
| `work_type` | 4 | Govt_job, Private, Self-employed, children |
| `Residence_type` | 2 | Rural, Urban |
| `smoking_status` | 4 | Unknown, formerly smoked, never smoked, smokes |

## 9. Resumen estadístico de variables numéricas

| Variable | min | 25% | mediana | media | 75% | max |
|---|---|---|---|---|---|---|
| `age` | 0.08 | 25.0 | 45.0 | 43.42 | 61.0 | 82.0 |
| `hypertension` | 0 | 0 | 0 | 0.096 | 0 | 1 |
| `heart_disease` | 0 | 0 | 0 | 0.055 | 0 | 1 |
| `avg_glucose_level` | 55.12 | 77.23 | 91.85 | 105.94 | 113.86 | 271.74 |
| `bmi` | 14.0 | 23.7 | 28.1 | 28.50 | 32.6 | 48.9 |
| `stroke` | 0 | 0 | 0 | 0.05 | 0 | 1 |

## 10. Observaciones

- La variable objetivo `stroke` presenta un desequilibrio importante (95% vs 5%), a considerar en etapas posteriores de modelado.
- Todas las columnas están completas (sin nulos) y no hay filas duplicadas.
- `work_type` y `smoking_status` son las variables categóricas con más categorías (4 cada una).
- `smoking_status` contiene la categoría `Unknown`, que representa información no disponible.

## 11. Alcance

Este informe se limita a la inspección de la estructura. No se ha realizado limpieza, imputación, encoding, escalado ni modelado.
