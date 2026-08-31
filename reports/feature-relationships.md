# Informe — Relación de las Variables con `stroke`

**Proyecto:** F5 RiskAI
**Etapa:** Análisis de relaciones con la variable objetivo (EDA)
**Fuente:** `data\raw\stroke_dataset.csv`
**Comparación:** `stroke = 0` (n=4733) frente a `stroke = 1` (n=248)

> **Nota:** Análisis descriptivo de asociaciones. **Correlación no implica causalidad**; no constituye evidencia médica.

## 1. Variables continuas vs. `stroke`

| Variable | media (0) | mediana (0) | media (1) | mediana (1) | Δ media | Cohen's d |
|---|---|---|---|---|---|---|
| age | 42.141 | 43.0 | 67.82 | 71.0 | +25.678 | +1.169 |
| avg_glucose_level | 104.569 | 91.45 | 132.176 | 105.04 | +27.607 | +0.618 |
| bmi | 28.41 | 28.0 | 30.187 | 29.45 | +1.777 | +0.262 |

### Interpretación (Cohen's d)

- **`age`:** media mayor en la clase `1` (Δ +25.678 puntos: 42.141 vs 67.82); Cohen's d = +1.169 (efecto grande).
- **`avg_glucose_level`:** media mayor en la clase `1` (Δ +27.607 puntos: 104.569 vs 132.176); Cohen's d = +0.618 (efecto medio).
- **`bmi`:** media mayor en la clase `1` (Δ +1.777 puntos: 28.41 vs 30.187); Cohen's d = +0.262 (efecto pequeño).

## 2. Variables binarias vs. `stroke`

| Variable | tasa en `0` | tasa en `1` | Δ tasa |
|---|---|---|---|
| hypertension | 0.087 | 0.266 | +0.179 |
| heart_disease | 0.048 | 0.190 | +0.141 |

### Interpretación

- **`hypertension`:** prevalencia del indicador del 26.6% en la clase `1` frente al 8.7% en la clase `0` (Δ +0.179 en tasa).
- **`heart_disease`:** prevalencia del indicador del 19.0% en la clase `1` frente al 4.8% en la clase `0` (Δ +0.141 en tasa).

## 3. Variables categóricas vs. `stroke`

### 3.1. `gender`

Distribución de cada categoría dentro de cada clase (%). `shift_pp` = diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto : 2.01 pp.

| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |
|---|---|---|---|---|---|
| Female | 2767 | 140 | 58.46 | 56.45 | -2.01 |
| Male | 1966 | 108 | 41.54 | 43.55 | +2.01 |

### 3.2. `ever_married`

Distribución de cada categoría dentro de cada clase (%). `shift_pp` = diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto : 23.63 pp.

| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |
|---|---|---|---|---|---|
| No | 1672 | 29 | 35.33 | 11.69 | -23.63 |
| Yes | 3061 | 219 | 64.67 | 88.31 | +23.63 |

### 3.3. `work_type`

Distribución de cada categoría dentro de cada clase (%). `shift_pp` = diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto : 13.37 pp.

| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |
|---|---|---|---|---|---|
| Govt_job | 611 | 33 | 12.91 | 13.31 | +0.40 |
| Private | 2712 | 148 | 57.3 | 59.68 | +2.38 |
| Self-employed | 739 | 65 | 15.61 | 26.21 | +10.60 |
| children | 671 | 2 | 14.18 | 0.81 | -13.37 |

### 3.4. `Residence_type`

Distribución de cada categoría dentro de cada clase (%). `shift_pp` = diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto : 3.79 pp.

| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |
|---|---|---|---|---|---|
| Rural | 2336 | 113 | 49.36 | 45.56 | -3.79 |
| Urban | 2397 | 135 | 50.64 | 54.44 | +3.79 |

### 3.5. `smoking_status`

Distribución de cada categoría dentro de cada clase (%). `shift_pp` = diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto : 11.75 pp.

| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |
|---|---|---|---|---|---|
| Unknown | 1453 | 47 | 30.7 | 18.95 | -11.75 |
| formerly smoked | 797 | 70 | 16.84 | 28.23 | +11.39 |
| never smoked | 1749 | 89 | 36.95 | 35.89 | -1.07 |
| smokes | 734 | 42 | 15.51 | 16.94 | +1.43 |

