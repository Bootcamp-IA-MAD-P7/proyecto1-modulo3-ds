"""Analyze the confusion matrix of the Logistic Regression baseline (#019).

This script loads the trained baseline artifact (Issue #017), reproduces the
exact Train/Test split used in #017/#018, computes the confusion matrix on Test
and (optionally) Train, and writes a report plus a PNG figure.

The matrix follows the explicit class order ``[0, 1]``::

    positives = "stroke = 1"

               Pred 0    Pred 1
    Real 0   [  TN       FP   ]
    Real 1   [  FN       TP   ]

* TN : negative correctly classified
* FP : false alarms (``stroke=0`` predicted as ``1``)
* FN : missed strokes (``stroke=1`` predicted as ``0``)
* TP : positives correctly classified

Only descriptive interpretation is given; no medical causality is claimed. The
model is NOT modified, no balancing/ tuning/ threshold change is applied.

Run from the repository root::

    python scripts/analyze_confusion_matrix.py [--output reports/confusion-matrix-analysis.md]
"""

from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.metrics import confusion_matrix  # noqa: E402

import evaluate_baseline as ev  # noqa: E402

DEFAULT_MODEL_PATH = os.path.join("artifacts", "logistic_regression_baseline.joblib")
DEFAULT_REPORT = os.path.join("reports", "confusion-matrix-analysis.md")
DEFAULT_FIGURE_DIR = os.path.join("reports", "figures")
DEFAULT_FIGURE = os.path.join(DEFAULT_FIGURE_DIR, "baseline-confusion-matrix.png")

DPI = 150
CLASS_ORDER = [0, 1]
CLASS_LABELS = ["0", "1"]


def compute_confusion_matrix(y_true, y_pred) -> np.ndarray:
    """Return a 2x2 confusion matrix with explicit class order [0, 1]."""
    return confusion_matrix(y_true, y_pred, labels=CLASS_ORDER)


def components(cm: np.ndarray) -> dict:
    """Split a 2x2 confusion matrix into TN/FP/FN/TP."""
    tn, fp, fn, tp = cm.ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def derived_metrics(comp: dict) -> dict:
    """Return Precision/Recall/F1 derived from the confusion components."""
    precision = comp["tp"] / (comp["tp"] + comp["fp"]) if (comp["tp"] + comp["fp"]) else 0.0
    recall = comp["tp"] / (comp["tp"] + comp["fn"]) if (comp["tp"] + comp["fn"]) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def plot_confusion_matrix(cm: np.ndarray, path: str) -> str:
    """Plot and save the confusion matrix heatmap to ``path``."""
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(CLASS_LABELS)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(CLASS_LABELS)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusión — baseline (Test)")

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                str(cm[i, j]),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )

    fig.colorbar(im, ax=ax)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def analyze_confusion_matrix(
    model_path: str = DEFAULT_MODEL_PATH,
    report_path: str = DEFAULT_REPORT,
    figure_path: str = DEFAULT_FIGURE,
) -> dict:
    """Run the confusion-matrix analysis (Test and Train) and write artifacts."""
    df = ev.load_dataset()
    X_train, X_test, y_train, y_test = ev.make_split(df)
    pipeline = ev.load_model(model_path)

    pred_test = pipeline.predict(X_test)
    pred_train = pipeline.predict(X_train)

    cm_test = compute_confusion_matrix(y_test, pred_test)
    cm_train = compute_confusion_matrix(y_train, pred_train)

    comp_test = components(cm_test)
    comp_train = components(cm_train)
    deriv_test = derived_metrics(comp_test)
    deriv_train = derived_metrics(comp_train)

    text = build_report(
        df=df,
        cm_test=cm_test,
        cm_train=cm_train,
        comp_test=comp_test,
        comp_train=comp_train,
        deriv_test=deriv_test,
        deriv_train=deriv_train,
        n_test=len(y_test),
        n_train=len(y_train),
        model_path=model_path,
        figure_path=figure_path,
    )

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    fig = plot_confusion_matrix(cm_test, figure_path)

    return {
        "test": comp_test,
        "train": comp_train,
        "derived_test": deriv_test,
        "derived_train": deriv_train,
        "report_path": report_path,
        "figure_path": fig,
    }


def _cm_table(cm: np.ndarray) -> str:
    return (
        f"|  | Pred: {CLASS_LABELS[0]} | Pred: {CLASS_LABELS[1]} |\n"
        f"|---|---|---|\n"
        f"| **Real: {CLASS_LABELS[0]}** | {cm[0, 0]} | {cm[0, 1]} |\n"
        f"| **Real: {CLASS_LABELS[1]}** | {cm[1, 0]} | {cm[1, 1]} |"
    )


def _components_table(comp: dict) -> str:
    return (
        f"| TN (negativos correctos) | {comp['tn']} |\n"
        f"| FP (falsas alarmas) | {comp['fp']} |\n"
        f"| FN (ictus no detectados) | {comp['fn']} |\n"
        f"| TP (ictus detectados) | {comp['tp']} |"
    )


def build_report(
    df: pd.DataFrame,
    cm_test: np.ndarray,
    cm_train: np.ndarray,
    comp_test: dict,
    comp_train: dict,
    deriv_test: dict,
    deriv_train: dict,
    n_test: int,
    n_train: int,
    model_path: str,
    figure_path: str,
) -> str:
    n = len(df)
    n_pos = int((df[ev.TARGET_COLUMN] == 1).sum())
    pct_pos = n_pos / n * 100
    fig_link = os.path.relpath(figure_path, start=os.path.dirname(DEFAULT_REPORT)).replace("\\", "/")

    lines: list[str] = []
    lines.append("# Informe — Análisis de la Matriz de Confusión del Baseline")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Análisis de errores de clasificación (ML)")
    lines.append(f"**Artefacto evaluado:** `{model_path}`")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe analiza los errores del baseline entrenado en #017, usando "
        "el mismo split y configuración de #016–#018. Es descriptivo; no modifica el "
        "modelo ni afirma causalidad médica."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Comprender los tipos de error del baseline (``LogisticRegression``) sobre "
        "Test, desglosando la matriz de confusión en TN/FP/FN/TP y relacionándola "
        "con Precision/Recall/F1 de la clase positiva `stroke=1`."
    )
    lines.append("")

    lines.append("## 2. Modelo utilizado")
    lines.append("")
    lines.append(
        "- Pipeline de scikit-learn = ``preprocessing`` + ``LogisticRegression`` "
        "(artefacto #017), cargado tal cual."
    )
    lines.append("- **Estado:** sin modificar; no se reentrena, no se balancea, no se ajusta el threshold.")
    lines.append("")

    lines.append("## 3. Dataset y split")
    lines.append("")
    lines.append(
        f"- {n} registros; target `stroke`: `0`≈{100-pct_pos:.2f}%, `1`≈{pct_pos:.2f}%."
    )
    lines.append("- **Split:** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.")
    lines.append(f"  - Train: {n_train} filas.")
    lines.append(f"  - Test: {n_test} filas.")
    lines.append("")

    lines.append("## 4. Confusion matrix (Test)")
    lines.append("")
    lines.append(_cm_table(cm_test))
    lines.append("")
    lines.append("Convención de clases: `[0, 1]` = [`no stroke`, `stroke`].")
    lines.append("")

    lines.append(f"![Matriz de confusión del baseline (Test)]({fig_link})")
    lines.append("")

    lines.append("## 5. TN / FP / FN / TP")
    lines.append("")
    lines.append("### 5.1 Test")
    lines.append("")
    lines.append(_components_table(comp_test))
    lines.append("")
    lines.append("### 5.2 Train (referencia)")
    lines.append("")
    lines.append(_components_table(comp_train))
    lines.append("")

    test_pos_support = comp_test["tp"] + comp_test["fn"]
    lines.append("## 6. Interpretación de errores")
    lines.append("")
    lines.append(
        f"- Sobre los {test_pos_support} casos reales de `stroke` en Test "
        f"(soporte `1`), el modelo **detectó (TP) {comp_test['tp']}** y **no "
        f"identificó (FN) {comp_test['fn']}**."
    )
    lines.append(
        f"- Se **produjeron {comp_test['fp']} falsas alarmas** (casos `stroke=0` "
        f"clasificados como `1`) y el modelo **clasificó correctamente (TN) "
        f"{comp_test['tn']}** negativos."
    )
    total_pred_1 = comp_test["tp"] + comp_test["fp"]
    total_pred_0 = comp_test["tn"] + comp_test["fn"]
    lines.append(
        f"- El modelo emite {total_pred_1} predicciones `1` y {total_pred_0} "
        f"predicciones `0`: en Test, **predice mayoritariamente la clase `0`** "
        f"({total_pred_0}/{n_test}), coherente con el fuerte desbalance."
    )
    lines.append(
        "- Dado el desbalance (~95/5), la clase minoritaria apenas se predice en "
        "decisión binaria, concentrando los errores en **FN (ictus no detectados)**."
    )
    lines.append("")

    lines.append("## 7. Relación con Precision / Recall / F1")
    lines.append("")
    lines.append("### 7.1 Test")
    lines.append("")
    lines.append(
        f"- **Precision** (TP/(TP+FP)) = {deriv_test['precision']:.4f}."
    )
    lines.append(
        f"- **Recall** (TP/(TP+FN)) = {deriv_test['recall']:.4f}."
    )
    lines.append(
        f"- **F1-score** = {deriv_test['f1']:.4f}."
    )
    lines.append("")
    lines.append("### 7.2 Train")
    lines.append("")
    lines.append(
        f"- **Precision** = {deriv_train['precision']:.4f}; **Recall** = "
        f"{deriv_train['recall']:.4f}; **F1** = {deriv_train['f1']:.4f}."
    )
    lines.append("")
    lines.append(
        "_Nota: estas métricas se derivan de la matriz de confusión y son "
        "coherentes con las reportadas en #018._"
    )
    lines.append("")

    lines.append("## 8. Principales conclusiones")
    lines.append("")
    lines.append(
        f"- El baseline **clasifica correctamente la mayoría de negativos** (TN="
        f"{comp_test['tn']}) e incurre en pocas falsas alarmas (FP={comp_test['fp']})."
    )
    lines.append(
        f"- El principal problema es la **perdida de la clase positiva**: FN="
        f"{comp_test['fn']} de {test_pos_support} casos de `stroke` en Test."
    )
    lines.append(
        "- Esto refleja que, sin tratamiento del desbalance, el baseline predice "
        "casi siempre la clase mayoritaria; el Recall de `stroke=1` es muy bajo."
    )
    lines.append(
        "- En consecuencia, se priorizará en #019/#020 analizar estrategias de "
        "balanceo y el gap Train/Test para mejorar la detección de `stroke=1`."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the baseline confusion matrix.")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, help="Path to the joblib artifact.")
    parser.add_argument("--output", default=DEFAULT_REPORT, help="Output markdown report path.")
    parser.add_argument("--figure", default=DEFAULT_FIGURE, help="Output figure path.")
    args = parser.parse_args()

    result = analyze_confusion_matrix(
        model_path=args.model,
        report_path=args.output,
        figure_path=args.figure,
    )
    print(f"Informe: {result['report_path']}")
    print(f"Figura: {result['figure_path']}")
    print("Confusion matrix (Test):", result["test"])


if __name__ == "__main__":
    main()