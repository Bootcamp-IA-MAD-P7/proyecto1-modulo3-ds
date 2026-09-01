"""Evaluate the Logistic Regression baseline for F5 RiskAI (Issue #018).

This script loads the trained baseline artifact (Pipeline = preprocessing +
LogisticRegression) trained in Issue #017, reproduces the exact same Train/Test
split, and computes the metrics defined in ``docs/ml-baseline-specification.md``
on both Train and Test.

Metrics computed (Train and Test):

* Accuracy
* Precision (class ``1`` = ``stroke``)
* Recall (class ``1``)
* F1-score (class ``1``)
* AUC-ROC

Accuracy is reported but flagged as insufficient given the strong class
imbalance (~95%/5%). The classification report (by class) is also generated.

This script ONLY evaluates; it does NOT modify, re-train, re-fit, balance or
tune the model. The raw dataset is not modified.

Run from the repository root::

    python scripts/evaluate_baseline.py [--output reports/baseline-evaluation.md]
"""

from __future__ import annotations

import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from preprocessing import (
    ALL_FEATURE_COLUMNS,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)

DEFAULT_MODEL_PATH = os.path.join("artifacts", "logistic_regression_baseline.joblib")
DEFAULT_REPORT = os.path.join("reports", "baseline-evaluation.md")

TEST_SIZE = 0.2
RANDOM_STATE = 42
POSITIVE_LABEL = 1  # stroke = 1


def load_model(path: str = DEFAULT_MODEL_PATH):
    """Load the trained Pipeline artifact, raising clear errors."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No existe el artefacto del modelo en '{path}'. Ejecuta antes "
            f"'scripts/train_baseline.py' (Issue #017)."
        )
    return joblib.load(path)


def load_dataset(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw dataset, validating the expected columns."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe el dataset en '{path}'.")
    df = pd.read_csv(path)
    expected = set(ALL_FEATURE_COLUMNS + [TARGET_COLUMN])
    if not expected.issubset(set(df.columns)):
        missing = expected - set(df.columns)
        raise ValueError(f"Faltan columnas esperadas en '{path}': {missing}.")
    return df


def make_split(df: pd.DataFrame):
    """Reproduce the exact Train/Test split used in Issue #017."""
    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    return train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    """Compute the evaluation metrics for a given split."""
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(
            float(precision_score(y_true, y_pred, pos_label=POSITIVE_LABEL, zero_division=0)), 4
        ),
        "recall": round(
            float(recall_score(y_true, y_pred, pos_label=POSITIVE_LABEL, zero_division=0)), 4
        ),
        "f1": round(
            float(f1_score(y_true, y_pred, pos_label=POSITIVE_LABEL, zero_division=0)), 4
        ),
        "auc_roc": round(float(_roc_auc(y_true, y_proba)), 4),
    }


def _roc_auc(y_true, y_proba) -> float:
    if len(np.unique(y_true)) < 2:
        return float("nan")
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    return float(auc(fpr, tpr))


def evaluate_baseline(
    model_path: str = DEFAULT_MODEL_PATH,
    report_path: str = DEFAULT_REPORT,
) -> dict:
    """Run the full evaluation and write the markdown report."""
    df = load_dataset()
    X_train, X_test, y_train, y_test = make_split(df)
    pipeline = load_model(model_path)

    # Predictions and probabilities (positive class stroke=1).
    pred_train = pipeline.predict(X_train)
    pred_test = pipeline.predict(X_test)
    proba_train = pipeline.predict_proba(X_train)[:, 1]
    proba_test = pipeline.predict_proba(X_test)[:, 1]

    metrics_train = compute_metrics(y_train, pred_train, proba_train)
    metrics_test = compute_metrics(y_test, pred_test, proba_test)

    class_report_train = classification_report(
        y_train, pred_train, output_dict=False, zero_division=0
    )
    class_report_test = classification_report(
        y_test, pred_test, output_dict=False, zero_division=0
    )

    text = build_report(
        df=df,
        metrics_train=metrics_train,
        metrics_test=metrics_test,
        class_report_train=class_report_train,
        class_report_test=class_report_test,
        n_train=len(y_train),
        n_test=len(y_test),
        model_path=model_path,
    )

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "train": metrics_train,
        "test": metrics_test,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
    }


def _pct(ratio: float) -> str:
    return f"{ratio * 100:.2f}%"


def _metric_row(metrics: dict) -> list[str]:
    return [
        f"| Accuracy | {metrics['accuracy']:.4f} |",
        f"| Precision (stroke=1) | {metrics['precision']:.4f} |",
        f"| Recall (stroke=1) | {metrics['recall']:.4f} |",
        f"| F1-score (stroke=1) | {metrics['f1']:.4f} |",
        f"| AUC-ROC | {metrics['auc_roc']:.4f} |",
    ]


def build_report(
    df: pd.DataFrame,
    metrics_train: dict,
    metrics_test: dict,
    class_report_train: str,
    class_report_test: str,
    n_train: int,
    n_test: int,
    model_path: str,
) -> str:
    n = len(df)
    n_positive = int((df[TARGET_COLUMN] == 1).sum())
    pct_positive = n_positive / n * 100
    pct_negative = 100 - pct_positive

    lines: list[str] = []
    lines.append("# Informe — Evaluación del Baseline de Logistic Regression")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Evaluación del baseline (ML)")
    lines.append(f"**Artefacto evaluado:** `{model_path}`")
    lines.append(f"**Fuente de datos:** `{RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe mide el rendimiento del baseline entrenado en el Issue #017 "
        "usando las métricas de la especificación (#016). Es exclusivamente de "
        "evaluación: no modifica el modelo, no aplica balanceo ni realiza tuning."
    )
    lines.append("")
    lines.append(
        "**Nota:** las métricas no afirman causalidad ni rendimiento clínico; son "
        "resultados descriptivos del modelo sobre los datos."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Medir el rendimiento del modelo baseline (``LogisticRegression``) sobre "
        "Train y Test, usando exactamente el split definido en #016/#017, para "
        "dejar base para el análisis de overfitting (#020) y decisiones posteriores."
    )
    lines.append("")

    lines.append("## 2. Modelo evaluado")
    lines.append("")
    lines.append(
        "- **Modelo:** Pipeline de scikit-learn = ``preprocessing`` + "
        "``LogisticRegression``."
    )
    lines.append("- **Preprocessing:** reutiliza `scripts/preprocessing.py` (ajustado solo con Train en #017).")
    lines.append(
        "- **Hiperparámetros:** ``C=1.0``, ``solver=lbfgs``, ``max_iter=100``, "
        "``random_state=42``, ``class_weight=None`` (sin balanceo)."
    )
    lines.append("- **Estado:** sin modificar; no se reentrena en este Issue.")
    lines.append("")

    lines.append("## 3. Dataset y split")
    lines.append("")
    lines.append(f"- **Registros:** {n} (sin nulos ni duplicados).")
    lines.append(
        f"- **Target `stroke`:** `0` ≈ {pct_negative:.2f}%, `1` ≈ {pct_positive:.2f}% "
        "(fuerte desbalance)."
    )
    lines.append("- **Split:** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.")
    lines.append(f"  - Train: {n_train} filas.")
    lines.append(f"  - Test: {n_test} filas.")
    lines.append(
        "- **Preprocessing:** ya ajustado en #017; en esta etapa no se vuelve a hacer `fit`."
    )
    lines.append("")
    lines.append(
        "_Criterio métricas:_ Precision, Recall y F1 se calculan sobre la **clase "
        "positiva `stroke = 1`** (`pos_label=1`)."
    )
    lines.append("")

    lines.append("## 4. Métricas Train")
    lines.append("")
    lines.append("| Metric | Valor |")
    lines.append("|---|---|")
    for row in _metric_row(metrics_train):
        lines.append(row)
    lines.append("")

    lines.append("## 5. Métricas Test")
    lines.append("")
    lines.append("| Metric | Valor |")
    lines.append("|---|---|")
    for row in _metric_row(metrics_test):
        lines.append(row)
    lines.append("")

    lines.append("## 6. Classification report")
    lines.append("")
    lines.append("### 6.1 Train")
    lines.append("")
    lines.append("```text")
    lines.append(class_report_train.rstrip())
    lines.append("```")
    lines.append("")
    lines.append("### 6.2 Test")
    lines.append("")
    lines.append("```text")
    lines.append(class_report_test.rstrip())
    lines.append("```")
    lines.append("")

    lines.append("## 7. Comparación Train vs Test")
    lines.append("")
    lines.append("| Metric | Train | Test |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Accuracy | {metrics_train['accuracy']:.4f} | {metrics_test['accuracy']:.4f} |")
    lines.append(f"| Precision | {metrics_train['precision']:.4f} | {metrics_test['precision']:.4f} |")
    lines.append(f"| Recall | {metrics_train['recall']:.4f} | {metrics_test['recall']:.4f} |")
    lines.append(f"| F1 | {metrics_train['f1']:.4f} | {metrics_test['f1']:.4f} |")
    lines.append(f"| AUC-ROC | {metrics_train['auc_roc']:.4f} | {metrics_test['auc_roc']:.4f} |")
    lines.append("")
    lines.append(
        "_Nota: esta tabla se prepara aquí por conveniencia; el análisis formal del "
        "gap (overfitting) se realizará en el Issue #020._"
    )
    lines.append("")

    lines.append("## 8. Observaciones")
    lines.append("")
    lines.append(
        "- La **Accuracy** no es suficiente para interpretar el modelo dado el fuerte "
        f"desbalance ({pct_positive:.2f}% de `stroke=1`): un clasificador trivial "
        f"que predijera siempre `0` alcanzaría ≈{pct_negative:.2f}%."
    )
    lines.append(
        "- Se presta especial atención a **Recall / Precision / F1 de `stroke=1`** "
        "y **AUC-ROC**."
    )
    lines.append(
        f"- En Test, el modelo alcanza Recall={metrics_test['recall']:.4f}, "
        f"Precision={metrics_test['precision']:.4f} y F1={metrics_test['f1']:.4f} "
        f"para la clase `stroke=1`, con AUC-ROC={metrics_test['auc_roc']:.4f}."
    )
    lines.append(
        "- El contraste Train/Test de cada métrica queda reflejado en la tabla del "
        "apartado 7; el análisis formal del gap se aborda en el Issue #020."
    )
    lines.append(
        "- Estos valores son descriptivos del modelo sobre los datos actuales; no "
        "implican rendimiento clínico ni relación causal con el ictus."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Logistic Regression baseline.")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, help="Path to the joblib artifact.")
    parser.add_argument("--output", default=DEFAULT_REPORT, help="Output markdown report path.")
    args = parser.parse_args()

    result = evaluate_baseline(model_path=args.model, report_path=args.output)

    print("Evaluación del baseline completada")
    print(f"  Informe: {args.output}")
    print("  Métricas Train:", json.dumps(result["train"]))
    print("  Métricas Test: ", json.dumps(result["test"]))


if __name__ == "__main__":
    main()
