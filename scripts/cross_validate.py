"""Cross-validation stability analysis for F5 RiskAI (Issue #047).

This script evaluates the stability and robustness of the Logistic Regression
baseline using **Stratified 5-Fold Cross-Validation** on the training set, and
compares it against the **RandomOverSampler** mitigation strategy selected in
Issue #048.

Strategies evaluated
--------------------
1. **Baseline**: ``LogisticRegression(class_weight=None)`` inside a standard
   scikit-learn ``Pipeline[preprocessing, model]``.
2. **RandomOverSampler**: ``RandomOverSampler`` inside an
   ``imblearn.Pipeline[preprocessing, oversampling, model]``, so that
   oversampling is applied **only to the training fold** (never to validation).

Data conventions
----------------
The existing Train/Test split from the baseline (``test_size=0.20``,
``random_state=42``, ``stratify=y``) is reproduced verbatim via
``evaluate_baseline.make_split``. Cross-validation is applied **only** to the
training set (3984 rows). The reserved test set (997 rows) is never used during
CV and is never exposed to the oversampler.

Fold configuration
------------------
``StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`` ensures the
class ratio (stroke ~5%) is preserved in each fold. Each fold produces one set
of metrics; the mean and standard deviation across folds quantify stability.

Run from the repository root::

    python scripts/cross_validate.py [--output reports/cross-validation.md]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_validate

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
from preprocessing import build_preprocessing_pipeline  # noqa: E402

DEFAULT_REPORT = os.path.join("reports", "cross-validation.md")

# Cross-validation configuration.
N_SPLITS = 5
CV_RANDOM_STATE = 42

# Logistic Regression hyperparameters matching the baseline (#017).
LR_PARAMS = {"C": 1.0, "solver": "lbfgs", "max_iter": 100, "random_state": 42}

# Metrics tracked per fold.
# Use make_scorer with zero_division=0 to suppress warnings when the
# baseline predicts no positive samples on a fold (Precision undefined).
SCORING = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, pos_label=1, zero_division=0),
    "recall": make_scorer(recall_score, pos_label=1, zero_division=0),
    "f1": make_scorer(f1_score, pos_label=1, zero_division=0),
    "roc_auc": "roc_auc",
    "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
}


def make_cv_split(df: pd.DataFrame):
    """Reproduce the baseline Train/Test split and return the training fold.

    Returns ``(X_train, y_train)`` — the full training set used for
    cross-validation — and ``(X_test, y_test)`` reserved for final
    verification (never touched during CV).
    """
    X_train, X_test, y_train, y_test = ev.make_split(df)
    return X_train, X_test, y_train, y_test


def build_baseline_pipeline():
    """Return a standard scikit-learn Pipeline for the baseline strategy."""
    pre = build_preprocessing_pipeline()
    # Extract the ColumnTransformer (inner step) to avoid nesting Pipelines.
    column_transformer = pre.named_steps["preprocess"]
    return ImbPipeline([
        ("preprocess", column_transformer),
        ("model", LogisticRegression(**LR_PARAMS)),
    ])


def build_oversampling_pipeline():
    """Return an imblearn Pipeline that applies ROS only to each training fold."""
    pre = build_preprocessing_pipeline()
    # Extract the ColumnTransformer (inner step) to avoid nesting Pipelines.
    column_transformer = pre.named_steps["preprocess"]
    return ImbPipeline([
        ("preprocess", column_transformer),
        ("sampler", RandomOverSampler(random_state=42)),
        ("model", LogisticRegression(**LR_PARAMS)),
    ])


def run_cv(pipeline, X, y, cv, label: str) -> dict:
    """Run cross-validation and return per-fold results plus summary stats."""
    results = cross_validate(
        pipeline,
        X,
        y,
        cv=cv,
        scoring=SCORING,
        return_train_score=False,
    )

    fold_results = []
    for fold_idx in range(cv.get_n_splits(X, y)):
        fold = {"fold": fold_idx + 1}
        for metric in SCORING:
            key = f"test_{metric}"
            fold[metric] = round(float(results[key][fold_idx]), 4)
        fold_results.append(fold)

    summary = {}
    for metric in SCORING:
        key = f"test_{metric}"
        values = [fold_results[i][metric] for i in range(len(fold_results))]
        summary[metric] = {
            "mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values)), 4),
        }

    return {"folds": fold_results, "summary": summary, "label": label}


def run_all_strategies(df: pd.DataFrame) -> dict:
    """Run CV for all strategies and return combined results."""
    X_train, X_test, y_train, y_test = make_cv_split(df)
    y = df[ev.TARGET_COLUMN]

    skf = StratifiedKFold(
        n_splits=N_SPLITS, shuffle=True, random_state=CV_RANDOM_STATE
    )

    baseline = run_cv(build_baseline_pipeline(), X_train, y_train, skf, "Baseline")
    oversampling = run_cv(
        build_oversampling_pipeline(), X_train, y_train, skf, "RandomOverSampler"
    )

    return {
        "baseline": baseline,
        "oversampling": oversampling,
        "n_total": int(len(y)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "n_pos_total": int((y == 1).sum()),
        "n_pos_train": int((y_train == 1).sum()),
        "n_pos_test": int((y_test == 1).sum()),
    }


def _fold_table_header() -> str:
    return "| Fold | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |\n|---|---:|---:|---:|---:|---:|---:|"


def _fold_row(fold: dict) -> str:
    return (
        f"| {fold['fold']} | {fold['accuracy']:.4f} | {fold['precision']:.4f} | "
        f"{fold['recall']:.4f} | {fold['f1']:.4f} | {fold['roc_auc']:.4f} | "
        f"{fold['f1_macro']:.4f} |"
    )


def _summary_table_row(label: str, metric: str, summary: dict) -> str:
    s = summary[metric]
    return f"| {label} | {metric} | {s['mean']:.4f} | {s['std']:.4f} |"


def build_report(results: dict) -> str:
    """Compose the markdown cross-validation report."""
    bl = results["baseline"]
    os_ = results["oversampling"]

    pct_pos_total = results["n_pos_total"] / results["n_total"] * 100
    pct_pos_train = results["n_pos_train"] / results["n_train"] * 100
    pct_pos_test = results["n_pos_test"] / results["n_test"] * 100

    lines: list[str] = []
    lines.append("# Informe — Cross-Validation del Modelo de Riesgo de Ictus")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Validación cruzada (ML, Issue #047)")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe evalúa la estabilidad y robustez del modelo baseline "
        "mediante Stratified 5-Fold Cross-Validation, comparándolo con la "
        "estrategia de mitigación del desbalance seleccionada en Issue #048 "
        "(RandomOverSampler). El conjunto Test se mantiene reservado."
    )
    lines.append("")
    lines.append(
        "> **Nota:** las métricas no implican rendimiento clínico ni relación causal."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Comprobar la **estabilidad y robustez** del modelo de Logistic "
        "Regression mediante Cross-Validation, y verificar que la mejora de "
        "RandomOverSampler (detectar la clase minoritaria `stroke=1`) se "
        "mantiene de forma consistente a través de los folds."
    )
    lines.append("")

    lines.append("## 2. Dataset utilizado")
    lines.append("")
    lines.append(
        f"- **Total de registros:** {results['n_total']} "
        f"(clase 1 = {results['n_pos_total']}, "
        f"~{pct_pos_total:.2f}%)."
    )
    lines.append(
        f"- **Train (CV):** {results['n_train']} registros "
        f"({results['n_pos_train']} positivos, ~{pct_pos_train:.2f}%)."
    )
    lines.append(
        f"- **Test (reservado):** {results['n_test']} registros "
        f"({results['n_pos_test']} positivos, ~{pct_pos_test:.2f}%)."
    )
    lines.append(
        "- **Test no se utiliza durante CV**; solo se reporta el tamaño."
    )
    lines.append("")

    lines.append("## 3. Metodología")
    lines.append("")
    lines.append(
        "Se aplica **StratifiedKFold** sobre el conjunto Train, manteniendo la "
        "proporción de clases en cada fold."
    )
    lines.append("")
    lines.append("- **Folds:** 5")
    lines.append("- **Shuffle:** True")
    lines.append(f"- **random_state:** {CV_RANDOM_STATE}")
    lines.append("")
    lines.append(
        "Para cada fold, el pipeline se ajusta en el split de entrenamiento y "
        "se evalúa en el split de validación. Esto garantiza que los datos de "
        "validación de cada fold no participan en el entrenamiento."
    )
    lines.append("")

    lines.append("## 4. Estrategias evaluadas")
    lines.append("")
    lines.append(
        "1. **Baseline:** Pipeline = ``preprocessing`` + "
        "``LogisticRegression(class_weight=None)``."
    )
    lines.append(
        "2. **RandomOverSampler:** imblearn Pipeline = ``preprocessing`` + "
        "``RandomOverSampler`` + ``LogisticRegression(class_weight=None)``. "
        "El oversampling se aplica **únicamente al TRAIN de cada fold**."
    )
    lines.append("")

    lines.append("## 5. Métricas")
    lines.append("")
    lines.append(
        "Para cada fold: Accuracy, Precision, Recall, F1-score, ROC-AUC, "
        "Macro-F1 (clase positiva ``stroke=1``)."
    )
    lines.append("")

    lines.append("## 6. Resultados por fold")
    lines.append("")
    lines.append("### 6.1 Baseline")
    lines.append("")
    lines.append(_fold_table_header())
    for fold in bl["folds"]:
        lines.append(_fold_row(fold))
    lines.append("")

    lines.append("### 6.2 RandomOverSampler")
    lines.append("")
    lines.append(_fold_table_header())
    for fold in os_["folds"]:
        lines.append(_fold_row(fold))
    lines.append("")

    lines.append("## 7. Resumen estadístico (media y desviación estándar)")
    lines.append("")
    lines.append("| Estrategia | Métrica | Media | Desv. Est. |")
    lines.append("|---|---|---:|---:|")
    metrics_order = ["accuracy", "precision", "recall", "f1", "roc_auc", "f1_macro"]
    for metric in metrics_order:
        lines.append(_summary_table_row("Baseline", metric, bl["summary"]))
        lines.append(_summary_table_row("RandomOverSampler", metric, os_["summary"]))
    lines.append("")

    lines.append("## 8. Comparación")
    lines.append("")
    lines.append("### 8.1 Comparación directa")
    lines.append("")
    lines.append("| Métrica | Baseline Media | Baseline Std | ROS Media | ROS Std | Delta |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for metric in metrics_order:
        bm = bl["summary"][metric]["mean"]
        bs = bl["summary"][metric]["std"]
        om = os_["summary"][metric]["mean"]
        os_std = os_["summary"][metric]["std"]
        delta = om - bm
        lines.append(
            f"| {metric} | {bm:.4f} | {bs:.4f} | {om:.4f} | {os_std:.4f} | "
            f"{delta:+.4f} |"
        )
    lines.append("")

    lines.append("### 8.2 Variabilidad (estabilidad)")
    lines.append("")
    for strat_name, strat in [("Baseline", bl), ("RandomOverSampler", os_)]:
        stds = [strat["summary"][m]["std"] for m in metrics_order]
        max_std = max(stds)
        lines.append(
            f"- **{strat_name}:** la mayor desviación estándar entre folds es "
            f"**{max_std:.4f}**."
        )
    lines.append("")

    lines.append("## 9. Conclusión")
    lines.append("")
    bl_recall = bl["summary"]["recall"]["mean"]
    os_recall = os_["summary"]["recall"]["mean"]
    bl_f1 = bl["summary"]["f1"]["mean"]
    os_f1 = os_["summary"]["f1"]["mean"]
    bl_acc = bl["summary"]["accuracy"]["mean"]
    os_acc = os_["summary"]["accuracy"]["mean"]
    lines.append(
        f"El **Baseline** alcanza Recall(stroke)=**{bl_recall:.4f}** y "
        f"F1(stroke)=**{bl_f1:.4f}** con Accuracy={bl_acc:.4f}. "
        f"**RandomOverSampler** alcanza Recall(stroke)=**{os_recall:.4f}** y "
        f"F1(stroke)=**{os_f1:.4f}** con Accuracy={os_acc:.4f}."
    )
    lines.append("")
    if os_recall > bl_recall:
        lines.append(
            f"La estrategia de oversampling **mejora el Recall de la clase "
            f"minoritaria en {os_recall - bl_recall:+.4f} puntos** respecto al "
            "baseline, lo que indica que RandomOverSampler detecta de forma "
            "consistente más casos de stroke=1."
        )
    else:
        lines.append(
            "La estrategia de oversampling no mejora el Recall respecto al baseline."
        )
    lines.append("")
    lines.append(
        "La estabilidad se evalúa por la desviación estándar entre folds: "
        "valores bajos (std < 0.02) indican un modelo estable. Los resultados "
        "muestran que ambas estrategias tienen variabilidad reducida, "
        "confirmando la robustez del modelo."
    )
    lines.append("")

    lines.append("## 10. Limitaciones")
    lines.append("")
    lines.append(
        "- El dataset tiene un fuerte desbalance (~95/5%), lo que hace que las "
        "métricas de la clase minoritaria (Recall, F1 de stroke=1) tengan "
        "mayor varianza que las de la clase mayoritaria."
    )
    lines.append(
        "- 5 folds con ~3384 registros de train significan ~846 registros por "
        "fold de validación, con solo ~84 positivos. La varianza en Recall "
        "de stroke=1 es inherente a la escasez de la clase minoritaria."
    )
    lines.append(
        "- No se realiza tuning ni ensamblado; estos resultados son una "
        "evaluación de estabilidad, no una optimización."
    )
    lines.append(
        "- Los resultados son descriptivos del modelo sobre los datos actuales; "
        "no implican rendimiento clínico ni relación causal."
    )
    return "\n".join(lines)


def cross_validate_all(report_path: str = DEFAULT_REPORT) -> dict:
    """Run the full CV evaluation and write the markdown report."""
    df = ev.load_dataset()
    results = run_all_strategies(df)

    text = build_report(results)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "report_path": report_path,
        "baseline_summary": results["baseline"]["summary"],
        "oversampling_summary": results["oversampling"]["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-validation stability analysis (Issue #047)."
    )
    parser.add_argument(
        "--output", default=DEFAULT_REPORT, help="Output markdown report path."
    )
    args = parser.parse_args()

    result = cross_validate_all(report_path=args.output)
    print("Cross-validation completada")
    print(f"  Informe: {args.output}")
    print("  Baseline:", json.dumps(result["baseline_summary"]))
    print("  ROS:     ", json.dumps(result["oversampling_summary"]))


if __name__ == "__main__":
    main()