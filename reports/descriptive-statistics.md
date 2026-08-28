# Informe — Estadísticas Descriptivas del Dataset

**Proyecto:** F5 RiskAI
**Etapa:** Análisis estadístico descriptivo (EDA)
**Fuente:** `data\raw\stroke_dataset.csv`
**Filas:** 4981 | **Columnas:** 11

> **Nota:** Este informe describe los datos. Ningún resultado debe interpretarse como evidencia médica ni como afirmación causal.

## 1. Variables numéricas continuas

### 1.1 Tabla de estadísticos descriptivos

| index | count | mean | median | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|---|---|
| age | 4981 | 43.42 | 45 | 22.663 | 0.08 | 25 | 45 | 61 | 82 |
| avg_glucose_level | 4981 | 105.944 | 91.85 | 45.075 | 55.12 | 77.23 | 91.85 | 113.86 | 271.74 |
| bmi | 4981 | 28.498 | 28.1 | 6.79 | 14 | 23.7 | 28.1 | 32.6 | 48.9 |

### 1.2 Interpretación

- **`age`:** media 43.4 vs mediana 45.0 (relativamente simétrica); std 22.7; rango [0.08, 82.00] (amplitud 81.92).
- **`avg_glucose_level`:** media 105.9 vs mediana 91.8 (sesgada); std 45.1; rango [55.12, 271.74] (amplitud 216.62).
- **`bmi`:** media 28.5 vs mediana 28.1 (relativamente simétrica); std 6.8; rango [14.00, 48.90] (amplitud 34.90).
- Dispersión relativa (coeficiente de variación = std/media): `age`: 0.52, `avg_glucose_level`: 0.43, `bmi`: 0.24. La variable con mayor dispersión relativa es `age` (0.52).

## 2. Variables binarias

``hypertension`` y ``heart_disease`` son indicadores binarios (0/1). No se interpretan como variables continuas; se reportan frecuencias.

### 2.1. `hypertension`

| hypertension | count | percentage |
|---|---|---|
| 0 | 4502 | 90.38 |
| 1 | 479 | 9.62 |

- **Categoría predominante:** `0` (4502 registros, 90.38%).

### 2.2. `heart_disease`

| heart_disease | count | percentage |
|---|---|---|
| 0 | 4706 | 94.48 |
| 1 | 275 | 5.52 |

- **Categoría predominante:** `0` (4706 registros, 94.48%).

## 3. Variables categóricas

### 3.1. `gender`

- **Categorías presentes:** Female, Male
- **Categoría predominante:** `Female` (2907 registros, 58.36%).

| gender | count | percentage |
|---|---|---|
| Female | 2907 | 58.36 |
| Male | 2074 | 41.64 |

    → Interpretación: las categorías se distribuyen de forma más equilibrada; la mayor es `Female` con 58.4%.

### 3.2. `ever_married`

- **Categorías presentes:** Yes, No
- **Categoría predominante:** `Yes` (3280 registros, 65.85%).

| ever_married | count | percentage |
|---|---|---|
| Yes | 3280 | 65.85 |
| No | 1701 | 34.15 |

    → Interpretación: existe una categoría claramente dominante (`Yes` con 65.8% de los 4981 registros).

### 3.3. `work_type`

- **Categorías presentes:** Private, Self-employed, children, Govt_job
- **Categoría predominante:** `Private` (2860 registros, 57.42%).

| work_type | count | percentage |
|---|---|---|
| Private | 2860 | 57.42 |
| Self-employed | 804 | 16.14 |
| children | 673 | 13.51 |
| Govt_job | 644 | 12.93 |

    → Interpretación: las categorías se distribuyen de forma más equilibrada; la mayor es `Private` con 57.4%.

### 3.4. `Residence_type`

- **Categorías presentes:** Urban, Rural
- **Categoría predominante:** `Urban` (2532 registros, 50.83%).

| Residence_type | count | percentage |
|---|---|---|
| Urban | 2532 | 50.83 |
| Rural | 2449 | 49.17 |

    → Interpretación: las categorías se distribuyen de forma más equilibrada; la mayor es `Urban` con 50.8%.

### 3.5. `smoking_status`

- **Categorías presentes:** never smoked, Unknown, formerly smoked, smokes
- **Categoría predominante:** `never smoked` (1838 registros, 36.9%).

| smoking_status | count | percentage |
|---|---|---|
| never smoked | 1838 | 36.9 |
| Unknown | 1500 | 30.11 |
| formerly smoked | 867 | 17.41 |
| smokes | 776 | 15.58 |

    → Interpretación: `Unknown` se conserva como categoría válida con 1500 registros (30.11% del total); el resto se reparte entre las tres categorías de tabaquismo.

## 4. Variable objetivo `stroke`

``stroke`` es la variable objetivo binaria: 0 = sin ictus, 1 = con ictus. El análisis profundo del desbalance corresponde al Issue #011; aquí se incluye solo el conteo básico como contexto.

| index | valor | count | percentage |
|---|---|---|---|
| 0 | 0 | 4733 | 95.02 |
| 1 | 1 | 248 | 4.98 |

    → La clase positiva (`stroke=1`) representa un 4.98% de las muestras; se estudiará su tratamiento en el Issue #011.

## 5. Observaciones automáticas y cuestiones a investigar

Las observaciones siguientes se derivan directamente de los datos. Aquellas que requieren una comprobación adicional se indican como **cuestión a investigar** y no como un hecho clínico confirmado.

- **Cuestión a investigar (`bmi`):** el rango observado es [14.0, 48.9] (min 14.0). Revisar la plausibilidad de los valores extremos; esto requiere comprobación adicional.
- **Observación (`avg_glucose_level`):** máximo 271.74 vs mediana 91.85 y media 105.944. Hay una cola de valores altos; se sugiere investigar su distribución en el Issue #011.
- **Cuestión a investigar (`age`):** valor mínimo de 0.08. Comprobar coherencia de los valores más bajos con el resto de variables.
- **Observación (`smoking_status`):** `Unknown` se conserva como categoría válida con 1500 registros (30.11% del total). Decidir su tratamiento en la etapa de modelado.
