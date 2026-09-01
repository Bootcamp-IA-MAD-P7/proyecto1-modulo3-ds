# Informe — Importancia de features del baseline

**Proyecto:** F5 RiskAI
**Fase:** Análisis de importancia de features (ML)
**Artefacto evaluado:** `artifacts\logistic_regression_baseline.joblib`
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe analiza la relevancia de las features transformadas en las decisiones del baseline ``LogisticRegression`` (#017). Es un análisis de interpretación; no modifica el modelo ni aplica balanceo/tuning.

## 1. Objetivo

Identificar qué features transformadas tienen mayor influencia en el modelo baseline de regresión logística, mediante el valor absoluto de sus coeficientes. El análisis se realiza sobre las features **después del preprocessing** (Issue #017) y es reproducible.

## 2. Modelo

- Pipeline = ``preprocessing`` + ``LogisticRegression`` (artefacto #017), cargado tal cual, sin reentrenar.
- Los coeficientes ``coef_`` corresponden a la clase positiva ``stroke=1``.

## 3. Cómo se obtienen los coeficientes

Se carga el Pipeline completo. Se accede al paso ``model`` (la ``LogisticRegression``) y se leen sus ``coef_``. Cada coeficiente se asocia con el nombre de su feature transformada usando ``get_transformed_feature_names``, que expande las variables categóricas en sus dummies (e.g. ``gender`` -> ``gender_Female``). Este informe no hardcodea nombres de features.

## 4. Tabla de coeficientes

Ordenados por ``abs_coefficient`` (mayor a menor):

| feature | coefficient | abs_coefficient |
|---|---:|---:|

| age | 1.5815 | 1.5815 |
| work_type_children | 0.5858 | 0.5858 |
| hypertension | 0.5248 | 0.5248 |
| work_type_Govt_job | -0.3031 | 0.3031 |
| work_type_Self-employed | -0.2742 | 0.2742 |
| avg_glucose_level | 0.2117 | 0.2117 |
| heart_disease | 0.2006 | 0.2006 |
| smoking_status_never smoked | -0.1971 | 0.1971 |
| smoking_status_smokes | 0.1564 | 0.1564 |
| bmi | 0.0829 | 0.0829 |
| ever_married_Yes | -0.0791 | 0.0791 |
| ever_married_No | 0.0738 | 0.0738 |
| smoking_status_formerly smoked | 0.0675 | 0.0675 |
| smoking_status_Unknown | -0.0321 | 0.0321 |
| gender_Female | -0.0185 | 0.0185 |
| work_type_Private | -0.0138 | 0.0138 |
| gender_Male | 0.0132 | 0.0132 |
| Residence_type_Rural | -0.0106 | 0.0106 |
| Residence_type_Urban | 0.0053 | 0.0053 |

## 5. Top features positivas

Coeficientes positivos **aumentan** los log-odds estimados de ``stroke=1``:

- age
- work_type_children
- hypertension
- avg_glucose_level
- heart_disease
- smoking_status_smokes
- bmi
- ever_married_No
- smoking_status_formerly smoked
- gender_Male

## 6. Top features negativas

Coeficientes negativos **disminuyen** los log-odds estimados de ``stroke=1``:

- work_type_Govt_job
- work_type_Self-employed
- smoking_status_never smoked
- ever_married_Yes
- smoking_status_Unknown
- gender_Female
- work_type_Private
- Residence_type_Rural

## 7. Interpretación

- **Signo:** un coeficiente positivo aumenta el log-odds estimado de la clase positiva ``stroke=1``; uno negativo lo disminuye. Esto se expresa en lenguaje de modelo estadístico y **no implica causalidad médica**.
- **Variables categóricas:** el One-Hot Encoding convierte cada variable categórica en varias features. Los coeficientes pertenecen a las features transformadas (p. ej. ``gender_Female``) y no a la variable original completa.
- **Variables numéricas:** las features continuas estandarizadas con ``StandardScaler`` tienen su coeficiente expresado por unidad de **desviación estándar**. No se comparan directamente coeficientes de representaciones incompatibles sin explicarlo.
- El ranking por ``abs_coefficient`` permite identificar las features de mayor peso: - age (1.5815), - work_type_children (0.5858), - hypertension (0.5248), - work_type_Govt_job (0.3031), - work_type_Self-employed (0.2742).
- Estos coeficientes son descriptivos del modelo sobre los datos; no demuestran causalidad clínica.

## 8. Limitaciones

- Los coeficientes representan **asociaciones dentro del modelo**, no causalidad.
- El One-Hot Encoding genera features separadas por categoría; una única variable original se reparte en varias columnas.
- La magnitud de un coeficiente debe interpretarse teniendo en cuenta el preprocessing (escalado estandarizado, codificación one-hot).
- 'Feature importance' aquí significa **importancia relativa dentro del modelo baseline**, no importancia clínica.
- El baseline predice casi siempre la clase mayoritaria; por ello los coeficientes describen un modelo con bajo recall de ``stroke=1`` y no deben leerse como un modelo óptimo de riesgo.

## 9. Conclusión

El análisis de coeficientes revela qué features transformadas influyen más en los log-odds estimados del baseline. La interpretación del signo y la magnitud (considerando el preprocessing aportado por Issue #017) permite comparar la relevancia relativa dentro del modelo, sin afirmar causalidad y sin modificar el artefacto.