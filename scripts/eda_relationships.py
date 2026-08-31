"""Analyze the relationships between features and the target ``stroke`` (#013).

This EDA script compares how each main feature behaves between the two classes
``stroke = 0`` and ``stroke = 1``:

* continuous features: mean / median per class and the (unstandardised) effect
  size (Cohen's d) to quantify how separated the two class means are;
* binary features: class-conditional rate of ``1`` per class and how the
  prevalence differs between groups;
* categorical features: category mix within each class (percent distribution)
  and the resulting absolute shift for each category.

All results are computed at runtime from ``data/raw/stroke_dataset.csv``; no
result is hardcoded. The script is read-only with respect to the data.

Run from the repository root::

    python scripts/eda_relationships.py [--output reports/feature-relationships.md]
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from preprocessing import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)

DEFAULT_OUTPUT = os.path.join("reports", "feature-relationships.md")


def cohens_d(group_a: pd.Series, group_b: pd.Series) -> float:
    """Cohen's d effect size between two groups (uncorrected pooled std)."""
    a = group_a.dropna()
    b = group_b.dropna()
    na, nb = a.size, b.size
    if na == 0 or nb == 0:
        return float("nan")
    ma, mb = a.mean(), b.mean()
    pooled = np.sqrt(
        ((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2)
    )
    if pooled == 0:
        return float("nan")
    return round(float((ma - mb) / pooled), 3)


def continuous_relationship(df: pd.DataFrame, col: str) -> dict:
    """Compare a continuous variable between the two stroke classes."""
    pos = df.loc[df[TARGET_COLUMN] == 1, col]
    neg = df.loc[df[TARGET_COLUMN] == 0, col]
    return {
        "col": col,
        "mean_0": round(float(neg.mean()), 3),
        "median_0": round(float(neg.median()), 3),
        "mean_1": round(float(pos.mean()), 3),
        "median_1": round(float(pos.median()), 3),
        "d": cohens_d(pos, neg),
        "delta_mean": round(float(pos.mean() - neg.mean()), 3),
    }


def binary_relationship(df: pd.DataFrame, col: str) -> dict:
    """Compare the prevalence (rate of ``1``) of a binary var between classes."""
    total_0 = int((df[TARGET_COLUMN] == 0).sum())
    total_1 = int((df[TARGET_COLUMN] == 1).sum())
    rate_0 = float(df.loc[df[TARGET_COLUMN] == 0, col].mean())
    rate_1 = float(df.loc[df[TARGET_COLUMN] == 1, col].mean())
    return {
        "col": col,
        "rate_1_given_0": round(rate_0, 3),
        "rate_1_given_1": round(rate_1, 3),
        "delta_rate": round(rate_1 - rate_0, 3),
        "n_0": total_0,
        "n_1": total_1,
    }


def categorical_relationship(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, float]:
    """Compare the category distribution between the two stroke classes."""
    tab = pd.crosstab(df[col], df[TARGET_COLUMN], normalize="columns") * 100
    diff = (tab[1] - tab[0]).round(3)
    table = tab.round(2).rename(columns={0: "pct_stroke0", 1: "pct_stroke1"})
    table["shift_pp"] = diff
    table["n_stroke0"] = df.loc[df[TARGET_COLUMN] == 0, col].value_counts()
    table["n_stroke1"] = df.loc[df[TARGET_COLUMN] == 1, col].value_counts()
    table = table.reindex(sorted(table.index), axis=0)
    return table, float(diff.abs().max())


def interpret_continuous(r: dict) -> str:
    """One-line interpretation of a continuous relationship."""
    direction = "mayor en la clase `1`" if r["delta_mean"] > 0 else "menor en la clase `1`"
    d = r["d"]
    if abs(d) >= 0.8:
        mag = "efecto grande"
    elif abs(d) >= 0.5:
        mag = "efecto medio"
    elif abs(d) >= 0.2:
        mag = "efecto pequeño"
    else:
        mag = "efecto despreciable"
    return (
        f"- **`{r['col']}`:** media {direction} (Δ {r['delta_mean']:+.3f} "
        f"puntos: {r['mean_0']} vs {r['mean_1']}); Cohen's d = {r['d']:+.3f} ({mag})."
    )


def interpret_binary(r: dict) -> str:
    """One-line interpretation of a binary relationship."""
    return (
        f"- **`{r['col']}`:** prevalencia del indicador del "
        f"{round(r['rate_1_given_1'] * 100, 1)}% en la clase `1` frente al "
        f"{round(r['rate_1_given_0'] * 100, 1)}% en la clase `0` "
        f"(Δ {r['delta_rate']:+.3f} en tasa)."
    )


def build_report(df: pd.DataFrame) -> str:
    """Build the feature-relationships markdown report text."""
    cont = [continuous_relationship(df, c) for c in CONTINUOUS_FEATURES]
    binary = [binary_relationship(df, b) for b in BINARY_FEATURES]
    cat = {c: categorical_relationship(df, c) for c in CATEGORICAL_FEATURES}

    n0 = int((df[TARGET_COLUMN] == 0).sum())
    n1 = int((df[TARGET_COLUMN] == 1).sum())

    lines: list[str] = []
    lines.append("# Informe — Relación de las Variables con `stroke`")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Etapa:** Análisis de relaciones con la variable objetivo (EDA)")
    lines.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    lines.append(f"**Comparación:** `stroke = 0` (n={n0}) frente a `stroke = 1` (n={n1})")
    lines.append("")
    lines.append(
        "> **Nota:** Análisis descriptivo de asociaciones. **Correlación no implica "
        "causalidad**; no constituye evidencia médica."
    )
    lines.append("")

    # Continuous
    lines.append("## 1. Variables continuas vs. `stroke`")
    lines.append("")
    lines.append(
        "| Variable | media (0) | mediana (0) | media (1) | mediana (1) | Δ media | Cohen's d |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for r in cont:
        lines.append(
            f"| {r['col']} | {r['mean_0']} | {r['median_0']} | {r['mean_1']} | "
            f"{r['median_1']} | {r['delta_mean']:+.3f} | {r['d']:+.3f} |"
        )
    lines.append("")
    lines.append("### Interpretación (Cohen's d)")
    lines.append("")
    for r in cont:
        lines.append(interpret_continuous(r))
    lines.append("")

    # Binary
    lines.append("## 2. Variables binarias vs. `stroke`")
    lines.append("")
    lines.append(
        "| Variable | tasa en `0` | tasa en `1` | Δ tasa |"
    )
    lines.append("|---|---|---|---|")
    for r in binary:
        lines.append(
            f"| {r['col']} | {r['rate_1_given_0']:.3f} | {r['rate_1_given_1']:.3f} | "
            f"{r['delta_rate']:+.3f} |"
        )
    lines.append("")
    lines.append("### Interpretación")
    lines.append("")
    for r in binary:
        lines.append(interpret_binary(r))
    lines.append("")

    # Categorical
    lines.append("## 3. Variables categóricas vs. `stroke`")
    lines.append("")
    for i, col in enumerate(CATEGORICAL_FEATURES, start=1):
        table, max_shift = cat[col]
        lines.append(f"### 3.{i}. `{col}`")
        lines.append("")
        lines.append(
            "Distribución de cada categoría dentro de cada clase (%). `shift_pp` = "
            "diferencia en puntos porcentuales (`1` − `0`); mayor valor absoluto "
            f": {max_shift:.2f} pp."
        )
        lines.append("")
        lines.append(
            "| Categoría | n (0) | n (1) | % en 0 | % en 1 | shift (pp) |"
        )
        lines.append("|---|---|---|---|---|---|")
        for idx in table.index:
            row = table.loc[idx]
            lines.append(
                f"| {idx} | {int(row['n_stroke0'])} | {int(row['n_stroke1'])} | "
                f"{row['pct_stroke0']} | {row['pct_stroke1']} | {row['shift_pp']:+.2f} |"
            )
        lines.append("")
    lines.append("")
    return "\n".join(lines)


def generate_report(output_path: str) -> str:
    """Write the feature-relationships report to ``output_path`` and return it."""
    df = pd.read_csv(RAW_DATA_PATH)
    text = build_report(df)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate feature-vs-stroke relationships report."
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output markdown path.")
    args = parser.parse_args()
    generate_report(args.output)
    print(f"Informe generado en: {args.output}")


if __name__ == "__main__":
    main()
