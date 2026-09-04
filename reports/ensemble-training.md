# Informe — Entrenamiento de Modelos Candidatos para Ensemble

**Proyecto:** F5 RiskAI
**Fase:** Entrenamiento de modelos (ML, Issue #049)
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe documenta el entrenamiento de los modelos candidatos necesarios para construir y comparar un ensemble en el Issue #050. Cada modelo se entrena con **RandomOverSampler** para mitigar el desbalance de clases.

> **Nota:** las métricas de entrenamiento son referenciales; la comparación definitiva se realizará en #050.

## 1. Objetivo

Entrenar los modelos candidatos (LogisticRegression, LinearSVC calibrado, ComplementNB, LightGBM) y documentar su configuración, métricas de entrenamiento y artefactos generados, dejando todo preparado para la comparación en #050.

## 2. Dataset utilizado

- **Total:** 4981 registros (clase 1 = ~248).
- **Train:** 3984 registros (198 positivos, ~4.97%).
- **Test (reservado):** 997 registros (50 positivos).

## 3. Split utilizado

- **Split:** `train_test_split(test_size=0.20, random_state=42, stratify=y)` (reutilizado del baseline #017).
- **Test set:** reservado y nunca utilizado durante el entrenamiento.

## 4. Modelos entrenados

| # | Modelo | Artefacto | Tiempo |
|---|---|---|---:|
| 1 | LogisticRegression | `artifacts\logistic_regression_ensemble.joblib` | 0.09s |
| 2 | LinearSVC (calibrated) | `artifacts\linear_svc_calibrated.joblib` | 0.09s |
| 3 | ComplementNB | `artifacts\complement_nb_ensemble.joblib` | 0.04s |
| 4 | LightGBM | `artifacts\lightgbm_ensemble.joblib` | 3.88s |
| — | DeBERTa-v3-small | *(no entrenado)* | — |

## 5. Estrategia de desbalance

Todos los modelos tabulares utilizan **RandomOverSampler** aplicado dentro de un ``imblearn.Pipeline``, garantizando que el oversampling se ejecuta **únicamente sobre los datos de entrenamiento** de cada fold (sin leakage).

- **sampling_strategy:** auto (balancea la clase minoritaria).
- **random_state:** 42.

## 6. Configuración principal de cada modelo

### 6.1 LogisticRegression

- **Preprocessing:** StandardScaler + OneHotEncoder (mismo que baseline).
- **Hiperparámetros:** C=1.0, solver='lbfgs', max_iter=100, random_state=42.
- **Desbalance:** RandomOverSampler.

### 6.2 LinearSVC (calibrado con CalibratedClassifierCV)

- **Preprocessing:** StandardScaler + OneHotEncoder.
- **LinearSVC:** C=1.0, max_iter=1000, random_state=42.
- **Calibración:** CalibratedClassifierCV(cv=3, method='sigmoid').
- **Desbalance:** RandomOverSampler.

### 6.3 ComplementNB

- **Preprocessing:** MinMaxScaler (features no-negativas) + OneHotEncoder.
- **Hiperparámetros:** default (alpha=1.0).
- **Desbalance:** RandomOverSampler.

### 6.4 LightGBM

- **Preprocessing:** StandardScaler + OneHotEncoder.
- **Hiperparámetros:** n_estimators=200, learning_rate=0.05, num_leaves=31.
- **Desbalance:** RandomOverSampler.

### 6.5 DeBERTa-v3-small

- **No entrenado.** El dataset no contiene una columna de texto apropiada para un modelo de lenguaje. DeBERTa requiere un corpus textual; las variables del dataset son puramente tabulares (demográficas y clínicas).

## 7. Métricas de entrenamiento

Las métricas se calculan sobre el **conjunto de entrenamiento** (referenceles). La evaluación formal se realizará en #050.

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| LogisticRegression | 0.7470 | 0.1397 | 0.7929 | 0.2375 | 0.8464 |
| LinearSVC (calibrated) | 0.7492 | 0.1402 | 0.7879 | 0.2380 | 0.8471 |
| ComplementNB | 0.6084 | 0.0893 | 0.7475 | 0.1595 | 0.7508 |
| LightGBM | 0.9736 | 0.6535 | 1.0000 | 0.7904 | 0.9999 |

## 8. Artefactos generados

| Archivo | Modelo |
|---|---|
| `artifacts\logistic_regression_ensemble.joblib` | LogisticRegression |
| `artifacts\linear_svc_calibrated.joblib` | LinearSVC (calibrated) |
| `artifacts\complement_nb_ensemble.joblib` | ComplementNB |
| `artifacts\lightgbm_ensemble.joblib` | LightGBM |

> **No se sobrescribe** el baseline existente: `artifacts/logistic_regression_baseline.joblib`.

## 9. Limitaciones

- Las métricas de entrenamiento son **referenciales** y no deben interpretarse como rendimiento generalizado.
- **DeBERTa-v3-small** no pudo entrenarse por la ausencia de una columna de texto en el dataset.
- ComplementNB utiliza MinMaxScaler (en lugar de StandardScaler) para garantizar features no-negativas. Esto puede afectar la distribución de las features continuas.
- LightGBM con oversampling puede tener un costo computacional mayor debido al aumento de muestras.
- No se realizó tuning de hiperparámetros; los valores son defaults o los mismos del baseline.

## 10. Próximo paso

Comparar los modelos entrenados en el Issue #050, evaluando su rendimiento en el conjunto de **Validación** (o mediante Cross-Validation) y seleccionando el mejor candidato para el ensemble definitivo.