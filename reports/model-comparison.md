# Informe — Comparación de Modelos (Ensemble)

**Proyecto:** F5 RiskAI
**Fase:** Comparación de modelos (ML, Issue #050)
**Fuente de datos:** `data\raw\stroke_dataset.csv`

> Este informe compara los modelos candidatos entrenados en #049 usando **Cross-Validation out-of-fold** sobre el conjunto de entrenamiento. El conjunto Test se mantiene reservado y NO se utiliza para seleccionar el modelo.

> **Nota:** las métricas no implican rendimiento clínico ni relación causal.

## 1. Objetivo

Identificar, mediante comparación objetiva sobre datos no utilizados para entrenar, qué modelo candidato presenta el mejor equilibrio y debería pasar a la siguiente fase de optimización.

## 2. Dataset y split

- **Total:** 4981 registros.
- **Train (CV):** 3984 registros (198 positivos).
- **Test (reservado):** 997 registros.
- **Test no se usa para seleccionar el modelo.**

## 3. Metodología

- **StratifiedKFold(5, shuffle=True, random_state=42)** sobre Train.
- Cada modelo se re-ajusta dentro de cada fold; las predicciones de validación siempre provienen de datos no vistos en el entrenamiento.
- Se informa **media y desviación estándar** por métrica a través de los 5 folds.

## 4. Modelos comparados

- **Original Baseline**.
- **LogisticRegression + ROS**.
- **LinearSVC + ROS**.
- **ComplementNB + ROS**.
- **LightGBM + ROS**.

## 5. Métricas

Accuracy, Precision, Recall, F1 (clase `stroke=1`), ROC-AUC y F1-macro. Se prioriza Recall/F1 de `stroke`, F1-macro y ROC-AUC.

## 6. Tabla de comparación (métricas out-of-fold)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |
|------|----------|-----------|--------|----|---------|----------|
| Original Baseline | 0.9506 | 0.2000 | 0.0050 | 0.0098 | 0.8375 | 0.4922 |
| LogisticRegression + ROS | 0.7432 | 0.1413 | 0.8183 | 0.2409 | 0.8360 | 0.5431 |
| LinearSVC + ROS | 0.7452 | 0.1403 | 0.8032 | 0.2388 | 0.8371 | 0.5429 |
| ComplementNB + ROS | 0.5874 | 0.0823 | 0.7226 | 0.1478 | 0.7386 | 0.4375 |
| LightGBM + ROS | 0.9064 | 0.1548 | 0.2017 | 0.1750 | 0.7920 | 0.5627 |

## 7. Desviación estándar entre folds (estabilidad)

| Model | Acc Std | Prec Std | Rec Std | F1 Std | AUC Std | Macro Std |
|---|---:|---:|---:|---:|---:|---:|
| Original Baseline | 0.0006 | 0.4000 | 0.0100 | 0.0195 | 0.0252 | 0.0098 |
| LogisticRegression + ROS | 0.0151 | 0.0145 | 0.0772 | 0.0242 | 0.0278 | 0.0162 |
| LinearSVC + ROS | 0.0137 | 0.0163 | 0.0894 | 0.0274 | 0.0273 | 0.0174 |
| ComplementNB + ROS | 0.0248 | 0.0085 | 0.1030 | 0.0157 | 0.0409 | 0.0120 |
| LightGBM + ROS | 0.0072 | 0.0636 | 0.0878 | 0.0739 | 0.0268 | 0.0386 |

## 8. Análisis por métrica

- **Mejor Recall (stroke):** LogisticRegression + ROS = 0.8183.
- **Mejor F1 (stroke):** LogisticRegression + ROS = 0.2409.
- **Mejor F1-macro:** LightGBM + ROS = 0.5627.
- **Mejor ROC-AUC:** Original Baseline = 0.8375.

## 9. Selección del modelo

El **mejor equilibrio general** (score compuesto que pondera Recall, F1, F1-macro y ROC-AUC) corresponde a **LogisticRegression + ROS**.

| Model | Score compuesto |
|---|---:|
| LogisticRegression + ROS | 0.5936 |
| LinearSVC + ROS | 0.5886 |
| ComplementNB + ROS | 0.4963 |
| LightGBM + ROS | 0.3840 |
| Original Baseline | 0.2704 |

## 10. Comparación con el baseline original

El baseline original alcanza Recall(stroke)=0.0050 y F1(stroke)=0.0098. Los modelos con ROS mejoran drásticamente la detección de la clase minoritaria manteniendo ROC-AUC comparable.

## 11. Recomendación

Se recomienda llevar **LogisticRegression + ROS** al siguiente ticket de optimización.

## 12. Verificación de artefactos (#049)

| Modelo | Existe | predict_proba | Predicción binaria |
|---|---|---|---|
| LogisticRegression + ROS | sí | sí | sí |
| LinearSVC + ROS | sí | sí | sí |
| ComplementNB + ROS | sí | sí | sí |
| LightGBM + ROS | sí | sí | sí |

## 13. Limitaciones

- La comparación se realiza re-ejecutando cada configuración en CV; los artefactos #049 quedan validados pero la selección usa out-of-fold.
- El dataset tiene fuerte desbalance; las métricas de la clase minoritaria tienen mayor varianza.
- DeBERTa-v3-small no se compara por ausencia de columna de texto.
- No se realiza tuning ni ensemble combinado en este ticket.
- Los resultados son descriptivos del modelo sobre los datos actuales; no implican rendimiento clínico ni relación causal.