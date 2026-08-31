"""Analyze the distributions of the main features (Issue #012).

This EDA script examines how the main variables of the F5 RiskAI stroke dataset
are distributed: concentration of values, shape, possible skewness, possible
outliers, category frequencies and dominant / infrequent categories.

For continuous variables it computes (min, max, quantiles, mean, median, std,
skewness, kurtosis and the interquartile range) and identifies potential
outliers using the IQR rule. For categorical variables it reports the frequency
and share of each category plus the proportion represented by the most common
category.

All results are computed at runtime from ``data/raw/stroke_dataset.csv``; no
result is hardcoded. The script is read-only with respect to the data.

Run from the repository root::

    python scripts/eda_distributions.py [--output reports/feature-distributions.md]
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from preprocessing import RAW_DATA_PATH, TARGET_COLUMN

CONTINUOUS_FEATURES = ["age", "avg_glucose_level", "bmi"]
BINARY_FEATURES = ["hypertension", "heart_disease"]
CATEGORICAL_FEATURES = [
    "gender",
    "ever_married",
    "work_type",
    "Residence_type",
    "smoking_status",
]

DEFAULT_OUTPUT = os.path.join("reports", "feature-distributions.md")


def continuous_distribution(df: pd.DataFrame, col: str) -> dict:
    """Return shape/outlier metrics for a continuous variable."""
    s = df[col].dropna()
    q1 = float(s.quantile(0.25))
    q3 = float(s.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = s[(s < lower) | (s > upper)]
    return {
        "count": int(s.count()),
        "mean": round(float(s.mean()), 3),
        "median": round(float(s.median()), 3),
        "std": round(float(s.std()), 3),
        "skewness": round(float(s.skew()), 3),
        "kurtosis": round(float(s.kurtosis()), 3),
        "min": round(float(s.min()), 3),
        "q1": round(q1, 3),
        "q3": round(q3, 3),
        "max": round(float(s.max()), 3),
        "iqr": round(iqr, 3),
        "outlier_lower": round(lower, 3),
        "outlier_upper": round(upper, 3),
        "n_outliers": int(outliers.size),
        "pct_outliers": round(outliers.size / s.size * 100, 2),
    }


def categorical_distribution(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, str]:
    """Return a frequency table and the dominant category for a categorical var."""
    counts = df[col].value_counts().sort_values(ascending=False)
    pct = (counts / counts.sum() * 100).round(2)
    table = pd.DataFrame({"count": counts.astype(int), "percentage": pct})
    table.index.name = col
    table["share_dominant_pct"] = float(table["percentage"].iloc[0])
    return table, str(counts.idxmax())


def interpret_continuous(rows: dict[str, dict]) -> list[str]:
    """Return interpretation bullets for the continuous distributions."""
    lines: list[str] = []
    for col in CONTINUOUS_FEATURES:
        r = rows[col]
        shape = (
            "asimetría positiva (cola hacia la derecha)" if r["skewness"] > 0.5
            else "asimetría negativa (cola hacia la izquierda)" if r["skewness"] < -0.5
            else "aproximadamente simétrica"
        )
        outliers_txt = (
            f"{r['n_outliers']} posibles valores extremos ({r['pct_outliers']}%) "
            f"según la regla del IQR"
        )
        lines.append(
            f"- **`{col}`:** {shape} (asimetría {r['skewness']:+.2f}); "
            f"media {r['mean']}, mediana {r['median']}; rango [{r['min']}, {r['max']}]; "
            f"IQR {r['iqr']}; {outliers_txt}."
        )
    return lines


def interpret_categorical(table: pd.DataFrame, col: str, n_total: int) -> str:
    """Return a one-line interpretation for a categorical distribution."""
    n_cat = len(table)
    top = table["percentage"].iloc[0]
    if top > 60:
        return (
            f"concentración alta: la categoría `{table.index[0]}` supone el "
            f"{top:.1f}% de los {n_total} registros."
        )
    return (
        f"más repartida: la categoría `{table.index[0]}` es la más frecuente con "
        f"el {top:.1f}%, entre {n_cat} categorías."
    )


def build_report(df: pd.DataFrame) -> str:
    """Build the feature-distribution markdown report text."""
    cont_rows = {c: continuous_distribution(df, c) for c in CONTINUOUS_FEATURES}
    cat_rows = {c: categorical_distribution(df, c) for c in CATEGORICAL_FEATURES}

    n_rows = len(df)
    lines: list[str] = []
    lines.append("# Informe — Distribución de las Variables")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Etapa:** Análisis de distribuciones (EDA)")
    lines.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    lines.append(f"**Total de registros:** {n_rows}")
    lines.append("")
    lines.append(
        "> **Nota:** Análisis descriptivo de las distribuciones. No constituye "
        "evidencia médica ni afirmación causal."
    )
    lines.append("")

    # Continuous
    lines.append("## 1. Variables continuas")
    lines.append("")
    lines.append("### 1.1 Métricas de forma y dispersión")
    lines.append("")
    lines.append(
        "| Variable | count | media | mediana | std | asimetría | curtosis | min | q1 | q3 | max | IQR |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    for c in CONTINUOUS_FEATURES:
        r = cont_rows[c]
        lines.append(
            f"| {c} | {r['count']} | {r['mean']} | {r['median']} | {r['std']} | "
            f"{r['skewness']:+.3f} | {r['kurtosis']:+.3f} | {r['min']} | {r['q1']} | "
            f"{r['q3']} | {r['max']} | {r['iqr']} |"
        )
    lines.append("")
    lines.append("### 1.2 Posibles valores extremos (regla del IQR)")
    lines.append("")
    for c in CONTINUOUS_FEATURES:
        r = cont_rows[c]
        lines.append(
            f"- `{c}`: {r['n_outliers']} valores por debajo de {r['outlier_lower']} "
            f"o por encima de {r['outlier_upper']} ({r['pct_outliers']}% del total)."
        )
    lines.append("")
    lines.append("### 1.3 Interpretación")
    lines.append("")
    lines.extend(interpret_continuous(cont_rows))
    lines.append("")

    # Categorical
    lines.append("## 2. Variables categóricas")
    lines.append("")
    for col in CATEGORICAL_FEATURES:
        table, dom = cat_rows[col]
        lines.append(f"### 2.{CATEGORICAL_FEATURES.index(col) + 1}. `{col}`")
        lines.append("")
        lines.append(
            f"- **Categorías presentes ({len(table)}):** {', '.join(map(str, table.index.tolist()))}"
        )
        lines.append(
            f"- **Categoría dominante:** `{dom}` ({int(table.loc[dom, 'count'])} registros, "
            f"{table.loc[dom, 'percentage']}%)."
        )
        lines.append("")
        lines.append("| Categoría | Nº | % |")
        lines.append("|---|---|---|")
        for idx, row in table.iterrows():
            lines.append(f"| {idx} | {int(row['count'])} | {row['percentage']} |")
        lines.append("")
        lines.append("    → " + interpret_categorical(table, col, n_rows))
        lines.append("")

    # Binary
    lines.append("## 3. Variables binarias")
    lines.append("")
    lines.append(
        "``hypertension`` y ``heart_disease`` son indicadores 0/1; se reporta su "
        "frecuencia, no se tratan como variables continuas."
    )
    lines.append("")
    for col in BINARY_FEATURES:
        counts = df[col].value_counts().sort_index()
        pct = (counts / counts.sum() * 100).round(2)
        lines.append(f"### 3.{BINARY_FEATURES.index(col) + 1}. `{col}`")
        lines.append("")
        lines.append("| Valor | Nº | % |")
        lines.append("|---|---|---|")
        for val in counts.index:
            lines.append(f"| {val} | {int(counts[val])} | {pct[val]} |")
        lines.append("")

    return "\n".join(lines)


def generate_report(output_path: str) -> str:
    """Write the distributions report to ``output_path`` and return its text."""
    df = pd.read_csv(RAW_DATA_PATH)
    text = build_report(df)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate feature distributions report.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output markdown path.")
    args = parser.parse_args()
    generate_report(args.output)
    print(f"Informe generado en: {args.output}")


if __name__ == "__main__":
    main()
