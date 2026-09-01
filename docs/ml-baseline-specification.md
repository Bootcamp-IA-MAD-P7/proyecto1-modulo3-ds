# Especificación Técnica — Baseline de Machine Learning (F5 RiskAI)

**Proyecto:** F5 RiskAI
**Fase:** Machine Learning — primer baseline
**Estado:** Especificación técnica (sin entrenar / sin evaluar)
**Issue de referencia:** #016

---

## 1. Problema

F5 RiskAI es un problema de **clasificación binaria**: a partir de los atributos de
un paciente se predice si sufrió un accidente cerebrovascular (ictus).

## 2. Variable objetivo

- **Target:** `stroke`
- **Clases:**
  - `0` — no ictus
  - `1` — ictus

## 3. Dataset

- **Fuente:** `data/raw/stroke_dataset.csv` (no modificable).
- **Volumen y calidad** (verificados durante EDA #010):
  - **4981** registros
  - **11** columnas
  - **0** valores nulos
  - **0** duplicados exactos
  - `stroke = 0` ≈ **95.02%**
  - `stroke = 1` ≈ **4.98%**

> Los valores anteriores fueron verificados contra el dataset raw antes de
> redactar esta especificación.

## 4. Baseline

- **Algoritmo:** `LogisticRegression`
- **Justificación:**
  - problema de clasificación binaria;
  - modelo sencillo y rápido de entrenar;
  - interpretable (coeficientes por feature);
  - adecuado como referencia inicial;
  - permite comparar posteriormente modelos más complejos.

> **Estado:** aún **no se entrena** ningún modelo. Este documento solo define la
> especificación.

## 5. Preprocessing

Se **reutiliza** el pipeline de preprocessing existente (`scripts/preprocessing.py`).
No se crea un pipeline paralelo.

Flujo esperado:

```text
Raw dataset
    ↓
Train/Test split      (ver §6)
    ↓
preprocessing         (fit solo con Train, ver §8)
    ↓
Logistic Regression   (ver §4)
```

Composición del pipeline (fases ya implementadas):

| Tipo de variable | Variables | Transformación |
|---|---|---|
| Continuas | `age`, `avg_glucose_level`, `bmi` | `StandardScaler` |
| Binarias | `hypertension`, `heart_disease` | paso directo (ya 0/1) |
| Categóricas | `gender`, `ever_married`, `work_type`, `Residence_type`, `smoking_status` | `OneHotEncoder` (`handle_unknown="ignore"`) |

El pipeline debe **ajustarse exclusivamente con Train**; el Test no participa en
ningún paso del `fit`.

## 6. Split

- **Método:** división estratificada `train_test_split`.
- **Parámetros** (fijos y reproducibles):
  - `test_size = 0.2`
  - `random_state = 42`
  - `stratify = y` (por `stroke`, para preservar la proporción de clases)

No se define otra estrategia de split.

> Coherente con el flujo ya implementado en
> `scripts/generate_processed_data.py` (`DEFAULT_TEST_SIZE = 0.2`,
> `DEFAULT_RANDOM_STATE = 42`, `stratify=y`).

## 7. Métricas

Métricas definidas para el baseline:

- **Accuracy**
- **Precision**
- **Recall**
- **F1-score**
- **AUC-ROC**

Debido al **fuerte desbalance de clases** (~95/5), la **Accuracy no será la única
métrica relevante**. Se prestará especial atención a, de la **clase positiva
`stroke = 1`**:

- **Recall** (sensibilidad)
- **Precision**
- **F1-score**
- **AUC-ROC**

## 8. Criterio de overfitting (aceptación)

**Criterio definido:** la diferencia entre la métrica equivalente de Train y de
Test debe ser **inferior a 5 puntos porcentuales** (en valor absoluto).

**Cómo se calculará la diferencia:**

```
Diferencia = | métrica_Train − métrica_Test |
```

donde la métrica se expresa en porcentaje (0–100). El criterio se aplicará a las
métricas definidas en §7 (Accuracy, Precision, Recall, F1, AUC-ROC):

- Se evalúa el modelo sobre Train y sobre Test con la misma métrica.
- Se calcula la diferencia absoluta en puntos porcentuales.
- El baseline se considera **aceptable** si, para cada métrica,
  `Diferencia < 5.0` puntos porcentuales.

> **Nota:** aún **no se realiza** la evaluación; este es el criterio que se
> aplicará en la etapa de entrenamiento/evaluación posterior.

## 9. Feature importance (análisis posterior)

Tras el entrenamiento, se **analizarán los coeficientes de `LogisticRegression`**
sobre las features **post-preprocessing**.

Consideraciones:

- El **One-Hot Encoding** convierte cada variable categórica en **múltiples
  features** (una por categoría), por lo que cada variable categórica contribuye
  con varios coeficientes.
- Los coeficientes se interpretarán de forma **relativa** (magnitud y signo por
  feature transformada), no como importancias comparables entre variables de
  distinta escala sin mayor análisis.
- **No se interpretarán los coeficientes como causalidad.**

## 10. Desbalance

**NO se implementa todavía** ninguna técnica de balanceo:

- SMOTE
- oversampling
- undersampling
- `class_weight`

El tratamiento del desbalance será una **decisión posterior**, evaluada después
de obtener el resultado del baseline.

## 11. Data leakage

Prevención explícita:

- el **preprocessing se ajusta solo con Train**;
- el **Test no participa en el entrenamiento** (ni `fit` de preprocessing ni fit
  del modelo);
- el **Test se reserva exclusivamente para la evaluación final**;
- se **evita cualquier uso de información del Test** durante el `fit`.

Una única llamada a `train_test_split` (antes del preprocessing) garantiza que
ninguna información del Test se filtre al ajuste.

## 12. Decisiones pendientes

- Definir los hiperparámetros finales de `LogisticRegression` para el baseline.
- Decidir la estrategia de balanceo (SMOTE / oversampling / undersampling /
  `class_weight`) en función del rendimiento del baseline.
- Establecer el conjunto definitivo de métricas de reporte y sus umbrales.
- Umbral de decisión de la clase positiva (ajuste posterior del threshold).
- Plan de comparación con modelos más complejos.

---

## Criterios de aceptación de esta especificación

Debe dejar definidos:

- [x] problema
- [x] target
- [x] baseline
- [x] preprocessing
- [x] split
- [x] métricas
- [x] criterio de overfitting
- [x] análisis posterior de coeficientes
- [x] prevención de data leakage
- [x] decisiones pendientes
