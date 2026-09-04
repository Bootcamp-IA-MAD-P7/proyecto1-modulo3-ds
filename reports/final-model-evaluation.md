# Evaluación Final del Modelo

## 1. Objetivo

Evaluar el rendimiento final del modelo optimizado (LogisticRegression + RandomOverSampler) sobre el **Test set reservado**, de forma **exclusivamente de evaluación** (post-selección de hiperparámetros).

## 2. Modelo Evaluado

- **Modelo:** LogisticRegression + RandomOverSampler.
- **Artefacto:** `artifacts\\logistic_regression_tuned.joblib`
- **Hiperparámetros optimizados (#051):** `C=0.5`, `solver=lbfgs`, `max_iter=500`, `random_state=42`.
- El modelo se **carga** desde el artefacto; no se re-entrena en este ticket.

## 3. Dataset y División Train/Test

- **Total:** 4981 registros.
- **Train:** 3984 registros.
- **Test (reservado):** 997 registros.
- Split reproducido: `train_test_split(test_size=0.2, random_state=42, stratify=y)`.

## 4. Metodología de Evaluación

Se carga el modelo optimizado y se evalúa **exclusivamente** sobre el Test set. Se calculan Accuracy, Precision, Recall, F1, F1-macro, ROC-AUC, matriz de confusión y classification report. La atención se centra en la clase minoritaria `stroke=1`.

## 5. Resultados sobre el Test

| Métrica | Valor |
|---|---:|
| Accuracy | 0.7533 |
| Precision (stroke=1) | 0.1475 |
| Recall (stroke=1) | 0.8200 |
| F1 (stroke=1) | 0.2500 |
| F1-macro | 0.5512 |
| ROC-AUC | 0.8395 |

## 6. Classification Report

```text
              precision    recall  f1-score   support

           0       0.99      0.75      0.85       947
           1       0.15      0.82      0.25        50

    accuracy                           0.75       997
   macro avg       0.57      0.78      0.55       997
weighted avg       0.95      0.75      0.82       997

```

## 7. Matriz de Confusión

```text
                       Predicted
                      stroke=0   stroke=1
Actual  stroke=0 (TN)        710   (FP)   237
        stroke=1 (FN)          9   (TP)    41
```

## 8. Comparación Cross-Validation vs Test

| Métrica | CV Mean | Test | Diferencia |
|---|---:|---:|---:|
| Accuracy | 0.7432 | 0.7533 | +0.0101 |
| Precision | 0.1419 | 0.1475 | +0.0056 |
| Recall | 0.8235 | 0.8200 | -0.0035 |
| F1 | 0.2421 | 0.2500 | +0.0079 |
| F1-macro | 0.5437 | 0.5512 | +0.0075 |
| ROC-AUC | 0.8361 | 0.8395 | +0.0034 |

## 9. Análisis de Generalización y Sobreajuste

**Preguntas clave:**

- **¿El Recall de stroke se mantiene?** CV=0.8235 -> Test=0.8200.
- **¿El F1 de stroke se mantiene?** CV=0.2421 -> Test=0.2500.
- **¿El F1-macro se mantiene?** CV=0.5437 -> Test=0.5512.
- **¿El ROC-AUC es similar?** CV=0.8361 -> Test=0.8395.
- **¿Existe una diferencia importante entre CV y Test?** No (dentro de lo razonable) (delta F1 = +0.0079).

**Interpretación:** la evaluación sobre el Test se basa principalmente en las métricas de la clase minoritaria (`stroke=1`) y en la comparación CV vs Test, no en la Accuracy.

## 10. Conclusión

El comportamiento observado en el Test es **consistente** con el obtenido durante la Cross-Validation (ticket #051): las métricas de la clase minoritaria (Recall, F1) y el ROC-AUC se mantienen dentro de un rango razonable en datos nunca vistos.

## 11. Limitaciones

- El Test set (997 registros) es pequeño y contiene pocos casos positivos (`stroke=1`), por lo que las métricas de la clase minoritaria tienen mayor varianza.
- Esta es una evaluación **post-selección** (final); no se usa para modificar el modelo.
- Los resultados son descriptivos del modelo sobre los datos actuales; no implican rendimiento clínico ni relación causal.