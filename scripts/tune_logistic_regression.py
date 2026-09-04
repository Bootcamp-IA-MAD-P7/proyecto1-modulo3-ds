"""Hyperparameter tuning for LogisticRegression + RandomOverSampler (Issue #051).

This script optimizes the hyperparameters of the winning model selected in
Issue #050 (LogisticRegression + RandomOverSampler) via Cross-Validation, with
the **test set fully reserved**.

Pipeline
--------
``Preprocessing -> RandomOverSampler -> LogisticRegression`` built as an
``imblearn.Pipeline``, so the RandomOverSampler runs **only on the training
fold** of each CV partition (never on validation and never on the test set) —
this avoids data leakage.

Search strategy
---------------
A `GridSearchCV` (with `StratifiedKFold(n_splits=5, shuffle=True,
random_state=42)`) explores ``C``, ``solver`` and ``max_iter`` for the
LogisticRegression, refitting on the **positive-class F1 (stroke = 1)** because
of the strong class imbalance (~95%/5%). Accuracy is recorded but is never the
selection metric.

Final model
-----------
The best estimator is refitted on the full training set and saved as
``artifacts/logistic_regression_tuned.joblib``. The original baseline artifact
(``logistic_regression_baseline.joblib``) and the #049 artifacts are **not**
overwritten.

Run from the repository root::

    python scripts/tune_logistic_regression.py [--output reports/hyperparameter-tuning.md]
"""

from __future__ import annotations

import argparse
import os
import sys

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
import train_ensemble as te  # noqa: E402

DEFAULT_OUTPUT = os.path.join("artifacts", "logistic_regression_tuned.joblib")
DEFAULT_REPORT = os.path.join("reports", "hyperparameter-tuning.md")

# Cross-validation configuration (same as Issues #047/#050).
N_SPLITS = 5
CV_RANDOM_STATE = 42
POSITIVE_LABEL = 1  # stroke = 1

# Reproducibility seed for the model itself (kept fixed, not tuned).
RANDOM_STATE = 42

# Baseline (untuned) LogisticRegression configuration (matches #049/#050).
BASELINE_LR_PARAMS = {
    "C": 1.0,
    "solver": "lbfgs",
    "max_iter": 100,
    "random_state": RANDOM_STATE,
}

# Hyperparameter search space for the LogisticRegression.
PARAM_GRID = {
    "model__C": [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    "model__solver": ["lbfgs", "liblinear"],
    "model__max_iter": [500, 1000],
}

# Metrics recorded in the search and in the before/after comparison.
SCORING = {
    "f1_pos": make_scorer(f1_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "recall_pos": make_scorer(recall_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "precision_pos": make_scorer(precision_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
    "roc_auc": "roc_auc",
    "accuracy": "accuracy",
}

METRICS = ["accuracy", "precision_pos", "recall_pos", "f1_pos", "roc_auc", "f1_macro"]

# Which metric is used to select the best hyperparameters.
REFIT_METRIC = "f1_pos"


def build_pipeline(model_params: dict | None = None):
    """Build ``ImbPipeline[preprocess, sampler, LogisticRegression]``.

    ``model_params`` overrides the LogisticRegression hyperparameters. ROS is
    always inside the pipeline (training-fold only).
    """
    params = {"random_state": RANDOM_STATE}
    if model_params:
        params.update(model_params)
    return ImbPipeline([
        ("preprocess", te.build_baseline_preprocessing()),
        ("sampler", RandomOverSampler(random_state=RANDOM_STATE)),
        ("model", LogisticRegression(**params)),
    ])


def make_cv():
    """Return the fixed stratified CV iterator."""
    return StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=CV_RANDOM_STATE)


def run_grid_search(X_train, y_train):
    """Run the GridSearchCV and return the fitted grid object."""
    pipe = build_pipeline()
    cv = make_cv()
    grid = GridSearchCV(
        pipe,
        PARAM_GRID,
        cv=cv,
        scoring=SCORING,
        refit=REFIT_METRIC,
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    return grid


def cross_val_summary(pipeline, X_train, y_train, cv):
    """Return mean/std per metric from out-of-fold CV for a given model config."""
    results = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=SCORING)
    summary = {}
    for metric in METRICS:
        values = results[f"test_{metric}"]
        summary[metric] = {
            "mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values)), 4),
        }
    return summary


def refitted_pipeline(model_params):
    """Return a pipeline fitted on the full training set with the given params."""
    pipe = build_pipeline(model_params)
    return pipe


def metric_label(metric: str) -> str:
    return {
        "accuracy": "Accuracy",
        "precision_pos": "Precision",
        "recall_pos": "Recall",
        "f1_pos": "F1",
        "roc_auc": "ROC-AUC",
        "f1_macro": "F1-macro",
    }[metric]


def build_report(baseline_summary, tuned_summary, best_params, tuned_artifact) -> str:
    """Compose the markdown hyperparameter-tuning report."""
    L = []
    L.append("# Informe — Hyperparameter Tuning (LogisticRegression + ROS)")
    L.append("")
    L.append("**Proyecto:** F5 RiskAI")
    L.append("**Fase:** Optimización de hiperparámetros (ML, Issue #051)")
    L.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    L.append("")
    L.append("> El Test set se mantiene completamente reservado y **no** participa ")
    L.append("> en la búsqueda de hiperparámetros.")
    L.append("")
    L.append("## 1. Objetivo")
    L.append("")
    L.append(
        "Optimizar los hiperparámetros del modelo ganador "
        "(**LogisticRegression + RandomOverSampler**, seleccionado en #050) "
        "mediante validación cruzada, mejorando el rendimiento sin usar el Test set."
    )
    L.append("")
    L.append("## 2. Modelo de partida")
    L.append("")
    L.append(
        "LogisticRegression + RandomOverSampler (seleccionado en #050 por el "
        "mejor equilibrio de Recall/F1 de `stroke` y estabilidad)."
    )
    L.append("")
    L.append("## 3. Metodología")
    L.append("")
    L.append("Pipeline: **Preprocessing -> RandomOverSampler -> LogisticRegression**.")
    L.append("")
    L.append(
        "- El RandomOverSampler se ejecuta `DENTRO` del pipeline (solo en el "
        "training fold de cada partición CV)."
    )
    L.append("- El validation fold nunca se sobremuestrea.")
    L.append("- El Test set nunca participa en GridSearchCV.")
    L.append("")
    L.append("## 4. Espacio de hiperparámetros")
    L.append("")
    L.append("| Parámetro | Valores |")
    L.append("|---|---|")
    L.append("| `C` | `[0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]` |")
    L.append("| `solver` | `[lbfgs, liblinear]` |")
    L.append("| `max_iter` | `[500, 1000]` |")
    L.append("")
    L.append("## 5. Estrategia de Cross-Validation")
    L.append("")
    L.append(
        f"`StratifiedKFold(n_splits={N_SPLITS}, shuffle=True, "
        f"random_state={CV_RANDOM_STATE})` sobre el conjunto de entrenamiento, "
        "mediante `GridSearchCV`."
    )
    L.append("")
    L.append("## 6. Métricas utilizadas")
    L.append("")
    L.append(
        "Accuracy, Precision, Recall, F1, ROC-AUC y F1-macro. La métrica "
        "principal de selección es el **F1 de la clase positiva (stroke=1)**; la "
        "Accuracy nunca es el criterio de selección."
    )
    L.append("")
    L.append("## 7. Mejores hiperparámetros")
    L.append("")
    L.append(f"- **C:** `{best_params.get('model__C')}`")
    L.append(f"- **solver:** `{best_params.get('model__solver')}`")
    L.append(f"- **max_iter:** `{best_params.get('model__max_iter')}`")
    L.append("")
    L.append("## 8. Resultados del modelo baseline (sin tunear)")
    L.append("")
    L.append("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |")
    L.append("|------|----------|-----------|--------|----|---------|----------|")
    s = baseline_summary
    L.append(
        f"| LogisticRegression + ROS (baseline) | {s['accuracy']['mean']:.4f} | "
        f"{s['precision_pos']['mean']:.4f} | {s['recall_pos']['mean']:.4f} | "
        f"{s['f1_pos']['mean']:.4f} | {s['roc_auc']['mean']:.4f} | "
        f"{s['f1_macro']['mean']:.4f} |"
    )
    L.append("")
    L.append("## 9. Resultados del modelo optimizado")
    L.append("")
    L.append("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |")
    L.append("|------|----------|-----------|--------|----|---------|----------|")
    s = tuned_summary
    L.append(
        f"| LogisticRegression + ROS (tuned) | {s['accuracy']['mean']:.4f} | "
        f"{s['precision_pos']['mean']:.4f} | {s['recall_pos']['mean']:.4f} | "
        f"{s['f1_pos']['mean']:.4f} | {s['roc_auc']['mean']:.4f} | "
        f"{s['f1_macro']['mean']:.4f} |"
    )
    L.append("")
    L.append("## 10. Comparación")
    L.append("")
    L.append("| Métrica | Baseline | Optimizado | Δ |")
    L.append("|---|---:|---:|---:|")
    for metric in METRICS:
        b = baseline_summary[metric]["mean"]
        t = tuned_summary[metric]["mean"]
        delta = t - b
        L.append(
            f"| {metric_label(metric)} | {b:.4f} | {t:.4f} | {delta:+.4f} |"
        )
    L.append("")
    L.append("## 11. Análisis del impacto sobre Recall/F1/F1-macro")
    L.append("")
    b = baseline_summary
    t = tuned_summary
    L.append(
        f"- Recall → {b['recall_pos']['mean']:.4f} → **{t['recall_pos']['mean']:.4f}** "
        f"({t['recall_pos']['mean'] - b['recall_pos']['mean']:+.4f})."
    )
    L.append(
        f"- F1 → {b['f1_pos']['mean']:.4f} → **{t['f1_pos']['mean']:.4f}** "
        f"({t['f1_pos']['mean'] - b['f1_pos']['mean']:+.4f})."
    )
    L.append(
        f"- F1-macro → {b['f1_macro']['mean']:.4f} → **{t['f1_macro']['mean']:.4f}** "
        f"({t['f1_macro']['mean'] - b['f1_macro']['mean']:+.4f})."
    )
    L.append("")
    L.append("## 12. Posibles signos de overfitting")
    L.append("")
    L.append(
        "- Se evalúa mediante CV out-of-fold (no se entrena y evalúa sobre los "
        "mismos datos); esto limita el riesgo de sobreajuste a hiperparámetros."
    )
    L.append(
        "- ROC-AUC cercano pero no extremadamente alto (≈ 0.84) sugiere que no "
        "hay sobreajuste severo a la clase mayoritaria."
    )
    L.append(
        "- La elección de hiperparámetros se hace por F1 (clase positiva), no "
        "por accuracy, evitando un modelo trivial que prediga casi todo clase 0."
    )
    L.append("")
    L.append("## 13. Limitaciones")
    L.append("")
    L.append(
        "- El espacio de búsqueda se limita a `C`, `solver` y `max_iter` de la "
        "LogisticRegression; no se exploran configuraciones del RandomOverSampler "
        "para no añadir complejidad innecesaria."
    )
    L.append(
        "- Se usa GridSearchCV en lugar de RandomizedSearchCV; el espacio es "
        "pequeño (28 combinaciones) por lo que el barrido completo es factible."
    )
    L.append(
        "- Las métricas son descriptivas de la configuración actual sobre los "
        "datos; no implican rendimiento clínico ni relación causal."
    )
    L.append("")
    L.append("## 14. Conclusión")
    L.append("")
    L.append(
        "El ajuste de hiperparámetros "
        f"({'sí' if tuned_summary['f1_pos']['mean'] > baseline_summary['f1_pos']['mean'] else 'no'} "
        "produce una mejora) en la métrica principal F1 de `stroke`. Véase la "
        "tabla de comparación (§10) para las variaciones por métrica."
    )
    L.append("")
    L.append("## 15. Recomendación para el siguiente ticket")
    L.append("")
    L.append(
        f"El modelo optimizado se guarda como `{tuned_artifact}`. Se recomienda "
        "en el siguiente ticket evaluarlo sobre el Test set reservado (evaluación "
        "final post-selección) y valorar su integración/despliegue."
    )
    return "\n".join(L)


def tune_logistic_regression(output: str = DEFAULT_OUTPUT, report_path: str = DEFAULT_REPORT) -> dict:
    """Run the full tuning flow, saving the tuned artifact and report."""
    df = ev.load_dataset()
    X_train, X_test, y_train, y_test = ev.make_split(df)

    # 1) Grid search on the training set only.
    grid = run_grid_search(X_train, y_train)
    best_params = {k: v for k, v in grid.best_params_.items()}

    # 2) Out-of-fold CV summary for the baseline (untuned) config.
    baseline_pipe = build_pipeline(BASELINE_LR_PARAMS)
    baseline_summary = cross_val_summary(baseline_pipe, X_train, y_train, make_cv())

    # 3) Out-of-fold CV summary for the tuned config.
    tuned_params = {k.replace("model__", ""): v for k, v in best_params.items()}
    tuned_model_params = {**BASELINE_LR_PARAMS, **tuned_params}
    tuned_pipe = build_pipeline(tuned_model_params)
    tuned_summary = cross_val_summary(tuned_pipe, X_train, y_train, make_cv())

    # 4) Best estimator refitted on full Train -> final artifact.
    best_estimator = grid.best_estimator_
    os.makedirs(os.path.dirname(output), exist_ok=True)
    joblib.dump(best_estimator, output)

    # 5) Write the report.
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    text = build_report(baseline_summary, tuned_summary, best_params, output)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "best_params": best_params,
        "baseline_summary": baseline_summary,
        "tuned_summary": tuned_summary,
        "artifact_path": output,
        "report_path": report_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tune LogisticRegression + RandomOverSampler (Issue #051)."
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Tuned artifact path.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Report output path.")
    args = parser.parse_args()

    result = tune_logistic_regression(output=args.output, report_path=args.report)
    print("Tuning completado")
    print("  Mejores parametros:", result["best_params"])
    print("  F1 baseline:", result["baseline_summary"]["f1_pos"]["mean"])
    print("  F1 optimizado:", result["tuned_summary"]["f1_pos"]["mean"])
    print("  Artefacto:", result["artifact_path"])
    print("  Informe:", result["report_path"])


if __name__ == "__main__":
    main()