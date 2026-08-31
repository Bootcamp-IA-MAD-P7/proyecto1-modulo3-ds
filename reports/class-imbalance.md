# Informe — Análisis de Desbalance de la Variable Objetivo

**Proyecto:** F5 RiskAI
**Etapa:** Análisis de desbalance de clases (EDA)
**Fuente:** `data\raw\stroke_dataset.csv`
**Total de registros:** 4981

> **Nota:** Este análisis describe la distribución de la variable objetivo y sus implicaciones para la evaluación del modelo. No constituye evidencia médica ni afirmación causal.

## 1. Distribución de clases

| Clase (`stroke`) | Nº registros | Porcentaje |
|---|---|---|
| 0 | 4733 | 95.02% |
| 1 | 248 | 4.98% |

- **Clase mayoritaria:** `0` (4733 registros, 95.02%).
- **Clase minoritaria:** `1` (248 registros, 4.98%).

- **Ratio de desbalance (mayoritaria / minoritaria):** 19.08x

## 2. Interpretación

La clase `0` es mayoritaria con un 95.02% de los registros, frente a un 4.98% para la clase `1`. Existe un ratio de desbalance de 19.08x, lo que implica que una evaluación ingenua de la precisión no reflejaría el rendimiento real sobre la clase minoritaria.

### Implicaciones para la evaluación del modelo

- La **accuracy global** puede ser engañosa: un modelo que siempre predijera la clase mayoritaria alcanzaría ~95.02% de acierto sin aprender nada.
- En la futura evaluación se deberán priorizar métricas que penalicen los falsos negativos de la clase minoritaria (p. ej. sensibilidad / recall, precisión, F1, y análisis de la curva ROC/PR).
- El desbalance puede requerir estrategias específicas en el modelado (muestreo, ponderación de clases, etc.). Su tratamiento queda fuera de este Issue (análisis únicamente).