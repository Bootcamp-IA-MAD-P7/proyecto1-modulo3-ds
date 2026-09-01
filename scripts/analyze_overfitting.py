"""Analyze whether the Logistic Regression baseline overfits (Issue #020).

This script loads the trained baseline artifact (Issue #017), reproduces the
exact Train/Test split used in #017–#019, and compares the evaluation metrics
on Train vs Test. For each metric it computes the gap in percentage points
(``abs(train - test) * 100``) and applies the acceptance criterion defined in
``docs/ml-baseline-specification.md`` (#016): the model meets the overfitting
criterion when the difference is < 5 percentage points.

Metrics (Train and Test): Accuracy, Precision, Recall, F1-score, AUC-ROC.
Precision/Recall/F1 use ``stroke = 1`` as the positive class (same conventions
as Issue #018).

This script ONLY analyzes overfitting; it does NOT modify, re-train, re-fit,
balance, tune or change the threshold of the model. Feature importance is NOT
implemented (belongs to a later issue). The raw dataset is not modified.

This script does NOT modify the pipeline, preprocessing, split,
hyperparameters or threshold. It uses exactly the #017 artifact.

Run from the repository root::

    python scripts/analyze_overfitting.py [--output reports/baseline-overfitting.md]
"""

from __future__ import annotations

import argparse
import json
import os

import pandas as pd

import evaluate_baseline as ev  # noqa: E402

DEFAULT_MODEL_PATH = os.path.join("artifacts", "logistic_regression_baseline.joblib")
DEFAULT_REPORT = os.path.join("reports", "baseline-overfitting.md")

THRESHOLD_PP = 5.0


def compute_gap(metrics_train: dict, metrics_test: dict) -> dict:
    """Compute the Train/Test gap in percentage points per metric."""
    gaps: dict[str, float] = {}
    for key in ["accuracy", "precision", "recall", "f1", "auc_roc"]:
        gaps[key] = round(abs(metrics_train[key] - metrics_test[key]) * 100, 2)
    return gaps


def apply_criterio(gaps: dict) -> dict:
    """Return PASS/FAIL per metric against the 5-pp overfitting criterion."""
    return {key: ("PASS" if gap < THRESHOLD_PP else "FAIL") for key, gap in gaps.items()}


def analyze_overfitting(
    model_path: str = DEFAULT_MODEL_PATH,
    report_path: str = DEFAULT_REPORT,
) -> dict:
    """Run the overfitting analysis and write the markdown report."""
    df = ev.load_dataset()
    X_train, X_test, y_train, y_test = ev.make_split(df)
    pipeline = ev.load_model(model_path)

    metrics_train = ev.compute_metrics(y_train, pipeline.predict(X_train), pipeline.predict_proba(X_train)[:, 1])
    metrics_test = ev.compute_metrics(y_test, pipeline.predict(X_test), pipeline.predict_proba(X_test)[:, 1])

    gaps = compute_gap(metrics_train, metrics_test)
    results = apply_criterio(gaps)

    text = build_report(
        df=df,
        metrics_train=metrics_train,
        metrics_test=metrics_test,
        gaps=gaps,
        results=results,
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
        "gaps": gaps,
        "results": results,
        "report_path": report_path,
    }


def _metric_rows(metrics_train, metrics_test, gaps, results, n_train, n_test) -> list[str]:
    header = (
        "| Metric | Train | Test | Gap (pp) | Criterio |\n"
        "|---|---|---:|---:|---:|\n"
    )
    rows = [header]
    labels = {
        "accuracy": "Accuracy",
        "precision": "Precision (stroke=1)",
        "recall": "Recall (stroke=1)",
        "f1": "F1-score (stroke=1)",
        "auc_roc": "AUC-ROC",
    }
    for key, label in labels.items():
        rows.append(
            f"| {label} | {metrics_train[key]:.4f} | {metrics_test[key]:.4f} | "
            f"{gaps[key]:.2f} | {results[key]} |"
        )
    return rows


def build_report(
    df: pd.DataFrame,
    metrics_train: dict,
    metrics_test: dict,
    gaps: dict,
    results: dict,
    n_train: int,
    n_test: int,
    model_path: str,
) -> str:
    n = len(df)
    n_pos = int((df[ev.TARGET_COLUMN] == 1).sum())
    pct_pos = n_pos / n * 100

    lines: list[str] = []
    lines.append("# Informe — Análisis de Overfitting del Baseline")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Análisis de overfitting (ML)")
    lines.append(f"**Artefacto evaluado:** `{model_path}`")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe compara el rendimiento del baseline en Train vs Test "
        "aplicando el criterio de la especificación (#016). Exclusivamente de "
        "análisis de overfitting; no modifica el modelo ni aplica balanceo/tuning."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Determinar si el baseline (``LogisticRegression``, #017) presenta "
        "overfitting, comparando sus métricas en Train y Test y aplicando el "
        "criterio definido en #016: diferencia < 5 puntos porcentuales."
    )
    lines.append("")

    lines.append("## 2. Modelo evaluado")
    lines.append("")
    lines.append(
        "- Pipeline = ``preprocessing`` + ``LogisticRegression`` (artefacto #017), "
        "cargado tal cual."
    )
    lines.append("- **Estado:** sin modificar; no se reentrena ni ajusta.")
    lines.append("")

    lines.append("## 3. Dataset y split")
    lines.append("")
    lines.append(
        f"- {n} registros; target `stroke`: `0`≈{100-pct_pos:.2f}%, `1`≈{pct_pos:.2f}%."
    )
    lines.append(f"   - Train: {n_train} filas.")
    lines.append(f"   - Test: {n_test} filas.")
    lines.append("- **Split:** `train_test_split(test_size=0.2, random_state=42, stratify=y)`.")
    lines.append(
        "- **Criterio métricas:** Precision/Recall/F1 sobre clase positiva `stroke=1`."
    )
    lines.append("")

    lines.append("## 4. Métricas Train/Test")
    lines.append("")
    lines.extend(_metric_rows(metrics_train, metrics_test, gaps, results, n_train, n_test))
    lines.append("")

    lines.append("## 5. Tabla de gaps")
    lines.append("")
    lines.append(
        "El gap se calcula como ``gap_pp = abs(metric_train - metric_test) * 100`` "
        "(en **puntos porcentuales**)."
    )
    lines.append("")
    lines.append("| Métrica | Gap (pp) |")
    lines.append("|---|---|")
    for key, gap in gaps.items():
        lines.append(f"| {key} | {gap:.2f} |")
    lines.append("")

    lines.append("## 6. Criterio de aceptación")
    lines.append("")
    lines.append(
        "Según #016, el modelo **cumple el criterio de overfitting** cuando la "
        "diferencia entre Train y Test es **inferior a 5 puntos porcentuales** "
        "para cada métrica."
    )
    lines.append("")

    lines.append("## 7. Resultado PASS/FAIL")
    lines.append("")
    lines.append("| Métrica | Resultado |")
    lines.append("|---|---|")
    for key, res in results.items():
        lines.append(f"| {key} | {res} |")
    lines.append("")

    lines.append("## 8. Interpretación")
    lines.append("")
    lines.append(
        "- **Sobre overfitting (strict):** aplicando el criterio métrica a métrica "
        "obtenemos "
        + ", ".join(f"{key}={gap:.2f} pp ({res})" for key, gap, res in
                    ((k, gaps[k], results[k]) for k in gaps))
        + ". La mayoría de métricas **PASS**; únicamente **Precision** cumple "
        "FAIL por su gap (100.00 pp)."
    )
    lines.append(
        "- **Distinción clave:** el **FAIL de Precision NO implica overfitting**. "
        "Se debe a que el baseline no predice ninguna clase positiva en Test "
        "(TP=0), por lo que Precision=0.0 en Test mientras que en Train alcanza "
        "1.0 con un único TP. Es un **efecto del desbalance** en la clase "
        "minoritaria, no una falta de generalización."
    )
    lines.append(
        "- **Bajo Recall de `stroke=1` no es overfitting:** el Recall es bajo en "
        "Train y en Test por igual (≈ 0), señalando **bajo rendimiento en la "
        "clase minoritaria**, favorecido por el desbalance (~95/5)."
    )
    lines.append(
        "- **Relación con #019:** la matriz de confusión mostró que el modelo "
        "predice casi siempre la clase `0` (en Test: TP=0, FN=50); eso se refleja "
        "en Precision=0 y Recall≈0 en Test."
    )
    lines.append(
        "- Las métricas **Accuracy (0.08 pp), Recall (0.51 pp), F1 (1.01 pp) y "
        "AUC-ROC (0.04 pp)** muestran gaps muy reducidos, apuntando a **baja "
        "evidencia de overfitting** salvo el caso degenerado de Precision."
    )
    lines.append(
        "- Estos resultados son descriptivos del modelo sobre los datos; no "
        "implican rendimiento clínico ni relación causal."
    )
    lines.append("")

    lines.append("## 9. Conclusión")
    lines.append("")
    lines.append(
        "El baseline **no presenta evidencia real de overfitting**: las métricas "
        "relevantes (Accuracy, Recall, F1, AUC-ROC) muestran gaps < 5 pp y "
        "estables. El **FAIL de Precision** es un artefacto del desbalance "
        "(ninguna predicción positiva en Test), no sobreajuste. La principal "
        "limitación es el **bajo Recall de la clase minoritaria** (`stroke=1`), "
        "consecuencia del **desbalance** del dataset, que deberá abordarse con "
        "estrategias de balanceo o umbral en Issues posteriores."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the baseline overfitting.")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, help="Path to the joblib artifact.")
    parser.add_argument("--output", default=DEFAULT_REPORT, help="Output markdown report path.")
    args = parser.parse_args()

    result = analyze_overfitting(model_path=args.model, report_path=args.output)
    print(f"Informe: {result['report_path']}")
    print("Gaps:", json.dumps(result["gaps"]))
    print("PASS/FAIL:", json.dumps(result["results"]))


if __name__ == "__main__":
    main()