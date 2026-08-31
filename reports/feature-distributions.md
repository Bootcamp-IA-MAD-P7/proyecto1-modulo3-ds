# Informe — Distribución de las Variables

**Proyecto:** F5 RiskAI
**Etapa:** Análisis de distribuciones (EDA)
**Fuente:** `data\raw\stroke_dataset.csv`
**Total de registros:** 4981

> **Nota:** Análisis descriptivo de las distribuciones. No constituye evidencia médica ni afirmación causal.

## 1. Variables continuas

### 1.1 Métricas de forma y dispersión

| Variable | count | media | mediana | std | asimetría | curtosis | min | q1 | q3 | max | IQR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| age | 4981 | 43.42 | 45.0 | 22.663 | -0.144 | -0.995 | 0.08 | 25.0 | 61.0 | 82.0 | 36.0 |
| avg_glucose_level | 4981 | 105.944 | 91.85 | 45.075 | +1.588 | +1.753 | 55.12 | 77.23 | 113.86 | 271.74 | 36.63 |
| bmi | 4981 | 28.498 | 28.1 | 6.79 | +0.372 | -0.138 | 14.0 | 23.7 | 32.6 | 48.9 | 8.9 |

### 1.2 Posibles valores extremos (regla del IQR)

- `age`: 0 valores por debajo de -29.0 o por encima de 115.0 (0.0% del total).
- `avg_glucose_level`: 602 valores por debajo de 22.285 o por encima de 168.805 (12.09% del total).
- `bmi`: 43 valores por debajo de 10.35 o por encima de 45.95 (0.86% del total).

### 1.3 Interpretación

- **`age`:** aproximadamente simétrica (asimetría -0.14); media 43.42, mediana 45.0; rango [0.08, 82.0]; IQR 36.0; 0 posibles valores extremos (0.0%) según la regla del IQR.
- **`avg_glucose_level`:** asimetría positiva (cola hacia la derecha) (asimetría +1.59); media 105.944, mediana 91.85; rango [55.12, 271.74]; IQR 36.63; 602 posibles valores extremos (12.09%) según la regla del IQR.
- **`bmi`:** aproximadamente simétrica (asimetría +0.37); media 28.498, mediana 28.1; rango [14.0, 48.9]; IQR 8.9; 43 posibles valores extremos (0.86%) según la regla del IQR.

## 2. Variables categóricas

### 2.1. `gender`

- **Categorías presentes (2):** Female, Male
- **Categoría dominante:** `Female` (2907 registros, 58.36%).

| Categoría | Nº | % |
|---|---|---|
| Female | 2907 | 58.36 |
| Male | 2074 | 41.64 |

    → más repartida: la categoría `Female` es la más frecuente con el 58.4%, entre 2 categorías.

### 2.2. `ever_married`

- **Categorías presentes (2):** Yes, No
- **Categoría dominante:** `Yes` (3280 registros, 65.85%).

| Categoría | Nº | % |
|---|---|---|
| Yes | 3280 | 65.85 |
| No | 1701 | 34.15 |

    → concentración alta: la categoría `Yes` supone el 65.8% de los 4981 registros.

### 2.3. `work_type`

- **Categorías presentes (4):** Private, Self-employed, children, Govt_job
- **Categoría dominante:** `Private` (2860 registros, 57.42%).

| Categoría | Nº | % |
|---|---|---|
| Private | 2860 | 57.42 |
| Self-employed | 804 | 16.14 |
| children | 673 | 13.51 |
| Govt_job | 644 | 12.93 |

    → más repartida: la categoría `Private` es la más frecuente con el 57.4%, entre 4 categorías.

### 2.4. `Residence_type`

- **Categorías presentes (2):** Urban, Rural
- **Categoría dominante:** `Urban` (2532 registros, 50.83%).

| Categoría | Nº | % |
|---|---|---|
| Urban | 2532 | 50.83 |
| Rural | 2449 | 49.17 |

    → más repartida: la categoría `Urban` es la más frecuente con el 50.8%, entre 2 categorías.

### 2.5. `smoking_status`

- **Categorías presentes (4):** never smoked, Unknown, formerly smoked, smokes
- **Categoría dominante:** `never smoked` (1838 registros, 36.9%).

| Categoría | Nº | % |
|---|---|---|
| never smoked | 1838 | 36.9 |
| Unknown | 1500 | 30.11 |
| formerly smoked | 867 | 17.41 |
| smokes | 776 | 15.58 |

    → más repartida: la categoría `never smoked` es la más frecuente con el 36.9%, entre 4 categorías.

## 3. Variables binarias

``hypertension`` y ``heart_disease`` son indicadores 0/1; se reporta su frecuencia, no se tratan como variables continuas.

### 3.1. `hypertension`

| Valor | Nº | % |
|---|---|---|
| 0 | 4502 | 90.38 |
| 1 | 479 | 9.62 |

### 3.2. `heart_disease`

| Valor | Nº | % |
|---|---|---|
| 0 | 4706 | 94.48 |
| 1 | 275 | 5.52 |
