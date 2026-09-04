# Informe — Hyperparameter Tuning (LogisticRegression + ROS)

**Proyecto:** F5 RiskAI
**Fase:** Optimización de hiperparámetros (ML, Issue #051)
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> El Test set se mantiene completamente reservado y **no** participa 
> en la búsqueda de hiperparámetros.

## 1. Objetivo

Optimizar los hiperparámetros del modelo ganador (**LogisticRegression + RandomOverSampler**, seleccionado en #050) mediante validación cruzada, mejorando el rendimiento sin usar el Test set.

## 2. Modelo de partida

LogisticRegression + RandomOverSampler (seleccionado en #050 por el mejor equilibrio de Recall/F1 de `stroke` y estabilidad).

## 3. Metodología

Pipeline: **Preprocessing -> RandomOverSampler -> LogisticRegression**.

- El RandomOverSampler se ejecuta `DENTRO` del pipeline (solo en el training fold de cada partición CV).
- El validation fold nunca se sobremuestrea.
- El Test set nunca participa en GridSearchCV.

## 4. Espacio de hiperparámetros

| Parámetro | Valores |
|---|---|
| `C` | `[0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]` |
| `solver` | `[lbfgs, liblinear]` |
| `max_iter` | `[500, 1000]` |

## 5. Estrategia de Cross-Validation

`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` sobre el conjunto de entrenamiento, mediante `GridSearchCV`.

## 6. Métricas utilizadas

Accuracy, Precision, Recall, F1, ROC-AUC y F1-macro. La métrica principal de selección es el **F1 de la clase positiva (stroke=1)**; la Accuracy nunca es el criterio de selección.

## 7. Mejores hiperparámetros

- **C:** `0.5`
- **solver:** `lbfgs`
- **max_iter:** `500`

## 8. Resultados del modelo baseline (sin tunear)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|------|----------|-----------|--------|----|---------|----------|
| LogisticRegression + ROS (baseline) | 0.7432 | 0.1413 | 0.8183 | 0.2409 | 0.8360 | 0.5431 |

## 9. Resultados del modelo optimizado

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|------|----------|-----------|--------|----|---------|----------|
| LogisticRegression + ROS (tuned) | 0.7432 | 0.1419 | 0.8235 | 0.2421 | 0.8361 | 0.5437 |

## 10. Comparación

| Métrica | Baseline | Optimizado | Δ |
|---|---:|---:|---:|
| Accuracy | 0.7432 | 0.7432 | +0.0000 |
| Precision | 0.1413 | 0.1419 | +0.0006 |
| Recall | 0.8183 | 0.8235 | +0.0052 |
| F1 | 0.2409 | 0.2421 | +0.0012 |
| ROC-AUC | 0.8360 | 0.8361 | +0.0001 |
| F1-macro | 0.5431 | 0.5437 | +0.0006 |

## 11. Análisis del impacto sobre Recall/F1/F1-macro

- Recall → 0.8183 → **0.8235** (+0.0052).
- F1 → 0.2409 → **0.2421** (+0.0012).
- F1-macro → 0.5431 → **0.5437** (+0.0006).

## 12. Posibles signos de overfitting

- Se evalúa mediante CV out-of-fold (no se entrena y evalúa sobre los mismos datos); esto limita el riesgo de sobreajuste a hiperparámetros.
- ROC-AUC cercano pero no extremadamente alto (≈ 0.84) sugiere que no hay sobreajuste severo a la clase mayoritaria.
- La elección de hiperparámetros se hace por F1 (clase positiva), no por accuracy, evitando un modelo trivial que prediga casi todo clase 0.

## 13. Limitaciones

- El espacio de búsqueda se limita a `C`, `solver` y `max_iter` de la LogisticRegression; no se exploran configuraciones del RandomOverSampler para no añadir complejidad innecesaria.
- Se usa GridSearchCV en lugar de RandomizedSearchCV; el espacio es pequeño (28 combinaciones) por lo que el barrido completo es factible.
- Las métricas son descriptivas de la configuración actual sobre los datos; no implican rendimiento clínico ni relación causal.

## 14. Conclusión

El ajuste de hiperparámetros (sí produce una mejora) en la métrica principal F1 de `stroke`. Véase la tabla de comparación (§10) para las variaciones por métrica.

## 15. Recomendación para el siguiente ticket

El modelo optimizado se guarda como `artifacts\\logistic_regression_tuned.joblib`. Se recomienda en el siguiente ticket evaluarlo sobre el Test set reservado (evaluación final post-selección) y valorar su integración/despliegue.