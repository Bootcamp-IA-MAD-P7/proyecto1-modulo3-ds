"""Analyze the feature importance of the Logistic Regression baseline (Issue #021).

This module inspects the fitted ``LogisticRegression`` inside the baseline
Pipeline trained in Issue #017. It retrieves ``coef_`` after preprocessing and
associates each coefficient with its transformed feature name via
``get_transformed_feature_names``.

The analysis is purely interpretative: the model artifact is loaded as-is, never
re-trained, re-fit, balanced, tuned, or re-thresholded. The raw dataset is never
modified.

Outputs:
* ``reports/baseline-feature-importance.md``  (markdown report, nine sections)
* ``reports/figures/baseline-feature-coefficients.png`` (horizontal bar chart)
"""

from __future__ import annotations

import os
from typing import Iterable

import matplotlib

matplotlib.use("Agg")  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import evaluate_baseline as ev  # noqa: E402
from evaluate_baseline import load_model  # noqa: E402
from preprocessing import get_transformed_feature_names  # noqa: E402

DEFAULT_MODEL_PATH = ev.DEFAULT_MODEL_PATH
DEFAULT_REPORT_PATH = os.path.join("reports", "baseline-feature-importance.md")
DEFAULT_FIGURE_PATH = os.path.join(
    "reports", "figures", "baseline-feature-coefficients.png"
)
DPI = 150
N_TOP = 10


def load_model_and_coefficients(model_path: str = DEFAULT_MODEL_PATH):
    """Load the Pipeline and return ``(model, coef_vector, feature_names)``.

    Returns
    -------
    tuple[LogisticRegression, np.ndarray, list[str]]
        The classifier, the flattened coefficient vector, and the transformed
        feature names in the same order as the coefficients.
    """
    pipeline = load_model(model_path)
    if not hasattr(pipeline, "named_steps") or "model" not in pipeline.named_steps:
        raise ValueError("El artefacto no es un Pipeline con un paso 'model'.")
    model = pipeline.named_steps["model"]
    if not hasattr(model, "coef_"):
        raise ValueError("El modelo no expone coef_ (no está entrenado).")
    feature_names = get_transformed_feature_names(pipeline.named_steps["preprocess"])
    coef = np.ravel(model.coef_)
    return model, coef, feature_names


def build_coefficient_table(
    coef: Iterable[float], feature_names: Iterable[str]
) -> pd.DataFrame:
    """Build a DataFrame ``feature / coefficient / abs_coefficient`` sorted by
    absolute coefficient descending."""
    df = pd.DataFrame(
        {
            "feature": list(feature_names),
            "coefficient": [float(c) for c in coef],
        }
    )
    df["abs_coefficient"] = df["coefficient"].abs()
    df = df.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)
    return df


def top_n(df: pd.DataFrame, n: int = N_TOP, positive: bool = True) -> pd.DataFrame:
    """Return the top ``n`` features by absolute magnitude for a sign bucket.

    ``positive=True`` filters coefficients > 0 (features that increase the
    estted log-odds of ``stroke=1``); ``positive=False`` filters < 0.
    """
    if positive:
        subset = df[df["coefficient"] > 0]
    else:
        subset = df[df["coefficient"] < 0]
    return subset.sort_values("abs_coefficient", ascending=False).head(n).reset_index(drop=True)


def top_by_magnitude(df: pd.DataFrame, n: int = N_TOP) -> pd.DataFrame:
    """Return the top ``n`` features by absolute coefficient magnitude."""
    return df.head(n)


def plot_coefficients(df: pd.DataFrame, path: str = DEFAULT_FIGURE_PATH) -> str:
    """Plot the top absolute coefficients as a horizontal bar chart and save to
    ``path``. Uses one color per sign to aid reading without arbitrary clutter."""
    plot_df = df.head(15).sort_values("abs_coefficient")
    colors = ["#d62728" if c < 0 else "#1f77b4" for c in plot_df["coefficient"]]

    fig, ax = plt.subplots(figsize=(9, len(plot_df) * 0.4 + 1))
    ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Coeficiente (log-odds)")
    ax.set_ylabel("Feature transformada")
    ax.set_title("Coeficientes del baseline LogisticRegression (Issue #021)")
    fig.tight_layout()

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _fmt_table(df: pd.DataFrame) -> str:
    """Render a coefficient DataFrame as a markdown table string."""
    header = "| feature | coefficient | abs_coefficient |\n|---|---:|---:|\n"
    rows = [header]
    for _, row in df.iterrows():
        rows.append(
            f"| {row['feature']} | {row['coefficient']:.4f} | {row['abs_coefficient']:.4f} |"
        )
    return "\n".join(rows)


def build_report(
    table: pd.DataFrame,
    top_pos: pd.DataFrame,
    top_neg: pd.DataFrame,
    top_abs: pd.DataFrame,
    model_path: str,
) -> str:
    """Build the full markdown report as a single string (nine sections)."""
    block_pos = ["- " + r["feature"] for _, r in top_pos.iterrows()]
    block_neg = ["- " + r["feature"] for _, r in top_neg.iterrows()]
    block_abs = [
        f"- {r['feature']} ({r['abs_coefficient']:.4f})" for _, r in top_abs.iterrows()
    ]

    lines: list[str] = []
    lines.append("# Informe — Importancia de features del baseline")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Análisis de importancia de features (ML)")
    lines.append(f"**Artefacto evaluado:** `{model_path}`")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe analiza la relevancia de las features transformadas en las "
        "decisiones del baseline ``LogisticRegression`` (#017). Es un análisis de "
        "interpretación; no modifica el modelo ni aplica balanceo/tuning."
    )

    lines.append("")
    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Identificar qué features transformadas tienen mayor influencia en el "
        "modelo baseline de regresión logística, mediante el valor absoluto de sus "
        "coeficientes. El análisis se realiza sobre las features **después del "
        "preprocessing** (Issue #017) y es reproducible."
    )

    lines.append("")
    lines.append("## 2. Modelo")
    lines.append("")
    lines.append(
        "- Pipeline = ``preprocessing`` + ``LogisticRegression`` (artefacto #017), "
        "cargado tal cual, sin reentrenar."
    )
    lines.append(
        "- Los coeficientes ``coef_`` corresponden a la clase positiva "
        "``stroke=1``."
    )

    lines.append("")
    lines.append("## 3. Cómo se obtienen los coeficientes")
    lines.append("")
    lines.append(
        "Se carga el Pipeline completo. Se accede al paso ``model`` (la "
        "``LogisticRegression``) y se leen sus ``coef_``. Cada coeficiente se "
        "asocia con el nombre de su feature transformada usando "
        "``get_transformed_feature_names``, que expande las variables "
        "categóricas en sus dummies (e.g. ``gender`` -> ``gender_Female``). "
        "Este informe no hardcodea nombres de features."
    )

    lines.append("")
    lines.append("## 4. Tabla de coeficientes")
    lines.append("")
    lines.append("Ordenados por ``abs_coefficient`` (mayor a menor):")
    lines.append("")
    lines.extend(_fmt_table(table).split("\n"))

    lines.append("")
    lines.append("## 5. Top features positivas")
    lines.append("")
    lines.append("Coeficientes positivos **aumentan** los log-odds estimados de ``stroke=1``:")
    lines.append("")
    lines.extend(block_pos)

    lines.append("")
    lines.append("## 6. Top features negativas")
    lines.append("")
    lines.append("Coeficientes negativos **disminuyen** los log-odds estimados de ``stroke=1``:")
    lines.append("")
    lines.extend(block_neg)

    lines.append("")
    lines.append("## 7. Interpretación")
    lines.append("")
    lines.append(
        "- **Signo:** un coeficiente positivo aumenta el log-odds estimado de la "
        "clase positiva ``stroke=1``; uno negativo lo disminuye. Esto se expresa "
        "en lenguaje de modelo estadístico y **no implica causalidad médica**."
    )
    lines.append(
        "- **Variables categóricas:** el One-Hot Encoding convierte cada variable "
        "categórica en varias features. Los coeficientes pertenecen a las "
        "features transformadas (p. ej. ``gender_Female``) y no a la variable "
        "original completa."
    )
    lines.append(
        "- **Variables numéricas:** las features continuas estandarizadas con "
        "``StandardScaler`` tienen su coeficiente expresado por unidad de "
        "**desviación estándar**. No se comparan directamente coeficientes de "
        "representaciones incompatibles sin explicarlo."
    )
    lines.append(
        "- El ranking por ``abs_coefficient`` permite identificar las features de "
        f"mayor peso: {', '.join(block_abs[:5])}."
    )
    lines.append(
        "- Estos coeficientes son descriptivos del modelo sobre los datos; no "
        "demuestran causalidad clínica."
    )

    lines.append("")
    lines.append("## 8. Limitaciones")
    lines.append("")
    lines.append(
        "- Los coeficientes representan **asociaciones dentro del modelo**, no "
        "causalidad."
    )
    lines.append(
        "- El One-Hot Encoding genera features separadas por categoría; una única "
        "variable original se reparte en varias columnas."
    )
    lines.append(
        "- La magnitud de un coeficiente debe interpretarse teniendo en cuenta el "
        "preprocessing (escalado estandarizado, codificación one-hot)."
    )
    lines.append(
        "- 'Feature importance' aquí significa **importancia relativa dentro del "
        "modelo baseline**, no importancia clínica."
    )
    lines.append(
        "- El baseline predice casi siempre la clase mayoritaria; por ello los "
        "coeficientes describen un modelo con bajo recall de ``stroke=1`` y no "
        "deben leerse como un modelo óptimo de riesgo."
    )

    lines.append("")
    lines.append("## 9. Conclusión")
    lines.append("")
    lines.append(
        "El análisis de coeficientes revela qué features transformadas influyen "
        "más en los log-odds estimados del baseline. La interpretación del signo "
        "y la magnitud (considerando el preprocessing aportado por Issue #017) "
        "permite comparar la relevancia relativa dentro del modelo, sin afirmar "
        "causalidad y sin modificar el artefacto."
    )
    return "\n".join(lines)


def analyze_feature_importance(
    model_path: str = DEFAULT_MODEL_PATH,
    report_path: str = DEFAULT_REPORT_PATH,
    figure_path: str = DEFAULT_FIGURE_PATH,
) -> dict:
    """Run the full analysis: table, ranking, figure and report.

    Returns a dict with the table, the top dataframes and artifact paths.
    """
    _, coef, feature_names = load_model_and_coefficients(model_path)
    table = build_coefficient_table(coef, feature_names)
    top_pos = top_n(table, positive=True)
    top_neg = top_n(table, positive=False)
    top_abs = top_by_magnitude(table)

    figure = plot_coefficients(table, figure_path)
    report = build_report(table, top_pos, top_neg, top_abs, model_path)

    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    return {
        "table": table,
        "top_positive": top_pos,
        "top_negative": top_neg,
        "top_abs": top_abs,
        "report_path": report_path,
        "figure_path": figure,
    }


if __name__ == "__main__":
    result = analyze_feature_importance()
    print(f"Informe: {result['report_path']}")
    print(f"Figura: {result['figure_path']}")
    print("Top abs:")
    print(result["top_abs"].to_string(index=False))