# Informe — Evaluación del Baseline de Logistic Regression

**Proyecto:** F5 RiskAI
**Fase:** Evaluación del baseline (ML)
**Artefacto evaluado:** `artifacts\logistic_regression_baseline.joblib`
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe mide el rendimiento del baseline entrenado en el Issue #017 usando las métricas de la especificación (#016). Es exclusivamente de evaluación: no modifica el modelo, no aplica balanceo ni realiza tuning.

**Nota:** las métricas no afirman causalidad ni rendimiento clínico; son resultados descriptivos del modelo sobre los datos.

## 1. Objetivo

Medir el rendimiento del modelo baseline (``LogisticRegression``) sobre Train y Test, usando exactamente el split definido en #016/#017, para dejar base para el análisis de overfitting (#020) y decisiones posteriores.

## 2. Modelo evaluado

- **Modelo:** Pipeline de scikit-learn = ``preprocessing`` + ``LogisticRegression``.
- **Preprocessing:** reutiliza `scripts/preprocessing.py` (ajustado solo con Train en #017).
- **Hiperparámetros:** ``C=1.0``, ``solver=lbfgs``, ``max_iter=100``, ``random_state=42``, ``class_weight=None`` (sin balanceo).
- **Estado:** sin modificar; no se reentrena en este Issue.

## 3. Dataset y split

- **Registros:** 4981 (sin nulos ni duplicados).
- **Target `stroke`:** `0` ≈ 95.02%, `1` ≈ 4.98% (fuerte desbalance).
- **Split:** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.
  - Train: 3984 filas.
  - Test: 997 filas.
- **Preprocessing:** ya ajustado en #017; en esta etapa no se vuelve a hacer `fit`.

_Criterio métricas:_ Precision, Recall y F1 se calculan sobre la **clase positiva `stroke = 1`** (`pos_label=1`).

## 4. Métricas Train

| Metric | Valor |
|---|---|
| Accuracy | 0.9506 |
| Precision (stroke=1) | 1.0000 |
| Recall (stroke=1) | 0.0051 |
| F1-score (stroke=1) | 0.0101 |
| AUC-ROC | 0.8463 |

## 5. Métricas Test

| Metric | Valor |
|---|---|
| Accuracy | 0.9498 |
| Precision (stroke=1) | 0.0000 |
| Recall (stroke=1) | 0.0000 |
| F1-score (stroke=1) | 0.0000 |
| AUC-ROC | 0.8459 |

## 6. Classification report

### 6.1 Train

```text
              precision    recall  f1-score   support

           0       0.95      1.00      0.97      3786
           1       1.00      0.01      0.01       198

    accuracy                           0.95      3984
   macro avg       0.98      0.50      0.49      3984
weighted avg       0.95      0.95      0.93      3984
```

### 6.2 Test

```text
              precision    recall  f1-score   support

           0       0.95      1.00      0.97       947
           1       0.00      0.00      0.00        50

    accuracy                           0.95       997
   macro avg       0.47      0.50      0.49       997
weighted avg       0.90      0.95      0.93       997
```

## 7. Comparación Train vs Test

| Metric | Train | Test |
|---|---:|---:|
| Accuracy | 0.9506 | 0.9498 |
| Precision | 1.0000 | 0.0000 |
| Recall | 0.0051 | 0.0000 |
| F1 | 0.0101 | 0.0000 |
| AUC-ROC | 0.8463 | 0.8459 |

_Nota: esta tabla se prepara aquí por conveniencia; el análisis formal del gap (overfitting) se realizará en el Issue #020._

## 8. Observaciones

- La **Accuracy** no es suficiente para interpretar el modelo dado el fuerte desbalance (4.98% de `stroke=1`): un clasificador trivial que predijera siempre `0` alcanzaría ≈95.02%.
- Se presta especial atención a **Recall / Precision / F1 de `stroke=1`** y **AUC-ROC**.
- En Test, el modelo alcanza Recall=0.0000, Precision=0.0000 y F1=0.0000 para la clase `stroke=1`, con AUC-ROC=0.8459.
- El contraste Train/Test de cada métrica queda reflejado en la tabla del apartado 7; el análisis formal del gap se aborda en el Issue #020.
- Estos valores son descriptivos del modelo sobre los datos actuales; no implican rendimiento clínico ni relación causal con el ictus.