"""Analyze the class imbalance of the target variable ``stroke`` (Issue #011).

This script quantifies the imbalance between the majority and minority classes
of ``stroke`` directly from the raw dataset and writes a markdown report to
``reports/class-imbalance.md``.

Computed metrics:

* records per class,
* percentage per class,
* imbalance ratio (majority / minority),
* majority class,
* minority class.

All values are computed at runtime from ``data/raw/stroke_dataset.csv``; no
result is hardcoded.

The script is read-only with respect to the data: it does not modify
``data/raw/`` and does NOT apply SMOTE, oversampling or undersampling (those
are out of scope). It only quantifies the imbalance and explains its
implications for future model evaluation.

Run from the repository root::

    python scripts/eda_imbalance.py [--output reports/class-imbalance.md]
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from preprocessing import RAW_DATA_PATH, TARGET_COLUMN

DEFAULT_OUTPUT = os.path.join("reports", "class-imbalance.md")


def compute_imbalance(df: pd.DataFrame) -> dict:
    """Compute class-imbalance metrics for the target column.

    Returns a dict with counts, percentages, the majority/minority classes and
    the imbalance ratio. The ratio is computed as `majority_count /
    minority_count` so that it is always >= 1.
    """
    counts = df[TARGET_COLUMN].value_counts().sort_index()

    majority_value = int(counts.idxmax())
    minority_value = int(counts.idxmin())

    majority_count = int(counts.max())
    minority_count = int(counts.min())

    total = int(counts.sum())
    majority_pct = round(majority_count / total * 100, 2)
    minority_pct = round(minority_count / total * 100, 2)

    imbalance_ratio = round(majority_count / minority_count, 2)

    return {
        "total": total,
        "counts": {int(k): int(v) for k, v in counts.items()},
        "percentages": {int(k): round(v / total * 100, 2) for k, v in counts.items()},
        "majority_value": majority_value,
        "majority_count": majority_count,
        "majority_pct": majority_pct,
        "minority_value": minority_value,
        "minority_count": minority_count,
        "minority_pct": minority_pct,
        "imbalance_ratio": imbalance_ratio,
    }


def build_report(df: pd.DataFrame) -> str:
    """Return the markdown report text for the imbalance analysis."""
    m = compute_imbalance(df)

    lines: list[str] = []
    lines.append("# Informe — Análisis de Desbalance de la Variable Objetivo")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Etapa:** Análisis de desbalance de clases (EDA)")
    lines.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    lines.append(f"**Total de registros:** {m['total']}")
    lines.append("")
    lines.append(
        "> **Nota:** Este análisis describe la distribución de la variable "
        "objetivo y sus implicaciones para la evaluación del modelo. No "
        "constituye evidencia médica ni afirmación causal."
    )
    lines.append("")

    lines.append("## 1. Distribución de clases")
    lines.append("")
    lines.append("| Clase (`stroke`) | Nº registros | Porcentaje |")
    lines.append("|---|---|---|")
    for k in sorted(m["counts"]):
        lines.append(f"| {k} | {m['counts'][k]} | {m['percentages'][k]}% |")
    lines.append("")
    lines.append(f"- **Clase mayoritaria:** `{m['majority_value']}` ({m['majority_count']} registros, {m['majority_pct']}%).")
    lines.append(f"- **Clase minoritaria:** `{m['minority_value']}` ({m['minority_count']} registros, {m['minority_pct']}%).")
    lines.append("")
    lines.append(f"- **Ratio de desbalance (mayoritaria / minoritaria):** {m['imbalance_ratio']}x")
    lines.append("")
    lines.append("## 2. Interpretación")
    lines.append("")
    lines.append(
        f"La clase `{m['majority_value']}` es mayoritaria con un "
        f"{m['majority_pct']}% de los registros, frente a un {m['minority_pct']}% "
        f"para la clase `{m['minority_value']}`. Existe un ratio de desbalance de "
        f"{m['imbalance_ratio']}x, lo que implica que una evaluación ingenua de la "
        "precisión no reflejaría el rendimiento real sobre la clase minoritaria."
    )
    lines.append("")
    lines.append("### Implicaciones para la evaluación del modelo")
    lines.append("")
    lines.append(
        "- La **accuracy global** puede ser engañosa: un modelo que siempre "
        f"predijera la clase mayoritaria alcanzaría ~{m['majority_pct']}% de "
        "acierto sin aprender nada."
    )
    lines.append(
        "- En la futura evaluación se deberán priorizar métricas que penalicen "
        "los falsos negativos de la clase minoritaria (p. ej. sensibilidad / "
        "recall, precisión, F1, y análisis de la curva ROC/PR)."
    )
    lines.append(
        "- El desbalance puede requerir estrategias específicas en el modelado "
        "(muestreo, ponderación de clases, etc.). Su tratamiento queda fuera de "
        "este Issue (análisis únicamente)."
    )

    return "\n".join(lines)


def generate_report(output_path: str) -> str:
    """Write the imbalance report to ``output_path`` and return its text."""
    df = pd.read_csv(RAW_DATA_PATH)
    text = build_report(df)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate class imbalance analysis report."
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output markdown path.")
    args = parser.parse_args()
    generate_report(args.output)
    print(f"Informe generado en: {args.output}")


if __name__ == "__main__":
    main()
