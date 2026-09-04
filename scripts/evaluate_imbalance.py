"""Evaluate class-imbalance mitigation strategies for F5 RiskAI (Issue #048).

This script compares strategies to mitigate the strong class imbalance of the
``stroke`` target (~95%/5%) on the Logistic Regression baseline, using a
**held-out Validation set** for strategy comparison and keeping the reserved
Test set pristine for final verification only (never used for selection).

Strategies evaluated (all reuse the exact preprocessing pipeline and the
Logistic Regression hyperparameters from the baseline, Issue #017, so the
comparison is controlled):

1. **baseline**: ``LogisticRegression`` with ``class_weight=None``, decision
   threshold ``0.5``.
2. **class_weight**: ``LogisticRegression`` with ``class_weight='balanced'``,
   decision threshold ``0.5``.
3. **threshold**: the baseline model re-scored at every decision threshold in
   ``[0.30, 0.35, ..., 0.70]`` computed from ``predict_proba``.
4. **oversampling**: a ``RandomOverSampler`` applied to the **training fold
   only** (never to validation/test), before fitting the estimator.

Dataset / split conventions
---------------------------
The existing Train/Test split from the baseline (#017/#018) is reproduced
verbatim via ``evaluate_baseline.make_split`` (``test_size=0.2``,
``random_state=42``, ``stratify=y``). Because this project defines no
Validation split, a stratified **Validation** subset is held out from the
**Train** fold (``test_size=0.15``, ``random_state=123``). This preserves the
original Train/Test boundary; the reserved Test is untouched and reported only
for final verification, never used to select a strategy. The preprocessing
pipeline is fitted on the training fold only, which avoids data leakage.

Metrics reported
----------------
``evaluate_baseline.compute_metrics`` (Accuracy, Precision, Recall, F1, ROC-AUC
for ``stroke = 1``) plus F1-macro and the confusion matrix. The positive class
is ``1`` (stroke). The recommendation is driven by **Recall (stroke=1)** and
**F1 (stroke=1)** on Validation, never by Accuracy alone.

Run from the repository root::

    python scripts/evaluate_imbalance.py [--output reports/imbalance-mitigation.md]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
from preprocessing import build_preprocessing_pipeline  # noqa: E402

DEFAULT_REPORT = os.path.join("reports", "imbalance-mitigation.md")

# Split conventions.
VALIDATION_SIZE = 0.15
VALIDATION_RANDOM_STATE = 123
OVERSAMPLE_RANDOM_STATE = 42

# Decision-threshold sweep (Issue #048 requires 0.30..0.70 in 0.05 steps).
THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

# Logistic Regression hyperparameters matching the baseline (#017).
LR_PARAMS = {"C": 1.0, "solver": "lbfgs", "max_iter": 100, "random_state": 42}

POSITIVE_LABEL = ev.POSITIVE_LABEL  # stroke = 1


def make_validation_split(df: pd.DataFrame):
    """Reproduce the baseline Train/Test split and hold out Validation from Train.

    Returns ``(X_train, X_val, X_test, y_train, y_val, y_test)`` where
    ``X_train``/``y_train`` is the training fold used to fit models, ``X_val``/
    ``y_val`` is the Validation subset used to compare strategies, and
    ``X_test``/``y_test`` is the reserved Test set from the baseline split
    (kept pristine).
    """
    X_train, X_test, y_train, y_test = ev.make_split(df)

    X_train, X_val, y_train, y_val = train_test_split(
        X_train,
        y_train,
        test_size=VALIDATION_SIZE,
        random_state=VALIDATION_RANDOM_STATE,
        stratify=y_train,
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def fit_estimator(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    class_weight=None,
    oversample: bool = False,
):
    """Fit the preprocessing pipeline and estimator on the training fold only.

    ``oversample`` applies ``RandomOverSampler`` to the training fold ONLY
    (never to validation/test). The preprocessing pipeline is always fitted on
    the training fold to avoid data leakage.

    Returns ``(pre, model, estimator_input_size)`` where ``pre`` transforms
    features, ``model`` is the fitted Logistic Regression, and
    ``estimator_input_size`` is the number of rows actually passed to the
    estimator (after optional oversampling).
    """
    pre = build_preprocessing_pipeline()
    X_tr_proc = pre.fit_transform(X_train, y_train)

    estimator_input = X_tr_proc
    estimator_target = y_train.to_numpy()
    if oversample:
        estimator_input, estimator_target = RandomOverSampler(
            random_state=OVERSAMPLE_RANDOM_STATE
        ).fit_resample(estimator_input, estimator_target)

    model = LogisticRegression(**LR_PARAMS, class_weight=class_weight)
    model.fit(estimator_input, estimator_target)
    return pre, model, int(estimator_input.shape[0])


def predict_at_threshold(proba: np.ndarray, threshold: float) -> np.ndarray:
    """Turn positive-class probabilities into binary predictions at a threshold."""
    return (proba >= threshold).astype(int)


def compute_metrics(y_true, y_pred, y_proba, threshold: float) -> dict:
    """Compute the full metric set (incl. F1-macro and confusion matrix)."""
    metrics = ev.compute_metrics(y_true, y_pred, y_proba)
    metrics["f1_macro"] = round(
        float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4
    )
    metrics["threshold"] = threshold
    metrics["confusion_matrix"] = confusion_matrix(y_true, y_pred).tolist()
    return metrics


def fold_metrics(pre, model, X_fold, y_fold, threshold: float) -> dict:
    """Transform a fold and compute metrics at the given decision threshold."""
    proba = model.predict_proba(pre.transform(X_fold))[:, POSITIVE_LABEL]
    y_true = y_fold.to_numpy()
    y_pred = predict_at_threshold(proba, threshold)
    return compute_metrics(y_true, y_pred, proba, threshold)


def run_strategies(df: pd.DataFrame) -> dict:
    """Run all mitigation strategies and return per-strategy results.

    Returns a dict keyed by strategy name. Each entry holds the Validation,
    Train and Test metrics (Train/Test informational; Test post-selection
    only), plus ``pre``/``model`` artifacts.
    """
    X_train, X_val, X_test, y_train, y_val, y_test = make_validation_split(df)

    # 1) baseline (class_weight=None, threshold=0.5).
    pre, model, _ = fit_estimator(X_train, y_train, class_weight=None, oversample=False)
    baseline = {
        "pre": pre,
        "model": model,
        "train": fold_metrics(pre, model, X_train, y_train, threshold=0.5),
        "val": fold_metrics(pre, model, X_val, y_val, threshold=0.5),
        "test": fold_metrics(pre, model, X_test, y_test, threshold=0.5),
    }

    # 2) class_weight='balanced' (threshold=0.5).
    pre, model, _ = fit_estimator(X_train, y_train, class_weight="balanced", oversample=False)
    class_weight = {
        "pre": pre,
        "model": model,
        "train": fold_metrics(pre, model, X_train, y_train, threshold=0.5),
        "val": fold_metrics(pre, model, X_val, y_val, threshold=0.5),
        "test": fold_metrics(pre, model, X_test, y_test, threshold=0.5),
    }

    # 3) threshold sweep: re-score the baseline model at each threshold.
    pre, model, _ = fit_estimator(X_train, y_train, class_weight=None, oversample=False)
    proba_val = model.predict_proba(pre.transform(X_val))[:, POSITIVE_LABEL]
    proba_train = model.predict_proba(pre.transform(X_train))[:, POSITIVE_LABEL]
    proba_test = model.predict_proba(pre.transform(X_test))[:, POSITIVE_LABEL]
    sweep_val: dict[float, dict] = {}
    for t in THRESHOLDS:
        y_pred = predict_at_threshold(proba_val, t)
        sweep_val[t] = compute_metrics(y_val.to_numpy(), y_pred, proba_val, threshold=t)
    threshold = {
        "pre": pre,
        "model": model,
        "probabilities": {"train": proba_train, "val": proba_val, "test": proba_test},
        "sweep": sweep_val,
    }

    # 4) RandomOverSampler on the training fold only (threshold=0.5).
    pre, model, estimator_input_size = fit_estimator(
        X_train, y_train, class_weight=None, oversample=True
    )
    oversampling = {
        "pre": pre,
        "model": model,
        "train": fold_metrics(pre, model, X_train, y_train, threshold=0.5),
        "val": fold_metrics(pre, model, X_val, y_val, threshold=0.5),
        "test": fold_metrics(pre, model, X_test, y_test, threshold=0.5),
        "estimator_input_size": estimator_input_size,
    }

    return {
        "baseline": baseline,
        "class_weight": class_weight,
        "threshold": threshold,
        "oversampling": oversampling,
        "n_train": int(len(y_train)),
        "n_val": int(len(y_val)),
        "n_test": int(len(y_test)),
        "pos_train": int((y_train == POSITIVE_LABEL).sum()),
        "pos_val": int((y_val == POSITIVE_LABEL).sum()),
        "pos_test": int((y_test == POSITIVE_LABEL).sum()),
    }


def _metric_columns(metrics: dict) -> list[str]:
    """Format a metrics dict as markdown table rows (single-column layout)."""
    rows = [
        f"| Accuracy | {metrics['accuracy']:.4f} |",
        f"| Precision (stroke=1) | {metrics['precision']:.4f} |",
        f"| Recall (stroke=1) | {metrics['recall']:.4f} |",
        f"| F1-score (stroke=1) | {metrics['f1']:.4f} |",
        f"| F1-score (macro) | {metrics['f1_macro']:.4f} |",
        f"| AUC-ROC | {metrics['auc_roc']:.4f} |",
        f"| Umbral de decisión | {metrics['threshold']:.2f} |",
    ]
    cm = metrics["confusion_matrix"]
    rows.append(f"| Matriz de confusión | `[[{cm[0][0]}, {cm[0][1]}], [{cm[1][0]}, {cm[1][1]}]]` |")
    return rows


def _recommendation(results: dict) -> dict:
    """Select the best strategy by Validation Recall/F1 of stroke (not Accuracy)."""
    val = {
        "baseline": results["baseline"]["val"],
        "class_weight": results["class_weight"]["val"],
        "oversampling": results["oversampling"]["val"],
    }
    # Best single threshold across the sweep (by stroke F1, tiebroken by recall).
    sweep = results["threshold"]["sweep"]
    best_t = max(
        sweep,
        key=lambda t: (sweep[t]["f1"], sweep[t]["recall"]),
    )
    val["threshold@{:.2f}".format(best_t)] = sweep[best_t]

    # Rank by stroke F1, tiebroken by stroke recall.
    ranked = sorted(val.items(), key=lambda kv: (kv[1]["f1"], kv[1]["recall"]), reverse=True)
    best_name, best_metrics = ranked[0]
    return {
        "ranking": [name for name, _ in ranked],
        "best_name": best_name,
        "best_f1": best_metrics["f1"],
        "best_recall": best_metrics["recall"],
        "best_threshold": best_metrics["threshold"],
    }


def build_report(df: pd.DataFrame, results: dict) -> str:
    """Compose the markdown mitigation-report text."""
    n = len(df)
    n_pos = int((df[ev.TARGET_COLUMN] == 1).sum())
    pct_pos = n_pos / n * 100

    rec = _recommendation(results)
    rows = val_rows(results)
    sweep = results["threshold"]["sweep"]

    lines: list[str] = []
    lines.append("# Informe — Mitigación del Desbalance de Clases")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Mitigación del desbalance (ML, Issue #048)")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe compara estrategias para mitigar el desbalance de la clase "
        "`stroke` sobre el baseline de `LogisticRegression` (Issue #017). Todas las "
        "estrategias se evalúan sobre un **subset de Validación**; el **Test** se "
        "mantiene intacto y solo se reporta a título informativo post-selección."
    )
    lines.append("")
    lines.append(
        "> **Nota:** las métricas no implican rendimiento clínico ni relación causal."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Seleccionar y documentar una estrategia que **mejore el Recall y el F1 de "
        "la clase minoritaria `stroke=1`** sobre la Validación, sin sacrificar la "
        "integridad del split (no se toca Test para elegir estrategia)."
    )
    lines.append("")

    lines.append("## 2. Dataset y split")
    lines.append("")
    lines.append(
        f"El dataset tiene {n} registros con **{pct_pos:.2f}%** de casos `stroke=1` "
        "(fuerte desbalance)."
    )
    lines.append(
        "- **Split base (reproducido):** `train_test_split(test_size=0.20, "
        "random_state=42, stratify=y)` (igual que #017/#018)."
    )
    lines.append(
        f"- **Validación (nueva, derivada de Train):** se reserva "
        f"{VALIDATION_SIZE:.0%} estratificada del split de Train "
        f"(`random_state={VALIDATION_RANDOM_STATE}`) para comparar estrategias. "
        "El conjunto de Test quedó intacto."
    )
    lines.append(f"  - Train: {results['n_train']} filas ({results['pos_train']} positivas).")
    lines.append(f"  - Validación: {results['n_val']} filas ({results['pos_val']} positivas).")
    lines.append(f"  - Test: {results['n_test']} filas ({results['pos_test']} positivas) — solo informe.")
    lines.append(
        "El pipeline de preprocesado se ajusta SOLO sobre Train para evitar "
        "fuga de datos."
    )
    lines.append("")

    lines.append("## 3. Estrategias evaluadas")
    lines.append("")
    lines.append("- **Baseline:** `LogisticRegression` (`class_weight=None`), umbral `0.50`.")
    lines.append("- **class_weight:** `LogisticRegression(class_weight='balanced')`, umbral `0.50`.")
    lines.append("- **Umbral:** baseline re-escoreado con umbral en `[0.30, 0.35, ..., 0.70]`.")
    lines.append(
        "- **Oversampling:** `RandomOverSampler` aplicado SOLO al fold de Train "
        "(antes de ajustar el modelo), umbral `0.50`."
    )
    lines.append("")

    lines.append("## 4. Resultados principales (Validación)")
    lines.append("")
    lines.append("| Estrategia | Acc | Prec | Rec | F1 | F1-macro | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    order = [
        ("Baseline (umbral 0.50)", "baseline"),
        ("class_weight=balanced", "class_weight"),
        (f"Umbral óptimo @{rec['best_threshold']:.2f}", f"threshold@{rec['best_threshold']:.2f}"),
        ("RandomOverSampler (Train)", "oversampling"),
    ]
    for name, key in order:
        m = rows[key]
        lines.append(
            f"| {name} | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {m['f1_macro']:.4f} | "
            f"{m['auc_roc']:.4f} |"
        )
    lines.append("")
    lines.append(
        "> Precision/Recall/F1 se refieren a la clase positiva `stroke=1`. "
        "El 'Umbral óptimo' corresponde al valor del barrido con mejor F1 de "
        "`stroke=1` sobre Validación."
    )
    lines.append("")

    lines.append("## 5. Barrido de umbral (baseline)")
    lines.append("")
    lines.append("| Umbral | Precision (stroke) | Recall (stroke) | F1 (stroke) |")
    lines.append("|---:|---:|---:|---:|")
    for t in THRESHOLDS:
        m = sweep[t]
        lines.append(
            f"| {t:.2f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} |"
        )
    lines.append("")

    lines.append("## 6. Métricas detalladas por estrategia")
    lines.append("")
    for label, key in order:
        lines.append(f"### {label}")
        lines.append("")
        lines.append("| Metric | Valor |")
        lines.append("|---|---|")
        lines.extend(_metric_columns(rows[key]))
        lines.append("")

    lines.append("## 7. Gap Train vs Validación (overfitting, informativo)")
    lines.append("")
    lines.append("| Estrategia | Gap Acc | Gap Rec | Gap F1 |")
    lines.append("|---|---:|---:|---:|")
    for label, key in [
        ("Baseline", "baseline"),
        ("class_weight=balanced", "class_weight"),
        ("RandomOverSampler (Train)", "oversampling"),
    ]:
        tr = results[key]["train"]
        vl = results[key]["val"]
        lines.append(
            f"| {label} | {abs(tr['accuracy'] - vl['accuracy']) * 100:.2f} pp | "
            f"{abs(tr['recall'] - vl['recall']) * 100:.2f} pp | "
            f"{abs(tr['f1'] - vl['f1']) * 100:.2f} pp |"
        )
    lines.append("")

    lines.append("## 8. Verificación en Test (post-selección, informativo)")
    lines.append("")
    lines.append("| Estrategia | Acc | Prec | Rec | F1 | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for label, key in [
        ("Baseline", "baseline"),
        ("class_weight=balanced", "class_weight"),
        ("RandomOverSampler (Train)", "oversampling"),
    ]:
        m = results[key]["test"]
        lines.append(
            f"| {label} | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {m['auc_roc']:.4f} |"
        )
    lines.append("")

    lines.append("## 9. Recomendación")
    lines.append("")
    lines.append(
        f"Selección por **Recall y F1 de `stroke=1` sobre Validación** (nunca por "
        f"Accuracy): mejor estrategia = **{rec['best_name']}** "
        f"con F1(stroke)={rec['best_f1']:.4f} y Recall(stroke)={rec['best_recall']:.4f} "
        f"@{rec['best_threshold']:.2f}."
    )
    lines.append("")
    lines.append("Ranking (F1 stroke desc): " + ", ".join(rec["ranking"]) + ".")
    lines.append("")
    lines.append(
        "- El resultado es **descriptivo del modelo sobre los datos actuales**; "
        "no es una decisión clínica."
    )
    lines.append(
        "- No se realizó tuning ni ensamblado; la recomendación queda documentada "
        "para un Issue posterior de modelado."
    )
    return "\n".join(lines)


def val_rows(results: dict) -> dict:
    """Return the Validation metrics dict for each comparable strategy."""
    rows: dict[str, dict] = {
        "baseline": results["baseline"]["val"],
        "class_weight": results["class_weight"]["val"],
        "oversampling": results["oversampling"]["val"],
    }
    rec = _recommendation(results)
    # Only add the threshold row if it is not already one of the direct rows.
    rows[f"threshold@{rec['best_threshold']:.2f}"] = results["threshold"]["sweep"][
        rec["best_threshold"]
    ]
    return rows


def evaluate_imbalance(report_path: str = DEFAULT_REPORT) -> dict:
    """Run the full mitigation evaluation and write the markdown report."""
    df = ev.load_dataset()
    results = run_strategies(df)

    text = build_report(df, results)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "n_train": results["n_train"],
        "n_val": results["n_val"],
        "n_test": results["n_test"],
        "recommendation": _recommendation(results),
        "report_path": report_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate class-imbalance mitigation strategies (Issue #048)."
    )
    parser.add_argument(
        "--output", default=DEFAULT_REPORT, help="Output markdown report path."
    )
    args = parser.parse_args()

    result = evaluate_imbalance(report_path=args.output)
    print("Evaluación de mitigación del desbalance completada")
    print(f"  Informe: {args.output}")
    print("  Recomendación:", json.dumps(result["recommendation"]))


if __name__ == "__main__":
    main()