# Informe — Mitigación del Desbalance de Clases

**Proyecto:** F5 RiskAI
**Fase:** Mitigación del desbalance (ML, Issue #048)
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe compara estrategias para mitigar el desbalance de la clase `stroke` sobre el baseline de `LogisticRegression` (Issue #017). Todas las estrategias se evalúan sobre un **subset de Validación**; el **Test** se mantiene intacto y solo se reporta a título informativo post-selección.

> **Nota:** las métricas no implican rendimiento clínico ni relación causal.

## 1. Objetivo

Seleccionar y documentar una estrategia que **mejore el Recall y el F1 de la clase minoritaria `stroke=1`** sobre la Validación, sin sacrificar la integridad del split (no se toca Test para elegir estrategia).

## 2. Dataset y split

El dataset tiene 4981 registros con **4.98%** de casos `stroke=1` (fuerte desbalance).
- **Split base (reproducido):** `train_test_split(test_size=0.20, random_state=42, stratify=y)` (igual que #017/#018).
- **Validación (nueva, derivada de Train):** se reserva 15% estratificada del split de Train (`random_state=123`) para comparar estrategias. El conjunto de Test quedó intacto.
  - Train: 3386 filas (168 positivas).
  - Validación: 598 filas (30 positivas).
  - Test: 997 filas (50 positivas) — solo informe.
El pipeline de preprocesado se ajusta SOLO sobre Train para evitar fuga de datos.

## 3. Estrategias evaluadas

- **Baseline:** `LogisticRegression` (`class_weight=None`), umbral `0.50`.
- **class_weight:** `LogisticRegression(class_weight='balanced')`, umbral `0.50`.
- **Umbral:** baseline re-escoreado con umbral en `[0.30, 0.35, ..., 0.70]`.
- **Oversampling:** `RandomOverSampler` aplicado SOLO al fold de Train (antes de ajustar el modelo), umbral `0.50`.

## 4. Resultados principales (Validación)

| Estrategia | Acc | Prec | Rec | F1 | F1-macro | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Baseline (umbral 0.50) | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.4871 | 0.8423 |
| class_weight=balanced | 0.7458 | 0.1412 | 0.8000 | 0.2400 | 0.5437 | 0.8367 |
| Umbral óptimo @0.50 | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.4871 | 0.8423 |
| RandomOverSampler (Train) | 0.7508 | 0.1437 | 0.8000 | 0.2437 | 0.5473 | 0.8364 |

> Precision/Recall/F1 se refieren a la clase positiva `stroke=1`. El 'Umbral óptimo' corresponde al valor del barrido con mejor F1 de `stroke=1` sobre Validación.

## 5. Barrido de umbral (baseline)

| Umbral | Precision (stroke) | Recall (stroke) | F1 (stroke) |
|---:|---:|---:|---:|
| 0.30 | 0.3333 | 0.1000 | 0.1538 |
| 0.35 | 0.1667 | 0.0333 | 0.0556 |
| 0.40 | 0.0000 | 0.0000 | 0.0000 |
| 0.45 | 0.0000 | 0.0000 | 0.0000 |
| 0.50 | 0.0000 | 0.0000 | 0.0000 |
| 0.55 | 0.0000 | 0.0000 | 0.0000 |
| 0.60 | 0.0000 | 0.0000 | 0.0000 |
| 0.65 | 0.0000 | 0.0000 | 0.0000 |
| 0.70 | 0.0000 | 0.0000 | 0.0000 |

## 6. Métricas detalladas por estrategia

### Baseline (umbral 0.50)

| Metric | Valor |
|---|---|
| Accuracy | 0.9498 |
| Precision (stroke=1) | 0.0000 |
| Recall (stroke=1) | 0.0000 |
| F1-score (stroke=1) | 0.0000 |
| F1-score (macro) | 0.4871 |
| AUC-ROC | 0.8423 |
| Umbral de decisión | 0.50 |
| Matriz de confusión | `[[568, 0], [30, 0]]` |

### class_weight=balanced

| Metric | Valor |
|---|---|
| Accuracy | 0.7458 |
| Precision (stroke=1) | 0.1412 |
| Recall (stroke=1) | 0.8000 |
| F1-score (stroke=1) | 0.2400 |
| F1-score (macro) | 0.5437 |
| AUC-ROC | 0.8367 |
| Umbral de decisión | 0.50 |
| Matriz de confusión | `[[422, 146], [6, 24]]` |

### Umbral óptimo @0.50

| Metric | Valor |
|---|---|
| Accuracy | 0.9498 |
| Precision (stroke=1) | 0.0000 |
| Recall (stroke=1) | 0.0000 |
| F1-score (stroke=1) | 0.0000 |
| F1-score (macro) | 0.4871 |
| AUC-ROC | 0.8423 |
| Umbral de decisión | 0.50 |
| Matriz de confusión | `[[568, 0], [30, 0]]` |

### RandomOverSampler (Train)

| Metric | Valor |
|---|---|
| Accuracy | 0.7508 |
| Precision (stroke=1) | 0.1437 |
| Recall (stroke=1) | 0.8000 |
| F1-score (stroke=1) | 0.2437 |
| F1-score (macro) | 0.5473 |
| AUC-ROC | 0.8364 |
| Umbral de decisión | 0.50 |
| Matriz de confusión | `[[425, 143], [6, 24]]` |

## 7. Gap Train vs Validación (overfitting, informativo)

| Estrategia | Gap Acc | Gap Rec | Gap F1 |
|---|---:|---:|---:|
| Baseline | 0.09 pp | 0.60 pp | 1.18 pp |
| class_weight=balanced | 0.27 pp | 2.74 pp | 0.22 pp |
| RandomOverSampler (Train) | 0.45 pp | 0.95 pp | 0.32 pp |

## 8. Verificación en Test (post-selección, informativo)

| Estrategia | Acc | Prec | Rec | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.8453 |
| class_weight=balanced | 0.7513 | 0.1464 | 0.8200 | 0.2485 | 0.8397 |
| RandomOverSampler (Train) | 0.7543 | 0.1402 | 0.7600 | 0.2368 | 0.8389 |

## 9. Recomendación

Selección por **Recall y F1 de `stroke=1` sobre Validación** (nunca por Accuracy): mejor estrategia = **oversampling** con F1(stroke)=0.2437 y Recall(stroke)=0.8000 @0.50.

Ranking (F1 stroke desc): oversampling, class_weight, threshold@0.30, baseline.

- El resultado es **descriptivo del modelo sobre los datos actuales**; no es una decisión clínica.
- No se realizó tuning ni ensamblado; la recomendación queda documentada para un Issue posterior de modelado.