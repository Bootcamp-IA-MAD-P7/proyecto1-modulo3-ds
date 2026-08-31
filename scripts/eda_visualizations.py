"""Create the final set of EDA visualizations for F5 RiskAI (Issue #014).

This script produces a small, clear set of PNG figures that summarise the
main findings of the previous issues:

* #010 descriptive statistics,
* #011 class imbalance,
* #012 feature distributions,
* #013 feature relationships with ``stroke``.

Figures are written to ``reports/figures/`` and a markdown report
``reports/visualizations.md`` embeds them so they can be reused in the EDA
report, README, technical presentation or project explanation.

Figures generated:

1. ``class_imbalance.png``        -- bar chart of the target distribution (#011)
2. ``continuous_distributions.png``-- grid of histograms + KDE (#010/#012)
3. ``continuous_vs_stroke.png``   -- boxplots per stroke class (#013)
4. ``categorical_frequencies.png``-- horizontal bars of category shares (#012)
5. ``categorical_vs_stroke.png``  -- grouped proportional bars (#013)

Everything is computed at runtime from ``data/raw/stroke_dataset.csv``; no
figure is hardcoded. The script is read-only with respect to the data.

Run from the repository root::

    python scripts/eda_visualizations.py [--output-dir reports/figures]
                                        [--report reports/visualizations.md]
"""

from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from preprocessing import (  # noqa: E402
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)

DEFAULT_FIGURE_DIR = os.path.join("reports", "figures")
DEFAULT_REPORT = os.path.join("reports", "visualizations.md")
DPI = 150

# Nice, accessible colour palette.
PALETTE = sns.color_palette("deep")

CLASS_LABELS = {0: "stroke = 0", 1: "stroke = 1"}
CLASS_COLORS = {0: PALETTE[0], 1: PALETTE[1]}

FIGURE_META = [
    ("class_imbalance.png", "Desbalance de la variable objetivo", "#011"),
    ("continuous_distributions.png", "Distribuciones de las variables continuas", "#010/#012"),
    ("continuous_vs_stroke.png", "Variables continuas según `stroke`", "#013"),
    ("categorical_frequencies.png", "Frecuencia de las categorías", "#012"),
    ("categorical_vs_stroke.png", "Variables categóricas según `stroke`", "#013"),
]


def _save(fig, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def plot_class_imbalance(df: pd.DataFrame, out_dir: str) -> str:
    """Figure 1: bar chart of the target class counts (Issue #011)."""
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    pct = counts / counts.sum() * 100
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        counts.index,
        counts.values,
        color=[CLASS_COLORS[int(v)] for v in counts.index],
        edgecolor="white",
    )
    for bar, v, p in zip(bars, counts.values, pct.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + counts.max() * 0.02,
            f"{v}\n({p:.2f}%)",
            ha="center",
            va="bottom",
        )
    ax.set_xticks(list(counts.index))
    ax.set_xticklabels([CLASS_LABELS[int(v)] for v in counts.index])
    ax.set_ylabel("Nº de registros")
    ax.set_title("Distribución de la variable objetivo `stroke`")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    path = os.path.join(out_dir, "class_imbalance.png")
    _save(fig, path)
    return path


def plot_continuous_distributions(df: pd.DataFrame, out_dir: str) -> str:
    """Figure 2: histograms + KDE of the continuous variables (#010/#012)."""
    n = len(CONTINUOUS_FEATURES)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, col in zip(axes, CONTINUOUS_FEATURES):
        sns.histplot(df[col], kde=True, ax=ax, color=PALETTE[0], edgecolor="white")
        ax.set_title(col)
        ax.set_xlabel(None)
        ax.set_ylabel("Frecuencia" if col == CONTINUOUS_FEATURES[0] else None)
    fig.suptitle("Distribuciones de las variables continuas", y=1.02)
    path = os.path.join(out_dir, "continuous_distributions.png")
    _save(fig, path)
    return path


def plot_continuous_vs_stroke(df: pd.DataFrame, out_dir: str) -> str:
    """Figure 3: boxplots of continuous vars split by stroke (#013)."""
    n = len(CONTINUOUS_FEATURES)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, col in zip(axes, CONTINUOUS_FEATURES):
        sns.boxplot(
            data=df,
            x=TARGET_COLUMN,
            y=col,
            ax=ax,
            hue=TARGET_COLUMN,
            palette=[CLASS_COLORS[0], CLASS_COLORS[1]],
            legend=False,
        )
        ax.set_xticks([0, 1])
        ax.set_xticklabels([CLASS_LABELS[0], CLASS_LABELS[1]])
        ax.set_xlabel(None)
        ax.set_title(col)
    fig.suptitle("Variables continuas según `stroke`", y=1.02)
    path = os.path.join(out_dir, "continuous_vs_stroke.png")
    _save(fig, path)
    return path


def plot_categorical_frequencies(df: pd.DataFrame, out_dir: str) -> str:
    """Figure 4: horizontal bars of category share for each categorical var (#012)."""
    n = len(CATEGORICAL_FEATURES)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, col in zip(axes, CATEGORICAL_FEATURES):
        counts = df[col].value_counts()
        pct = counts / counts.sum() * 100
        ax.barh(pct.index, pct.values, color=PALETTE[0], edgecolor="white")
        ax.invert_yaxis()
        ax.set_title(col)
        for y, p in enumerate(pct.values):
            ax.text(p + 1, y, f"{p:.1f}%", va="center")
        ax.set_xlabel("%")
        ax.set_xlim(0, max(pct.values) * 1.2)
    fig.suptitle("Frecuencia relativa de las categorías", y=1.02)
    path = os.path.join(out_dir, "categorical_frequencies.png")
    _save(fig, path)
    return path


def plot_categorical_vs_stroke(df: pd.DataFrame, out_dir: str) -> str:
    """Figure 5: grouped 100% stacked bars per categorical var by stroke (#013)."""
    n = len(CATEGORICAL_FEATURES)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 4), sharey=True)
    if n == 1:
        axes = [axes]
    for ax, col in zip(axes, CATEGORICAL_FEATURES):
        tab = pd.crosstab(df[col], df[TARGET_COLUMN], normalize="columns") * 100
        tab = tab.reindex(sorted(tab.index))
        x = range(len(tab.index))
        width = 0.35
        b0 = ax.bar(
            [i - width / 2 for i in x],
            tab[0].values,
            width,
            label="stroke = 0",
            color=CLASS_COLORS[0],
            edgecolor="white",
        )
        b1 = ax.bar(
            [i + width / 2 for i in x],
            tab[1].values,
            width,
            label="stroke = 1",
            color=CLASS_COLORS[1],
            edgecolor="white",
        )
        ax.set_xticks(x)
        ax.set_xticklabels(tab.index, rotation=45, ha="right")
        ax.set_ylabel("%" if col == CATEGORICAL_FEATURES[0] else None)
        ax.set_title(col)
        if col == CATEGORICAL_FEATURES[-1]:
            ax.legend(fontsize=8)
    fig.suptitle("Distribución de categorías dentro de cada clase de `stroke`", y=1.05)
    path = os.path.join(out_dir, "categorical_vs_stroke.png")
    _save(fig, path)
    return path


def build_report(out_dir: str, report_path: str) -> str:
    """Write a markdown report that embeds the generated figures."""
    fig_dir_link = os.path.relpath(out_dir, start=os.path.dirname(report_path))
    lines: list[str] = []
    lines.append("# Informe — Visualizaciones del EDA")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Etapa:** Visualizaciones del EDA (conjunto final)")
    lines.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "Conjunto de visualizaciones que resumen los hallazgos de los Issues "
        "#010 (descriptivas), #011 (desbalance), #012 (distribuciones) y #013 "
        "(relaciones con `stroke`)."
    )
    lines.append("")
    lines.append("Las imágenes se guardan en `reports/figures/` para su reutilización.")
    lines.append("")
    for fname, title, issue in FIGURE_META:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"*Issue relacionado: {issue}*")
        lines.append("")
        lines.append(f"![{title}]({fig_dir_link}/{fname})")
        lines.append("")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    text = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def generate_all(out_dir: str = DEFAULT_FIGURE_DIR, report_path: str = DEFAULT_REPORT) -> list[str]:
    """Generate all figures + report; return the list of figure paths."""
    df = pd.read_csv(RAW_DATA_PATH)
    os.makedirs(out_dir, exist_ok=True)
    figures = [
        plot_class_imbalance(df, out_dir),
        plot_continuous_distributions(df, out_dir),
        plot_continuous_vs_stroke(df, out_dir),
        plot_categorical_frequencies(df, out_dir),
        plot_categorical_vs_stroke(df, out_dir),
    ]
    build_report(out_dir, report_path)
    return figures


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EDA visualizations.")
    parser.add_argument("--output-dir", default=DEFAULT_FIGURE_DIR, help="Figures directory.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Report markdown path.")
    args = parser.parse_args()
    figures = generate_all(args.output_dir, args.report)
    print(f"Reporte: {args.report}")
    for f in figures:
        print(f"Figura: {f}")


if __name__ == "__main__":
    main()
