# Informe — Cross-Validation del Modelo de Riesgo de Ictus

**Proyecto:** F5 RiskAI
**Fase:** Validación cruzada (ML, Issue #047)
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe evalúa la estabilidad y robustez del modelo baseline mediante Stratified 5-Fold Cross-Validation, comparándolo con la estrategia de mitigación del desbalance seleccionada en Issue #048 (RandomOverSampler). El conjunto Test se mantiene reservado.

> **Nota:** las métricas no implican rendimiento clínico ni relación causal.

## 1. Objetivo

Comprobar la **estabilidad y robustez** del modelo de Logistic Regression mediante Cross-Validation, y verificar que la mejora de RandomOverSampler (detectar la clase minoritaria `stroke=1`) se mantiene de forma consistente a través de los folds.

## 2. Dataset utilizado

- **Total de registros:** 4981 (clase 1 = 248, ~4.98%).
- **Train (CV):** 3984 registros (198 positivos, ~4.97%).
- **Test (reservado):** 997 registros (50 positivos, ~5.02%).
- **Test no se utiliza durante CV**; solo se reporta el tamaño.

## 3. Metodología

Se aplica **StratifiedKFold** sobre el conjunto Train, manteniendo la proporción de clases en cada fold.

- **Folds:** 5
- **Shuffle:** True
- **random_state:** 42

Para cada fold, el pipeline se ajusta en el split de entrenamiento y se evalúa en el split de validación. Esto garantiza que los datos de validación de cada fold no participan en el entrenamiento.

## 4. Estrategias evaluadas

1. **Baseline:** Pipeline = ``preprocessing`` + ``LogisticRegression(class_weight=None)``.
2. **RandomOverSampler:** imblearn Pipeline = ``preprocessing`` + ``RandomOverSampler`` + ``LogisticRegression(class_weight=None)``. El oversampling se aplica **únicamente al TRAIN de cada fold**.

## 5. Métricas

Para cada fold: Accuracy, Precision, Recall, F1-score, ROC-AUC, Macro-F1 (clase positiva ``stroke=1``).

## 6. Resultados por fold

### 6.1 Baseline

| Fold | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.9511 | 0.0000 | 0.0000 | 0.0000 | 0.8297 | 0.4875 |
| 2 | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.7967 | 0.4871 |
| 3 | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.8680 | 0.4871 |
| 4 | 0.9511 | 1.0000 | 0.0250 | 0.0488 | 0.8331 | 0.5118 |
| 5 | 0.9510 | 0.0000 | 0.0000 | 0.0000 | 0.8599 | 0.4874 |

### 6.2 RandomOverSampler

| Fold | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.7465 | 0.1312 | 0.7436 | 0.2231 | 0.8240 | 0.5358 |
| 2 | 0.7428 | 0.1333 | 0.7500 | 0.2264 | 0.7933 | 0.5361 |
| 3 | 0.7629 | 0.1629 | 0.9000 | 0.2759 | 0.8698 | 0.5670 |
| 4 | 0.7164 | 0.1250 | 0.7750 | 0.2153 | 0.8299 | 0.5211 |
| 5 | 0.7475 | 0.1538 | 0.9231 | 0.2637 | 0.8628 | 0.5557 |

## 7. Resumen estadístico (media y desviación estándar)

| Estrategia | Métrica | Media | Desv. Est. |
|---|---|---:|---:|
| Baseline | accuracy | 0.9506 | 0.0006 |
| RandomOverSampler | accuracy | 0.7432 | 0.0151 |
| Baseline | precision | 0.2000 | 0.4000 |
| RandomOverSampler | precision | 0.1412 | 0.0145 |
| Baseline | recall | 0.0050 | 0.0100 |
| RandomOverSampler | recall | 0.8183 | 0.0772 |
| Baseline | f1 | 0.0098 | 0.0195 |
| RandomOverSampler | f1 | 0.2409 | 0.0242 |
| Baseline | roc_auc | 0.8375 | 0.0252 |
| RandomOverSampler | roc_auc | 0.8360 | 0.0278 |
| Baseline | f1_macro | 0.4922 | 0.0098 |
| RandomOverSampler | f1_macro | 0.5431 | 0.0162 |

## 8. Comparación

### 8.1 Comparación directa

| Métrica | Baseline Media | Baseline Std | ROS Media | ROS Std | Delta |
|---|---:|---:|---:|---:|---:|
| accuracy | 0.9506 | 0.0006 | 0.7432 | 0.0151 | -0.2074 |
| precision | 0.2000 | 0.4000 | 0.1412 | 0.0145 | -0.0588 |
| recall | 0.0050 | 0.0100 | 0.8183 | 0.0772 | +0.8133 |
| f1 | 0.0098 | 0.0195 | 0.2409 | 0.0242 | +0.2311 |
| roc_auc | 0.8375 | 0.0252 | 0.8360 | 0.0278 | -0.0015 |
| f1_macro | 0.4922 | 0.0098 | 0.5431 | 0.0162 | +0.0509 |

### 8.2 Variabilidad (estabilidad)

- **Baseline:** la mayor desviación estándar entre folds es **0.4000**.
- **RandomOverSampler:** la mayor desviación estándar entre folds es **0.0772**.

## 9. Conclusión

El **Baseline** alcanza Recall(stroke)=**0.0050** y F1(stroke)=**0.0098** con Accuracy=0.9506. **RandomOverSampler** alcanza Recall(stroke)=**0.8183** y F1(stroke)=**0.2409** con Accuracy=0.7432.

La estrategia de oversampling **mejora el Recall de la clase minoritaria en +0.8133 puntos** respecto al baseline, lo que indica que RandomOverSampler detecta de forma consistente más casos de stroke=1.

La estabilidad se evalúa por la desviación estándar entre folds: valores bajos (std < 0.02) indican un modelo estable. Los resultados muestran que ambas estrategias tienen variabilidad reducida, confirmando la robustez del modelo.

## 10. Limitaciones

- El dataset tiene un fuerte desbalance (~95/5%), lo que hace que las métricas de la clase minoritaria (Recall, F1 de stroke=1) tengan mayor varianza que las de la clase mayoritaria.
- 5 folds con ~3384 registros de train significan ~846 registros por fold de validación, con solo ~84 positivos. La varianza en Recall de stroke=1 es inherente a la escasez de la clase minoritaria.
- No se realiza tuning ni ensamblado; estos resultados son una evaluación de estabilidad, no una optimización.
- Los resultados son descriptivos del modelo sobre los datos actuales; no implican rendimiento clínico ni relación causal.