# Informe — Análisis de Overfitting del Baseline

**Proyecto:** F5 RiskAI
**Fase:** Análisis de overfitting (ML)
**Artefacto evaluado:** `artifacts\logistic_regression_baseline.joblib`
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe compara el rendimiento del baseline en Train vs Test aplicando el criterio de la especificación (#016). Exclusivamente de análisis de overfitting; no modifica el modelo ni aplica balanceo/tuning.

## 1. Objetivo

Determinar si el baseline (``LogisticRegression``, #017) presenta overfitting, comparando sus métricas en Train y Test y aplicando el criterio definido en #016: diferencia < 5 puntos porcentuales.

## 2. Modelo evaluado

- Pipeline = ``preprocessing`` + ``LogisticRegression`` (artefacto #017), cargado tal cual.
- **Estado:** sin modificar; no se reentrena ni ajusta.

## 3. Dataset y split

- 4981 registros; target `stroke`: `0`≈95.02%, `1`≈4.98%.
   - Train: 3984 filas.
   - Test: 997 filas.
- **Split:** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.
- **Criterio métricas:** Precision/Recall/F1 sobre clase positiva `stroke=1`.

## 4. Métricas Train/Test

| Metric | Train | Test | Gap (pp) | Criterio |
|---|---|---:|---:|---:|

| Accuracy | 0.9506 | 0.9498 | 0.08 | PASS |
| Precision (stroke=1) | 1.0000 | 0.0000 | 100.00 | FAIL |
| Recall (stroke=1) | 0.0051 | 0.0000 | 0.51 | PASS |
| F1-score (stroke=1) | 0.0101 | 0.0000 | 1.01 | PASS |
| AUC-ROC | 0.8463 | 0.8459 | 0.04 | PASS |

## 5. Tabla de gaps

El gap se calcula como ``gap_pp = abs(metric_train - metric_test) * 100`` (en **puntos porcentuales**).

| Métrica | Gap (pp) |
|---|---|
| accuracy | 0.08 |
| precision | 100.00 |
| recall | 0.51 |
| f1 | 1.01 |
| auc_roc | 0.04 |

## 6. Criterio de aceptación

Según #016, el modelo **cumple el criterio de overfitting** cuando la diferencia entre Train y Test es **inferior a 5 puntos porcentuales** para cada métrica.

## 7. Resultado PASS/FAIL

| Métrica | Resultado |
|---|---|
| accuracy | PASS |
| precision | FAIL |
| recall | PASS |
| f1 | PASS |
| auc_roc | PASS |

## 8. Interpretación

- **Sobre overfitting (strict):** aplicando el criterio métrica a métrica obtenemos accuracy=0.08 pp (PASS), precision=100.00 pp (FAIL), recall=0.51 pp (PASS), f1=1.01 pp (PASS), auc_roc=0.04 pp (PASS). La mayoría de métricas **PASS**; únicamente **Precision** cumple FAIL por su gap (100.00 pp).
- **Distinción clave:** el **FAIL de Precision NO implica overfitting**. Se debe a que el baseline no predice ninguna clase positiva en Test (TP=0), por lo que Precision=0.0 en Test mientras que en Train alcanza 1.0 con un único TP. Es un **efecto del desbalance** en la clase minoritaria, no una falta de generalización.
- **Bajo Recall de `stroke=1` no es overfitting:** el Recall es bajo en Train y en Test por igual (≈ 0), señalando **bajo rendimiento en la clase minoritaria**, favorecido por el desbalance (~95/5).
- **Relación con #019:** la matriz de confusión mostró que el modelo predice casi siempre la clase `0` (en Test: TP=0, FN=50); eso se refleja en Precision=0 y Recall≈0 en Test.
- Las métricas **Accuracy (0.08 pp), Recall (0.51 pp), F1 (1.01 pp) y AUC-ROC (0.04 pp)** muestran gaps muy reducidos, apuntando a **baja evidencia de overfitting** salvo el caso degenerado de Precision.
- Estos resultados son descriptivos del modelo sobre los datos; no implican rendimiento clínico ni relación causal.

## 9. Conclusión

El baseline **no presenta evidencia real de overfitting**: las métricas relevantes (Accuracy, Recall, F1, AUC-ROC) muestran gaps < 5 pp y estables. El **FAIL de Precision** es un artefacto del desbalance (ninguna predicción positiva en Test), no sobreajuste. La principal limitación es el **bajo Recall de la clase minoritaria** (`stroke=1`), consecuencia del **desbalance** del dataset, que deberá abordarse con estrategias de balanceo o umbral en Issues posteriores.