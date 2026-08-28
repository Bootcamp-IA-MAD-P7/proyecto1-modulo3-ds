"""Generate descriptive statistics for the F5 RiskAI stroke dataset (Issue #010).

This script computes descriptive statistics (central tendency, dispersion,
ranges, category frequencies) for the raw dataset and writes a markdown report
to ``reports/descriptive-statistics.md``.

It is intentionally read-only for the data: it does not modify ``data/raw/``,
does not remove or impute any value, and does NOT transform the data for
Machine Learning or train any model.

Run from the repository root::

    python scripts/eda_descriptive.py [--output reports/descriptive-statistics.md]
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

DEFAULT_OUTPUT = os.path.join("reports", "descriptive-statistics.md")


def build_continuous_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a table of descriptive stats for continuous variables."""
    rows = {}
    for col in CONTINUOUS_FEATURES:
        s = df[col].dropna()
        rows[col] = {
            "count": int(s.count()),
            "mean": round(float(s.mean()), 3),
            "median": round(float(s.median()), 3),
            "std": round(float(s.std()), 3),
            "min": round(float(s.min()), 3),
            "25%": round(float(s.quantile(0.25)), 3),
            "50%": round(float(s.quantile(0.50)), 3),
            "75%": round(float(s.quantile(0.75)), 3),
            "max": round(float(s.max()), 3),
        }
    return pd.DataFrame(rows).T


def build_binary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return per-variable frequency tables for binary features."""
    tables = {}
    for col in BINARY_FEATURES:
        counts = df[col].value_counts().sort_index()
        pct = (counts / counts.sum() * 100).round(2)
        table = pd.DataFrame({"count": counts.astype(int), "percentage": pct})
        table.index.name = col
        tables[col] = table
    return tables


def build_categorical_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return per-variable frequency tables for categorical features."""
    tables = {}
    for col in CATEGORICAL_FEATURES:
        counts = df[col].value_counts().sort_values(ascending=False)
        pct = (counts / counts.sum() * 100).round(2)
        table = pd.DataFrame({"count": counts.astype(int), "percentage": pct})
        table.index.name = col
        predominant = counts.idxmax()
        tables[col] = (table, predominant)
    return tables


def _format_value(value) -> str:
    """Format a cell value for markdown.

    ``iterrows`` coerces rows with mixed dtypes to float, turning whole counts
    into ``2907.0``. Reformat integral floats to integers for cleaner output.
    """
    if isinstance(value, (float,)) and float(value).is_integer():
        return str(int(value))
    return str(value)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Render a pandas DataFrame as a GitHub-flavoured markdown table.

    The DataFrame index is rendered as the first column, with its name used as
    the first header cell.
    """
    columns = [df.index.name or "index"] + list(df.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join(["---"] * len(columns)) + "|"

    lines = [header, separator]
    for idx, row in df.iterrows():
        cells = [_format_value(idx)] + [_format_value(row[c]) for c in df.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def generate_report(output_path: str) -> str:
    """Compute statistics and write the markdown report. Returns the text."""
    df = pd.read_csv(RAW_DATA_PATH)

    n_rows, n_cols = df.shape

    continuous = build_continuous_table(df)
    binary_tables = build_binary_tables(df)
    categorical_tables = build_categorical_tables(df)

    # Target summary (basic context only; deep imbalance analysis is #011).
    target_counts = df[TARGET_COLUMN].value_counts().sort_index()
    target_pct = (target_counts / target_counts.sum() * 100).round(2)

    lines: list[str] = []
    lines.append("# Informe — Estadísticas Descriptivas del Dataset")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Etapa:** Análisis estadístico descriptivo (EDA)")
    lines.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    lines.append(f"**Filas:** {n_rows} | **Columnas:** {n_cols}")
    lines.append("")
    lines.append(
        "> **Nota:** Este informe describe los datos. Ningún resultado debe "
        "interpretarse como evidencia médica ni como afirmación causal."
    )
    lines.append("")

    # 1. Continuous
    lines.append("## 1. Variables numéricas continuas")
    lines.append("")
    lines.append("### 1.1 Tabla de estadísticos descriptivos")
    lines.append("")
    lines.append(dataframe_to_markdown(continuous))
    lines.append("")
    lines.append("### 1.2 Interpretación")
    lines.append("")
    lines.append(interpret_continuous(df))
    lines.append("")

    # 2. Binary
    lines.append("## 2. Variables binarias")
    lines.append("")
    lines.append(
        "``hypertension`` y ``heart_disease`` son indicadores binarios (0/1). "
        "No se interpretan como variables continuas; se reportan frecuencias."
    )
    lines.append("")
    for idx, col in enumerate(binary_tables.keys(), start=1):
        table = binary_tables[col]
        lines.append(f"### 2.{idx}. `{col}`")
        lines.append("")
        lines.append(dataframe_to_markdown(table))
        lines.append("")
        lines.append(f"- **Categoría predominante:** `{table['count'].idxmax()}` ({int(table.loc[table['count'].idxmax(), 'count'])} registros, {table.loc[table['count'].idxmax(), 'percentage']}%).")
        lines.append("")

    # 3. Categorical
    lines.append("## 3. Variables categóricas")
    lines.append("")
    for i, (col, (table, predominant)) in enumerate(categorical_tables.items(), start=1):
        lines.append(f"### 3.{i}. `{col}`")
        lines.append("")
        lines.append(f"- **Categorías presentes:** {', '.join(map(str, table.index.tolist()))}")
        lines.append(f"- **Categoría predominante:** `{predominant}` ({int(table.loc[predominant, 'count'])} registros, {table.loc[predominant, 'percentage']}%).")
        lines.append("")
        lines.append(dataframe_to_markdown(table))
        lines.append("")
        lines.append(
            "    → Interpretación: " + interpret_categorical(df, col, table, predominant)
        )
        lines.append("")

    # 4. Target
    lines.append("## 4. Variable objetivo `stroke`")
    lines.append("")
    lines.append(
        "``stroke`` es la variable objetivo binaria: 0 = sin ictus, 1 = con ictus. "
        "El análisis profundo del desbalance corresponde al Issue #011; aquí se "
        "incluye solo el conteo básico como contexto."
    )
    lines.append("")
    lines.append(dataframe_to_markdown(
        pd.DataFrame({
            "valor": target_counts.index,
            "count": target_counts.values.astype(int),
            "percentage": target_pct.values,
        })
    ))
    lines.append("")
    lines.append(
        f"    → La clase positiva (`stroke=1`) representa un {target_pct.get(1, 0):.2f}% "
        "de las muestras; se estudiará su tratamiento en el Issue #011."
    )
    lines.append("")

    # 5. Anomalies / notes
    lines.append("## 5. Observaciones automáticas y cuestiones a investigar")
    lines.append("")
    lines.append(
        "Las observaciones siguientes se derivan directamente de los datos. "
        "Aquellas que requieren una comprobación adicional se indican como "
        "**cuestión a investigar** y no como un hecho clínico confirmado."
    )
    lines.append("")
    lines.extend(build_observations(df, continuous, categorical_tables))
    lines.append("")

    text = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def relative_dispersion(df: pd.DataFrame) -> dict[str, float]:
    """Return the coefficient of variation (std / mean) per continuous variable.

    The coefficient of variation is a scale-free measure of relative
    dispersion, comparable across variables with different units and ranges.
    """
    cv = {}
    for col in CONTINUOUS_FEATURES:
        s = df[col].dropna()
        mean = float(s.mean())
        std = float(s.std())
        cv[col] = std / mean if mean != 0 else float("nan")
    return cv


def find_most_dispersed(df: pd.DataFrame) -> str:
    """Return the continuous variable with the highest relative dispersion."""
    cv = relative_dispersion(df)
    return max(cv, key=cv.get)


def interpret_continuous(df: pd.DataFrame) -> str:
    """Return a brief interpretation string for the continuous variables."""
    parts = []
    for col in CONTINUOUS_FEATURES:
        s = df[col].dropna()
        mean = s.mean()
        median = s.median()
        std = s.std()
        vmin, vmax = s.min(), s.max()
        spread = vmax - vmin
        skew = "sesgada" if abs(mean - median) > 0.1 * std else "relativamente simétrica"
        parts.append(
            f"- **`{col}`:** media {mean:.1f} vs mediana {median:.1f} ({skew}); "
            f"std {std:.1f}; rango [{vmin:.2f}, {vmax:.2f}] (amplitud {spread:.2f})."
        )

    cv = relative_dispersion(df)
    most = find_most_dispersed(df)
    cv_line = ", ".join(f"`{c}`: {cv[c]:.2f}" for c in CONTINUOUS_FEATURES)
    parts.append(
        f"- Dispersión relativa (coeficiente de variación = std/media): {cv_line}. "
        f"La variable con mayor dispersión relativa es `{most}` ({cv[most]:.2f})."
    )
    return "\n".join(parts)


def interpret_categorical(df: pd.DataFrame, col: str, table: pd.DataFrame, predominant) -> str:
    """Return a one-line interpretation for a categorical variable."""
    n = int(table["count"].sum())
    top_pct = float(table.loc[predominant, "percentage"])
    if col == "smoking_status":
        unknown = int(table.loc["Unknown", "count"]) if "Unknown" in table.index else 0
        unknown_pct = float(table.loc["Unknown", "percentage"]) if "Unknown" in table.index else 0.0
        return (
            f"`Unknown` se conserva como categoría válida con {unknown} registros "
            f"({unknown_pct:.2f}% del total); el resto se reparte entre las tres "
            "categorías de tabaquismo."
        )
    if top_pct > 60:
        return f"existe una categoría claramente dominante (`{predominant}` con {top_pct:.1f}% de los {n} registros)."
    return f"las categorías se distribuyen de forma más equilibrada; la mayor es `{predominant}` con {top_pct:.1f}%."


def build_observations(
    df: pd.DataFrame,
    continuous: pd.DataFrame,
    categorical_tables: dict,
) -> list[str]:
    """Return data-derived observations and open questions, as markdown bullets."""
    obs: list[str] = []

    bmi = continuous.loc["bmi"]
    obs.append(
        f"- **Cuestión a investigar (`bmi`):** el rango observado es "
        f"[{bmi['min']}, {bmi['max']}] (min {bmi['min']}). Revisar la "
        "plausibilidad de los valores extremos; esto requiere comprobación adicional."
    )

    glucose = continuous.loc["avg_glucose_level"]
    obs.append(
        f"- **Observación (`avg_glucose_level`):** máximo {glucose['max']} vs "
        f"mediana {glucose['median']} y media {glucose['mean']}. Hay una cola de "
        "valores altos; se sugiere investigar su distribución en el Issue #011."
    )

    age = continuous.loc["age"]
    obs.append(
        f"- **Cuestión a investigar (`age`):** valor mínimo de {age['min']}. "
        "Comprobar coherencia de los valores más bajos con el resto de variables."
    )

    unknown_table = categorical_tables.get("smoking_status")
    if unknown_table is not None:
        table = unknown_table[0]
        if "Unknown" in table.index:
            unknown = int(table.loc["Unknown", "count"])
            unknown_pct = float(table.loc["Unknown", "percentage"])
            obs.append(
                f"- **Observación (`smoking_status`):** `Unknown` se conserva como "
                f"categoría válida con {unknown} registros ({unknown_pct:.2f}% del "
                "total). Decidir su tratamiento en la etapa de modelado."
            )

    return obs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate descriptive statistics report.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output markdown path.")
    args = parser.parse_args()
    generate_report(args.output)
    print(f"Informe generado en: {args.output}")


if __name__ == "__main__":
    main()
