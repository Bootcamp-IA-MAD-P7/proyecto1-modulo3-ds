# Model Comparison Report

**Proyecto:** F5 RiskAI
**Fase:** Documentación — comparación y justificación del modelo (ML, Issue #054)
**Fuente de datos:** `data\raw\stroke_dataset.csv`
**Última revisión:** documentos #048–#053 (evaluación del desbalance → test de cobertura)

> Este informe reúne el proceso completo de **selección y justificación del modelo** del prototipo F5 RiskAI, desde la evaluación del desbalance hasta la evaluación final sobre el Test reservado. Todas las métricas provienen exclusivamente de los informes ya generados en el proyecto (`reports/cross-validation.md`, `reports/model-comparison.md`, `reports/hyperparameter-tuning.md`, `reports/final-model-evaluation.md`); no se inventan ni se modifican valores.

> **Nota importante:** las métricas no implican rendimiento clínico ni relación causal. Este prototipo **no sustituye la evaluación médica**.

---

## 1. Executive Summary

F5 RiskAI es un prototipo de Machine Learning cuyo objetivo es estimar el **riesgo de ictus (stroke)** a partir de datos tabulares de pacientes.

El dataset presenta un **fuerte desbalance de clases** (~95% clase 0 / ~5% clase 1): detectar la clase minoritaria (`stroke=1`) es el objetivo principal, por lo que **no** se puede evaluar el modelo únicamente por Accuracy.

Se evaluaron cuatro familias de modelos candidatos (Logistic Regression, LinearSVC calibrado, ComplementNB y LightGBM), todos con **RandomOverSampler (ROS)** dentro del pipeline como mitigación del desbalance, y se compararon mediante **Stratified 5-Fold Cross-Validation** (out-of-fold). El modelo seleccionado fue:

> **Logistic Regression + RandomOverSampler**, con hiperparámetros `C=0.5`, `solver=lbfgs`, `max_iter=500`, `random_state=42`.

Sobre el Test reservado (997 registros) alcanzó: **Accuracy = 0.7533**, **Recall(stroke) = 0.82**, **F1(stroke) = 0.25**, **F1-macro = 0.5512**, **ROC-AUC = 0.8395**, detectando 41 de los 50 casos reales de ictus del Test.

## 2. Dataset and Evaluation Strategy

- **Dataset:** tabular, 4981 registros.
- **Target binario:** `stroke` (1 = ictus).
- **Desbalance:** ~95% clase 0 / ~5% clase 1 (4.98% positivos).
- **Split reproducido:** `train_test_split(test_size=0.20, random_state=42, stratify=y)`.
  - Train: 3984 registros (198 positivos).
  - Test (reservado): 997 registros (50 positivos).
- **Estrategia de evaluación:** el Test se mantiene **reservado** hasta la evaluación final (post-selección). La selección de estrategia, modelo e hiperparámetros se realiza sobre el **Train** mediante **StratifiedKFold(5, shuffle=True, random_state=42)** con métricas out-of-fold.

## 3. Imbalance Mitigation

El **baseline** de Logistic Regression entrena a ignorar por completo la clase minoritaria: sobre Validación obtiene **Recall(stroke) ≈ 0.00** (no detecta ningún caso de ictus), a pesar de tener una Accuracy alta (~0.95) debida al desbalance.

Se compararon cuatro estrategias sobre un subset de Validación (derivado de Train, sin tocar Test):

| Estrategia | Accuracy | Precision | Recall | F1 | F1-macro | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Baseline (umbral 0.50) | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.4871 | 0.8423 |
| class_weight='balanced' | 0.7458 | 0.1412 | 0.8000 | 0.2400 | 0.5437 | 0.8367 |
| Umbral óptimo @0.50 | 0.9498 | 0.0000 | 0.0000 | 0.0000 | 0.4871 | 0.8423 |
| **RandomOverSampler** | 0.7508 | 0.1437 | **0.8000** | **0.2437** | **0.5473** | 0.8364 |

**¿Por qué se seleccionó ROS?** Porque mejoró de forma considerable la detección de la clase minoritaria — alcanzando `Recall(stroke)=0.80` y `F1(stroke)=0.2437` sobre Validación — con el mejor F1 de `stroke` entre las estrategias, manteniendo un ROC-AUC comparable al baseline. El ajuste de `class_weight='balanced'` fue cercano, pero el oversampling obtuvo el mejor F1 de la clase positiva.

## 4. Candidate Models

Se entrenaron cuatro modelos candidatos (todos con RandomOverSampler **dentro del pipeline**, es decir, aplicado únicamente al fold de entrenamiento para evitar fuga de datos):

1. **Logistic Regression + ROS** — modelo lineal, estable y de baja varianza.
2. **LinearSVC + CalibratedClassifierCV + ROS** — SVM lineal con calibración de probabilidades (sigmoid).
3. **ComplementNB + ROS** — Naive Bayes multinomial (usa MinMaxScaler por su requerimiento de features no-negativas).
4. **LightGBM + ROS** — Gradient boosting sobre árboles.

**DeBERTa-v3-small NO se utilizó:** el dataset disponible es **tabular** y **no contiene una columna de texto**. No se inventaron datos ni se creó texto artificial para entrenarlo.

## 5. Cross-Validation Results

Comparación mediante **Stratified 5-Fold Cross-Validation / out-of-fold** sobre el Train (media entre folds). Accuracy, Precision, Recall y F1 corresponden a la clase positiva `stroke=1`:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|---|---:|---:|---:|---:|---:|---:|
| Original Baseline | 0.9506 | 0.2000 | 0.0050 | 0.0098 | 0.8375 | 0.4922 |
| **LogisticRegression + ROS** | 0.7432 | 0.1413 | **0.8183** | **0.2409** | 0.8360 | 0.5431 |
| LinearSVC + ROS | 0.7452 | 0.1403 | 0.8032 | 0.2388 | 0.8371 | 0.5429 |
| ComplementNB + ROS | 0.5874 | 0.0823 | 0.7226 | 0.1478 | 0.7386 | 0.4375 |
| LightGBM + ROS | 0.9064 | 0.1548 | 0.2017 | 0.1750 | 0.7920 | **0.5627** |

**Estabilidad (desviación estándar entre folds):**

| Model | Acc Std | Prec Std | Rec Std | F1 Std | AUC Std | Macro Std |
|---|---:|---:|---:|---:|---:|---:|
| Original Baseline | 0.0006 | 0.4000 | 0.0100 | 0.0195 | 0.0252 | 0.0098 |
| **LogisticRegression + ROS** | 0.0151 | 0.0145 | **0.0772** | 0.0242 | 0.0278 | 0.0162 |
| LinearSVC + ROS | 0.0137 | 0.0163 | 0.0894 | 0.0274 | 0.0273 | 0.0174 |
| ComplementNB + ROS | 0.0248 | 0.0085 | 0.1030 | 0.0157 | 0.0409 | 0.0120 |
| LightGBM + ROS | 0.0072 | 0.0636 | 0.0878 | 0.0739 | 0.0268 | 0.0386 |

El **baseline** apenas detecta la clase minoritaria (Recall ≈ 0.005). Todos los modelos con ROS mejoran drásticamente el Recall de `stroke`, manteniendo un ROC-AUC comparable al baseline.

## 6. Model Selection

El modelo seleccionado fue **Logistic Regression + RandomOverSampler**. La selección **no se basó en Accuracy**, sino en el equilibrio de las métricas relevantes para el objetivo del prototipo (detectar casos de ictus):

- **Recall de la clase positiva:** mejor valor entre los candidatos (**0.8183**).
- **F1 de `stroke`:** mejor valor (**0.2409**).
- **ROC-AUC:** comparable al baseline (**0.8360** vs 0.8375).
- **Estabilidad entre folds:** menor variabilidad de Recall entre folds (**std 0.0772**) que LinearSVC (0.0894) o ComplementNB (0.1030).
- **Equilibrio general:** el mejor score compuesto que pondera Recall, F1, F1-macro y ROC-AUC (0.5936, frente a 0.5886 de LinearSVC, 0.4963 de ComplementNB, 0.3840 de LightGBM y 0.2704 del baseline).

**¿Por qué NO LightGBM, pese a tener el mejor F1-macro (0.5627)?** Porque su **Recall de `stroke` fue muy bajo (~0.20)**: a pesar de optimizar la métrica macro, deja de detectar la mayor parte de los casos reales de ictus, lo que contradice el objetivo principal del prototipo. Un F1-macro alto sin un buen Recall de la clase minoritaria no es suficiente.

ComplementNB mostró el peor rendimiento en la clase minoritaria y LinearSVC, aunque muy cercano a Logistic Regression, no lo superó en las métricas prioritarias.

## 7. Hyperparameter Optimization

Se aplicó **GridSearchCV** sobre el pipeline del modelo ganador (`Preprocessing → RandomOverSampler → LogisticRegression`), con **StratifiedKFold(5, shuffle=True, random_state=42)** y selección mediante **F1 de la clase positiva (stroke=1)** — **no** por Accuracy.

**Mejores hiperparámetros:**

| Parámetro | Valor |
|---|---|
| C | 0.5 |
| solver | lbfgs |
| max_iter | 500 |
| random_state | 42 |

**Mejora del candidato baseline al modelo tunado** (CV out-of-fold):

| Métrica | Candidato baseline | Modelo tunado | Δ |
|---|---:|---:|---:|
| Accuracy | 0.7432 | 0.7432 | +0.0000 |
| Precision | 0.1413 | 0.1419 | +0.0006 |
| Recall | 0.8183 | 0.8235 | +0.0052 |
| F1 | 0.2409 | 0.2421 | +0.0012 |
| ROC-AUC | 0.8360 | 0.8361 | +0.0001 |
| F1-macro | 0.5431 | 0.5437 | +0.0006 |

La mejora fue **pequeña pero positiva** en las métricas de la clase minoritaria, con un coste de complejidad nulo (misma familia de modelo).

## 8. Final Test Evaluation

El modelo optimizado se evaluó **una sola vez** sobre el Test reservado (997 registros), de forma exclusivamente de evaluación:

| Métrica | Valor |
|---|---:|
| Accuracy | 0.7533 |
| Precision (stroke=1) | 0.1475 |
| Recall (stroke=1) | 0.8200 |
| F1 (stroke=1) | 0.2500 |
| F1-macro | 0.5512 |
| ROC-AUC | 0.8395 |

**Matriz de confusión:**

| | Pred: stroke=0 | Pred: stroke=1 |
|---|---|---:|
| **Actual: stroke=0** | TN = 710 | FP = 237 |
| **Actual: stroke=1** | FN = 9 | TP = 41 |

**En lenguaje sencillo:** de los **50 casos reales de ictus** en el Test, el modelo **detectó 41** (TP) y **omitió 9** (FN). De los 947 casos sin ictus, **acertó 710** (TN) y marcó **237 falsos positivos** (FP). Es decir, el modelo es bueno capturando casos de riesgo (Recall alto) pero genera bastantes falsas alarmas (Precision baja).

## 9. Generalization and Overfitting

Se comparó el rendimiento del modelo tuneado entre la **Cross-Validation** y el **Test**:

| Métrica | CV Mean | Test | Diferencia |
|---|---:|---:|---:|
| Accuracy | 0.7432 | 0.7533 | +0.0101 |
| Precision | 0.1419 | 0.1475 | +0.0056 |
| Recall | 0.8235 | 0.8200 | -0.0035 |
| F1 | 0.2421 | 0.2500 | +0.0079 |
| F1-macro | 0.5437 | 0.5512 | +0.0075 |
| ROC-AUC | 0.8361 | 0.8395 | +0.0034 |

Todas las diferencias principales entre CV y Test fueron **menores a 0.01**. Las métricas de la clase minoritaria se mantienen y el ROC-AUC incluso es ligeramente superior en Test. **No se observa evidencia importante de sobreajuste.**

Nota: esto no implica que el modelo sea perfecto; simplemente no muestra degradación sustancial al pasar a datos nunca vistos.

## 10. Limitations

- **Dataset desbalanceado** (~95/5%): las métricas de la clase minoritaria tienen mayor varianza e inestabilidad.
- **Precision relativamente baja de `stroke`** (≈ 0.15): muchos de los casos marcados como riesgo son falsos positivos.
- **Falsos positivos elevados** (237 de 947 no-ictus se marcan como ictus).
- **Dataset tabular**: no se explota información textual.
- **Ausencia de texto** → DeBERTa-v3-small no pudo utilizarse.
- **Métricas no implican uso clínico real**: los resultados son descriptivos del modelo sobre los datos actuales.
- **El prototipo NO sustituye la evaluación médica** y no constituye una decisión clínica.

## 11. Final Recommendation

El modelo final seleccionado es:

> **Logistic Regression + RandomOverSampler**
> con `C=0.5`, `solver=lbfgs`, `max_iter=500`, `random_state=42`.

Es la opción más adecuada para el objetivo del prototipo porque ofrece el **mejor equilibrio** entre:
- un **Recall alto de `stroke`** (0.82 en Test), priorizando la detección de los casos de riesgo;
- un **F1 de `stroke`** razonable y un **ROC-AUC** comparable al baseline (0.8395);
- **menor variabilidad** entre folds que sus competidores directos;
- y la **simplicidad e interpretabilidad** de un modelo lineal.

Aunque tiene una precisión baja y genera falsos positivos, para el objetivo de *cribado de riesgo* es preferible **detectar más casos (alto Recall)** que omitirlos. Estos resultados deben interpretarse dentro del contexto de un prototipo y nunca como un sustituto del criterio médico.
