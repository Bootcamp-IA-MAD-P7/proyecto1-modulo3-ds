# Informe Técnico — Análisis de Valores Nulos y Duplicados

**Proyecto:** F5 RiskAI
**Etapa:** Análisis de valores nulos y duplicados
**Fuente:** `data/raw/stroke_dataset.csv`
**Fecha:** 2026-08-27

---

## 1. Resumen

| Métrica | Resultado |
|---|---|
| Número de filas | 4.981 |
| Número de columnas | 11 |
| Valores nulos totales | **0** |
| Filas duplicadas (exactas) | **0** |
| Filas duplicadas (sin objetivo) | **0** |

## 2. Valores nulos por columna

| Columna | Nulos | Porcentaje |
|---|---|---|
| `gender` | 0 | 0.00% |
| `age` | 0 | 0.00% |
| `hypertension` | 0 | 0.00% |
| `heart_disease` | 0 | 0.00% |
| `ever_married` | 0 | 0.00% |
| `work_type` | 0 | 0.00% |
| `Residence_type` | 0 | 0.00% |
| `avg_glucose_level` | 0 | 0.00% |
| `bmi` | 0 | 0.00% |
| `smoking_status` | 0 | 0.00% |
| `stroke` | 0 | 0.00% |

**Columnas afectadas:** Ninguna.

> Se comprobó además que no existen cadenas que representen valores ausentes de forma textual (`N/A`, `NA`, `NaN`, `NULL`, `None`, cadena vacía `""`). El dataset está completamente limpio en cuanto a valores ausentes.

## 3. Duplicados

| Tipo de duplicado | Conteo |
|---|---|
| Filas exactamente duplicadas (todas las columnas) | 0 |
| Filas duplicadas excluyendo la variable objetivo `stroke` | 0 |

No se detectaron registros duplicados.

## 4. Hallazgos

1. **Valores nulos:** El dataset no presenta valores nulos en ninguna de sus 11 columnas.
2. **Duplicados:** No existen filas duplicadas, considerando ni todos los campos ni excluyendo la variable objetivo.
3. **Implicación:** La etapa de limpieza no requerirá imputación de valores ausentes ni eliminación de duplicados para este dataset.

## 5. Nota sobre reproducibilidad

Para reproducir este análisis:

```python
import pandas as pd

df = pd.read_csv('data/raw/stroke_dataset.csv')

# Valores nulos
print(df.isnull().sum())
print((df.isnull().sum() / len(df)) * 100)

# Duplicados
print(df.duplicated().sum())
cols = [c for c in df.columns if c != 'stroke']
print(df.duplicated(subset=cols).sum())
```

## 6. Alcance

Este informe se limita al análisis de valores nulos y duplicados. No se ha realizado limpieza, eliminación de filas ni sustitución de valores.
