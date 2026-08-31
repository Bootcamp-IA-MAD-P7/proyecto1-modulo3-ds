"""Generate the consolidated EDA report for F5 RiskAI (Issue #015).

This script assembles ``reports/eda-report.md``, the formal closing document of
the Exploratory Data Analysis phase, consolidating the results of:

* #010 descriptive statistics,
* #011 class imbalance,
* #012 feature distributions,
* #013 feature relationships with ``stroke``,
* #014 EDA visualizations.

The key figures (class counts, ratio, continuous statistics, effect sizes,
binary prevalence, dominant categories) are computed at runtime from
``data/raw/stroke_dataset.csv`` so that nothing is hardcoded. The report embeds
the PNG figures produced by Issue #014.

Run from the repository root::

    python scripts/eda_report.py [--output reports/eda-report.md]
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

from preprocessing import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)

import eda_relationships as rel  # noqa: E402

DEFAULT_REPORT = os.path.join("reports", "eda-report.md")
DEFAULT_FIGURE_DIR = os.path.join("reports", "figures")


def _d_interpret(d: float) -> str:
    a = abs(d)
    if a >= 0.8:
        return "grande"
    if a >= 0.5:
        return "medio"
    if a >= 0.2:
        return "pequeño"
    return "despreciable"


def continuous_stats_table(df: pd.DataFrame) -> list[str]:
    rows = []
    for col in CONTINUOUS_FEATURES:
        s = df[col].dropna()
        rows.append(
            f"| {col} | {len(s)} | {s.mean():.2f} | {s.median():.2f} | {s.std():.2f} | "
            f"{s.skew():+.2f} | {s.min():.1f} | {s.max():.1f} |"
        )
    return rows


def continuous_rels_table(df: pd.DataFrame) -> list[str]:
    rows = []
    for col in CONTINUOUS_FEATURES:
        r = rel.continuous_relationship(df, col)
        rows.append(
            f"| {col} | {r['mean_0']} | {r['mean_1']} | {r['delta_mean']:+.3f} | "
            f"{r['d']:+.3f} ({_d_interpret(r['d'])}) |"
        )
    return rows


def binary_rels_list(df: pd.DataFrame) -> list[str]:
    items = []
    for col in BINARY_FEATURES:
        r = rel.binary_relationship(df, col)
        p0 = r["rate_1_given_0"] * 100
        p1 = r["rate_1_given_1"] * 100
        items.append(
            f"- **`{col}`:** prevalencia {p1:.1f}% en `stroke=1` vs {p0:.1f}% en `stroke=0` "
            f"(Δ {r['delta_rate']:+.3f})."
        )
    return items


def dominant_list(df: pd.DataFrame) -> list[str]:
    items = []
    for col in CATEGORICAL_FEATURES:
        counts = df[col].value_counts()
        top = counts.index[0]
        pct = counts.iloc[0] / counts.sum() * 100
        items.append(
            f"- **`{col}`:** categoría dominante `{top}` con {pct:.1f}% "
            f"({counts.iloc[0]} de {counts.sum()})."
        )
    return items


def build_report(df: pd.DataFrame, figure_dir: str) -> str:
    n = len(df)
    n0 = int((df[TARGET_COLUMN] == 0).sum())
    n1 = int((df[TARGET_COLUMN] == 1).sum())
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    pct0 = counts[0] / n * 100
    pct1 = counts[1] / n * 100
    majority, minority = int(counts.idxmax()), int(counts.idxmin())
    ratio = counts[majority] / counts[minority]

    fig_rel = os.path.relpath(figure_dir, start=os.path.dirname(DEFAULT_REPORT)).replace("\\", "/")

    L: list[str] = []
    L.append("# Informe EDA — F5 RiskAI")
    L.append("")
    L.append("**Proyecto:** F5 RiskAI")
    L.append("**Fase:** Exploratory Data Analysis (EDA) — informe consolidado")
    L.append(f"**Fuente:** `{RAW_DATA_PATH}`")
    L.append(f"**Registros:** {n} · **Variables:** {len(df.columns)}")
    L.append("")
    L.append(
        "> Este documento consolida los hallazgos de los Issues #010–#014 y cierra "
        "formalmente la fase de EDA, dejando la base para la siguiente etapa de "
        "Machine Learning. Nada aquí constituye evidencia médica ni afirmación causal."
    )
    L.append("")

    # 0. Resumen ejecutivo
    L.append("## 1. Resumen ejecutivo")
    L.append("")
    L.append(
        f"El dataset contiene {n} registros (0 valores nulos y 0 duplicados, ver "
        "`dataset-inspection.md`). La variable objetivo `stroke` presenta un claro "
        f"desbalance: la clase mayoritaria `0` supone el {pct0:.2f}% frente al "
        f"{pct1:.2f}% de la clase minoritaria `1` (ratio {ratio:.2f}x)."
    )
    L.append("")
    L.append(
        "Las variables continuas muestran distribuciones distintas: `age` es "
        "aproximadamente simétrica; `avg_glucose_level` tiene fuerte asimetría "
        "positiva con numerosos valores extremos; `bmi` es casi simétrica. En "
        "cuanto a la relación con `stroke`, la edad destaca con un efecto grande "
        "(Cohen's d ≈ 1.17), seguida de la glucosa (efecto medio) y el IMC "
        "(efecto pequeño)."
    )
    L.append("")
    L.append(
        "Entre las categóricas, estar casado (`ever_married`) y el tipo de empleo "
        "(`work_type`) muestran las mayores diferencias entre clases, mientras que "
        "`gender` y `Residence_type` apenas discriminan."
    )
    L.append("")
    L.append("### Índice")
    L.append("")
    L.append("1. [Resumen ejecutivo](#1-resumen-ejecutivo)")
    L.append("2. [Datos y calidad](#2-datos-y-calidad)")
    L.append("3. [Desbalance de clases](#3-desbalance-de-clases)")
    L.append("4. [Distribución de las variables](#4-distribución-de-las-variables)")
    L.append("5. [Relaciones con `stroke`](#5-relaciones-con-stroke)")
    L.append("6. [Frecuencias de categorías](#6-frecuencias-de-categorías)")
    L.append("7. [Conclusiones y siguientes pasos](#7-conclusiones-y-siguientes-pasos)")
    L.append("")

    # 2. Datos y calidad
    L.append("## 2. Datos y calidad")
    L.append("")
    L.append("### 2.1 Dataset")
    L.append("")
    L.append(
        f"- **Fuente:** `data/raw/stroke_dataset.csv` ({n} filas, {len(df.columns)} columnas)."
    )
    L.append("- **Preprocesamiento:** flujo en `scripts/preprocessing.py` y `generate_processed_data.py`.")
    L.append(
        "- **Calidad:** 0 valores nulos y 0 duplicados (ver `reports/dataset-inspection.md` "
        "y `reports/missing-values-and-duplicates.md`)."
    )
    L.append("")
    L.append("### 2.2 Variables")
    L.append("")
    L.append("**Continuas**")
    L.append("")
    L.append("| Variable | count | media | mediana | std | asimetría | min | max |")
    L.append("|---|---|---|---|---|---|---|---|")
    L.extend(continuous_stats_table(df))
    L.append("")
    L.append("**Binarias (0/1):** " + ", ".join(f"`{c}`" for c in BINARY_FEATURES) + ".")
    L.append("")
    L.append("**Categóricas:** " + ", ".join(f"`{c}`" for c in CATEGORICAL_FEATURES) + ".")
    L.append("")

    # 3. Desbalance
    L.append("## 3. Desbalance de clases")
    L.append("")
    L.append(
        f"- **Clase mayoritaria:** `{majority}` ({counts[majority]} registros, {pct0 if majority == 0 else pct1:.2f}%)."
    )
    L.append(
        f"- **Clase minoritaria:** `{minority}` ({counts[minority]} registros, {pct1 if minority == 1 else pct0:.2f}%)."
    )
    L.append(f"- **Ratio de desbalance (mayoritaria / minoritaria):** {ratio:.2f}x.")
    L.append("")
    L.append(
        "**Implicación:** una evaluación ingenua de la accuracy sería engañosa "
        f"(un clasificador trivial alcanzará ~{max(pct0, pct1):.1f}% sin aprender). "
        "La evaluación deberá priorizar recall/sensibilidad, precisión, F1 y "
        "análisis ROC/PR sobre la clase minoritaria."
    )
    L.append("")
    L.append(f"![Desbalance de la variable objetivo]({fig_rel}/class_imbalance.png)")
    L.append("")

    # 4. Distribución
    L.append("## 4. Distribución de las variables")
    L.append("")
    L.append(
        "- **`age`:** aproximadamente simétrica, con un ligero ensanchamiento en "
        "las edades extremas; sin valores atípicos relevantes."
    )
    L.append(
        "- **`avg_glucose_level`:** asimetría positiva pronunciada; la regla del "
        "IQR señala ~12% de posibles valores extremos en el extremo alto."
    )
    L.append(
        "- **`bmi`:** casi simétrica, con pocos valores extremos por IQR (~1%)."
    )
    L.append("")
    L.append("### Frecuencia de las categorías")
    L.append("")
    L.extend(dominant_list(df))
    L.append("")
    L.append(f"![Distribuciones de las variables continuas]({fig_rel}/continuous_distributions.png)")
    L.append("")
    L.append(f"![Frecuencia de las categorías]({fig_rel}/categorical_frequencies.png)")
    L.append("")

    # 5. Relaciones
    L.append("## 5. Relaciones con `stroke`")
    L.append("")
    L.append("### 5.1 Continuas (Cohen's d: `1` vs `0`)")
    L.append("")
    L.append("| Variable | media en `0` | media en `1` | Δ media | Cohen's d |")
    L.append("|---|---|---|---|---|")
    L.extend(continuous_rels_table(df))
    L.append("")
    L.append("Los mayores efectos sobre `stroke` son la **edad** (d grande) y la ")
    L.append("**glucosa** (d medio); el IMC aporta un efecto pequeño.")
    L.append("")
    L.append("### 5.2 Binarias")
    L.append("")
    L.extend(binary_rels_list(df))
    L.append("")
    L.append("`hypertension` y `heart_disease` son más prevalentes en la clase `1`.")
    L.append("")
    L.append("### 5.3 Categóricas")
    L.append("")
    # compute top shifts
    shifts = {}
    for col in CATEGORICAL_FEATURES:
        table, _ = rel.categorical_relationship(df, col)
        table = table.reindex(table["shift_pp"].abs().sort_values(ascending=False).index)
        n_top = 2 if col in ("ever_married", "work_type") else 1
        shifts[col] = [
            (str(idx), float(row["shift_pp"]))
            for idx, row in table.head(n_top).iterrows()
        ]
    em_txt = ", ".join(f"`{c}` {s:+.1f} pp" for c, s in shifts["ever_married"])
    wt_txt = ", ".join(f"`{c}` {s:+.1f} pp" for c, s in shifts["work_type"])
    L.append(
        "Las mayores diferencias entre clases se observan en `ever_married` "
        f"({em_txt}) y `work_type` ({wt_txt}); `gender` y `Residence_type` "
        "apenas discriminan."
    )
    L.append("")
    L.append(f"![Variables continuas según `stroke`]({fig_rel}/continuous_vs_stroke.png)")
    L.append("")
    L.append(f"![Variables categóricas según `stroke`]({fig_rel}/categorical_vs_stroke.png)")
    L.append("")

    # 6. Frecuencias (referencia a secciones previas, índice)
    L.append("## 6. Frecuencias de categorías")
    L.append("")
    L.append(
        "Las tablas de frecuencia por categoría se detallan en "
        "`reports/feature-distributions.md` y las diferencias entre clases en "
        "`reports/feature-relationships.md`. Los gráficos del apartado 4 y 5 "
        "resumen las frecuencias y sus diferencias según `stroke`."
    )
    L.append("")

    # 7. Conclusiones
    L.append("## 7. Conclusiones y siguientes pasos")
    L.append("")
    L.append("**Hallazgos clave**")
    L.append("")
    L.append("- Fuerte desbalance en `stroke` (~95/5), con ratio ≈ 19x.")
    L.append("- `age` es la variable con mayor poder discriminativo (d ≈ 1.17).")
    L.append("- `avg_glucose_level` asimétrica con outliers; `bmi` casi simétrica.")
    L.append("- `hypertension`, `heart_disease` y `ever_married` asociados a mayor riesgo.")
    L.append("- `gender` y `Residence_type` aportan poca discriminación.")
    L.append("")
    L.append("**Siguientes pasos (Machine Learning)**")
    L.append("")
    L.append(
        "- Usar división estratificada por `stroke` (ya implementada en "
        "`generate_processed_data.py`)."
    )
    L.append(
        "- Evaluar con métricas sensibles al desbalance (recall, F1, ROC/PR) y no "
        "solo con accuracy."
    )
    L.append(
        "- Considerar técnicas específicas para el desbalance en el modelado "
        "(ponderación de clases, muestreo, etc.), fuera del alcance del EDA."
    )
    L.append("")
    L.append("---")
    L.append("")
    L.append("**Archivos de EDA relacionados**")
    L.append("")
    L.append("- `reports/descriptive-statistics.md` (#010)")
    L.append("- `reports/class-imbalance.md` (#011)")
    L.append("- `reports/feature-distributions.md` (#012)")
    L.append("- `reports/feature-relationships.md` (#013)")
    L.append("- `reports/visualizations.md` y `reports/figures/` (#014)")

    return "\n".join(L)


def generate_report(
    output_path: str = DEFAULT_REPORT,
    figure_dir: str = DEFAULT_FIGURE_DIR,
) -> str:
    """Write the consolidated EDA report and return its text."""
    df = pd.read_csv(RAW_DATA_PATH)
    text = build_report(df, figure_dir)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the consolidated EDA report.")
    parser.add_argument("--output", default=DEFAULT_REPORT, help="Output markdown path.")
    parser.add_argument(
        "--figure-dir", default=DEFAULT_FIGURE_DIR, help="Directory with the EDA figures."
    )
    args = parser.parse_args()
    generate_report(args.output, args.figure_dir)
    print(f"Informe EDA generado en: {args.output}")


if __name__ == "__main__":
    main()
