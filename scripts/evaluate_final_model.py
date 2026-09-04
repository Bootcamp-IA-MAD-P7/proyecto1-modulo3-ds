"""Final evaluation of the optimized model (Issue #052).

This script performs the **final, post-selection evaluation** of the optimized
model (LogisticRegression + RandomOverSampler, tuned in Issue #051) using
**exclusively the reserved Test set**.

It **does NOT** re-train, re-tune or modify the model. It only loads the tuned
artifact, reproduces the established Train/Test split, evaluates on the Test set
and writes a markdown report.

Metrics computed on the Test set
--------------------------------
* Accuracy
* Precision (stroke = 1)
* Recall (stroke = 1)
* F1-score (stroke = 1)
* F1-macro
* ROC-AUC
* Confusion matrix
* Classification report

The comparison section contrasts the Test results with the out-of-fold
Cross-Validation means from Issue #051 to check generalization consistency.

Data conventions
----------------
The established split (``test_size=0.20``, ``random_state=42``,
``stratify=y``) is reproduced via ``evaluate_baseline.make_split``. The Test set
contains exactly 997 records and is used only for this final evaluation.

Run from the repository root::

    python scripts/evaluate_final_model.py [--output reports/final-model-evaluation.md]
"""

from __future__ import annotations

import argparse
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
import tune_logistic_regression as tune  # noqa: E402

DEFAULT_MODEL_PATH = os.path.join("artifacts", "logistic_regression_tuned.joblib")
DEFAULT_REPORT = os.path.join("reports", "final-model-evaluation.md")
BASELINE_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")

POSITIVE_LABEL = 1  # stroke = 1

# Optimized hyperparameters selected in Issue #051 (used only to reproduce the
# CV reference for the comparison; the loaded artifact is NOT re-trained).
OPTIMIZED_PARAMS = {
    "C": 0.5,
    "solver": "lbfgs",
    "max_iter": 500,
    "random_state": 42,
}


def load_model(path: str = DEFAULT_MODEL_PATH):
    """Load the tuned model artifact, raising a clear error if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No existe el artefacto optimizado en '{path}'. Ejecuta antes "
            f"'scripts/tune_logistic_regression.py' (Issue #051)."
        )
    return joblib.load(path)


def evaluate_on_test(df, pipeline) -> dict:
    """Evaluate the pipeline on the reserved Test set and return metrics."""
    X_train, X_test, y_train, y_test = ev.make_split(df)

    pred = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)[:, POSITIVE_LABEL]
    y_true = y_test.to_numpy()

    metrics = ev.compute_metrics(y_true, pred, proba)
    # Normalize to a consistent key set (roc_auc instead of auc_roc).
    metrics = {
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "roc_auc": metrics["auc_roc"],
        "f1_macro": round(
            float(f1_score(y_true, pred, average="macro", zero_division=0)), 4
        ),
    }
    cm = confusion_matrix(y_true, pred)
    class_report = classification_report(y_true, pred, output_dict=False, zero_division=0)

    return {
        "metrics": metrics,
        "confusion_matrix": cm,
        "classification_report": class_report,
        "y_true": y_true,
        "y_pred": pred,
    }


def cv_reference(df) -> dict:
    """Compute the out-of-fold CV summary for the optimized parameters (#051)."""
    X_train, _, y_train, _ = ev.make_split(df)
    pipe = tune.build_pipeline(OPTIMIZED_PARAMS)
    summary = tune.cross_val_summary(pipe, X_train, y_train, tune.make_cv())
    return {
        "accuracy": summary["accuracy"]["mean"],
        "precision": summary["precision_pos"]["mean"],
        "recall": summary["recall_pos"]["mean"],
        "f1": summary["f1_pos"]["mean"],
        "roc_auc": summary["roc_auc"]["mean"],
        "f1_macro": summary["f1_macro"]["mean"],
    }


_METRIC_LABELS = [
    ("accuracy", "Accuracy"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("f1", "F1"),
    ("f1_macro", "F1-macro"),
    ("roc_auc", "ROC-AUC"),
]


def _cm_cells(cm: np.ndarray) -> dict:
    tn, fp, fn, tp = cm.ravel()
    return {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def _format_cm(cm: np.ndarray, cells: dict) -> str:
    return (
        "```text\n"
        "                       Predicted\n"
        "                      stroke=0   stroke=1\n"
        f"Actual  stroke=0 (TN)      {cells['tn']:>5}   (FP) {cells['fp']:>5}\n"
        f"        stroke=1 (FN)      {cells['fn']:>5}   (TP) {cells['tp']:>5}\n"
        "```"
    )


def build_report(df, test_result, cv, n_train, n_test, model_path) -> str:
    """Compose the final-model-evaluation markdown report."""
    metrics = test_result["metrics"]
    cells = _cm_cells(test_result["confusion_matrix"])
    cm_text = _format_cm(test_result["confusion_matrix"], cells)

    L = []
    L.append("# Evaluación Final del Modelo")
    L.append("")
    L.append("## 1. Objetivo")
    L.append("")
    L.append(
        "Evaluar el rendimiento final del modelo optimizado "
        "(LogisticRegression + RandomOverSampler) sobre el **Test set reservado**, "
        "de forma **exclusivamente de evaluación** (post-selección de "
        "hiperparámetros)."
    )
    L.append("")
    L.append("## 2. Modelo Evaluado")
    L.append("")
    L.append(f"- **Modelo:** LogisticRegression + RandomOverSampler.")
    L.append("- **Artefacto:** `{0}`".format(model_path))
    L.append(
        "- **Hiperparámetros optimizados (#051):** `C=0.5`, `solver=lbfgs`, "
        "`max_iter=500`, `random_state=42`."
    )
    L.append("- El modelo se **carga** desde el artefacto; no se re-entrena en este ticket.")
    L.append("")
    L.append("## 3. Dataset y División Train/Test")
    L.append("")
    L.append(f"- **Total:** {len(df)} registros.")
    L.append(f"- **Train:** {n_train} registros.")
    L.append(f"- **Test (reservado):** {n_test} registros.")
    L.append(
        "- Split reproducido: `train_test_split(test_size=0.2, random_state=42, stratify=y)`."
    )
    L.append("")
    L.append("## 4. Metodología de Evaluación")
    L.append("")
    L.append(
        "Se carga el modelo optimizado y se evalúa **exclusivamente** sobre el "
        "Test set. Se calculan Accuracy, Precision, Recall, F1, F1-macro, ROC-AUC, "
        "matriz de confusión y classification report. La atención se centra en la "
        "clase minoritaria `stroke=1`."
    )
    L.append("")
    L.append("## 5. Resultados sobre el Test")
    L.append("")
    L.append("| Métrica | Valor |")
    L.append("|---|---:|")
    L.append(f"| Accuracy | {metrics['accuracy']:.4f} |")
    L.append(f"| Precision (stroke=1) | {metrics['precision']:.4f} |")
    L.append(f"| Recall (stroke=1) | {metrics['recall']:.4f} |")
    L.append(f"| F1 (stroke=1) | {metrics['f1']:.4f} |")
    L.append(f"| F1-macro | {metrics['f1_macro']:.4f} |")
    L.append(f"| ROC-AUC | {metrics['roc_auc']:.4f} |")
    L.append("")
    L.append("## 6. Classification Report")
    L.append("")
    L.append("```text")
    L.append(test_result["classification_report"])
    L.append("```")
    L.append("")
    L.append("## 7. Matriz de Confusión")
    L.append("")
    L.append(cm_text)
    L.append("")
    L.append("## 8. Comparación Cross-Validation vs Test")
    L.append("")
    L.append("| Métrica | CV Mean | Test | Diferencia |")
    L.append("|---|---:|---:|---:|")
    for key, label in _METRIC_LABELS:
        cv_val = cv[key]
        test_val = metrics[key]
        diff = test_val - cv_val
        L.append(f"| {label} | {cv_val:.4f} | {test_val:.4f} | {diff:+.4f} |")
    L.append("")
    L.append("## 9. Análisis de Generalización y Sobreajuste")
    L.append("")
    L.append("**Preguntas clave:**")
    L.append("")
    recall = metrics["recall"]; f1 = metrics["f1"]; macro = metrics["f1_macro"]; auc = metrics["roc_auc"]
    cv_r = cv["recall"]; cv_f1 = cv["f1"]; cv_macro = cv["f1_macro"]; cv_auc = cv["roc_auc"]
    L.append(f"- **¿El Recall de stroke se mantiene?** CV={cv_r:.4f} -> Test={recall:.4f}.")
    L.append(f"- **¿El F1 de stroke se mantiene?** CV={cv_f1:.4f} -> Test={f1:.4f}.")
    L.append(f"- **¿El F1-macro se mantiene?** CV={cv_macro:.4f} -> Test={macro:.4f}.")
    L.append(f"- **¿El ROC-AUC es similar?** CV={cv_auc:.4f} -> Test={auc:.4f}.")
    L.append(
        f"- **¿Existe una diferencia importante entre CV y Test?** "
        f"{'Sí' if abs(metrics['f1'] - cv['f1']) > 0.05 else 'No (dentro de lo razonable)'} "
        f"(delta F1 = {metrics['f1'] - cv['f1']:+.4f})."
    )
    L.append("")
    L.append(
        "**Interpretación:** la evaluación sobre el Test se basa principalmente en "
        "las métricas de la clase minoritaria (`stroke=1`) y en la comparación "
        "CV vs Test, no en la Accuracy."
    )
    L.append("")
    L.append("## 10. Conclusión")
    L.append("")
    consistent = True
    reasons = []
    if abs(metrics["recall"] - cv["recall"]) > 0.05:
        consistent = False
        reasons.append("Recall muy diferente al CV")
    if abs(metrics["f1"] - cv["f1"]) > 0.05:
        consistent = False
        reasons.append("F1 muy diferente al CV")
    if abs(metrics["roc_auc"] - cv["roc_auc"]) > 0.05:
        consistent = False
        reasons.append("ROC-AUC muy diferente al CV")
    if consistent:
        L.append(
            "El comportamiento observado en el Test es **consistente** con el "
            "obtenido durante la Cross-Validation (ticket #051): las métricas de "
            "la clase minoritaria (Recall, F1) y el ROC-AUC se mantienen dentro "
            "de un rango razonable en datos nunca vistos."
        )
    else:
        L.append(
            "El comportamiento observado en el Test **no es totalmente consistente** "
            "con la Cross-Validation. Motivos: " + "; ".join(reasons) + "."
        )
    L.append("")
    L.append("## 11. Limitaciones")
    L.append("")
    L.append(
        "- El Test set (997 registros) es pequeño y contiene pocos casos positivos "
        "(`stroke=1`), por lo que las métricas de la clase minoritaria tienen "
        "mayor varianza."
    )
    L.append(
        "- Esta es una evaluación **post-selección** (final); no se usa para "
        "modificar el modelo."
    )
    L.append(
        "- Los resultados son descriptivos del modelo sobre los datos actuales; "
        "no implican rendimiento clínico ni relación causal."
    )
    return "\n".join(L)


def evaluate_final_model(
    model_path: str = DEFAULT_MODEL_PATH,
    report_path: str = DEFAULT_REPORT,
) -> dict:
    """Run the full final evaluation and write the markdown report."""
    df = ev.load_dataset()
    pipeline = load_model(model_path)
    test_result = evaluate_on_test(df, pipeline)
    cv = cv_reference(df)

    X_train, X_test, y_train, y_test = ev.make_split(df)
    n_train = len(y_train)
    n_test = len(y_test)

    text = build_report(df, test_result, cv, n_train, n_test, model_path)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "test_metrics": test_result["metrics"],
        "confusion_matrix": test_result["confusion_matrix"].tolist(),
        "cv": cv,
        "n_train": int(n_train),
        "n_test": int(n_test),
        "report_path": report_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Final evaluation of the optimized model (Issue #052)."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, help="Tuned model artifact path.")
    parser.add_argument("--output", default=DEFAULT_REPORT, help="Report output path.")
    args = parser.parse_args()

    result = evaluate_final_model(model_path=args.model, report_path=args.output)
    print("Evaluación final completada")
    print("  Test metrics:", result["test_metrics"])
    print("  Confusion matrix:", result["confusion_matrix"])
    print("  n_test:", result["n_test"])
    print("  Informe:", result["report_path"])


if __name__ == "__main__":
    main()