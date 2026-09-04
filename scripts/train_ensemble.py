"""Train ensemble candidate models for F5 RiskAI (Issue #049).

This script trains the candidate models needed for future ensemble construction
and comparison (Issue #050). Each model is trained using the existing Train/Test
split, with **RandomOverSampler** applied inside an ``imblearn.Pipeline`` to
mitigate class imbalance (strategy validated in Issue #048).

Models trained
--------------
1. **LogisticRegression** — tabular, with ROS.
2. **LinearSVC + CalibratedClassifierCV** — tabular, with ROS.
3. **ComplementNB** — tabular, with ROS and MinMaxScaler (non-negative features).
4. **LightGBM** — tabular, with ROS.
5. **DeBERTa-v3-small** — **NOT trained** (no text column in the dataset).

Data conventions
----------------
The existing Train/Test split from the baseline (``test_size=0.20``,
``random_state=42``, ``stratify=y``) is reproduced via
``evaluate_baseline.make_split``. All models train on the training set only.
The reserved test set is never used during training.

Preprocessing
-------------
Each model receives the same ColumnTransformer extracted from
``build_preprocessing_pipeline()``. The ColumnTransformer is used directly (not
wrapped in a ``sklearn.Pipeline``) to avoid the imblearn nested-Pipeline error.
The exception is ComplementNB, which uses a dedicated ColumnTransformer with
``MinMaxScaler`` (non-negative requirement).

Run from the repository root::

    python scripts/train_ensemble.py [--output-dir artifacts]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
from preprocessing import (  # noqa: E402
    ALL_FEATURE_COLUMNS,
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_COLUMN,
)

DEFAULT_OUTPUT_DIR = "artifacts"
DEFAULT_REPORT = os.path.join("reports", "ensemble-training.md")

# Reproducibility.
RANDOM_STATE = 42
OVERSAMPLE_RANDOM_STATE = 42

# Logistic Regression hyperparameters matching the baseline (#017).
LR_PARAMS = {"C": 1.0, "solver": "lbfgs", "max_iter": 100, "random_state": RANDOM_STATE}

# LightGBM hyperparameters.
LGBM_PARAMS = {
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": -1,
    "num_leaves": 31,
    "random_state": RANDOM_STATE,
    "verbose": -1,
}


def build_column_transformer(scaler=None):
    """Return a ColumnTransformer with the specified scaler.

    The default ``scaler=None`` uses ``StandardScaler`` (same as the baseline).
    Pass ``MinMaxScaler()`` for models that require non-negative features
    (e.g. ComplementNB).
    """
    if scaler is None:
        scaler = StandardScaler()

    continuous_transformer = Pipeline(steps=[("scaler", scaler)])

    return ColumnTransformer(
        transformers=[
            ("scale_continuous", continuous_transformer, CONTINUOUS_FEATURES),
            ("binary_passthrough", "passthrough", BINARY_FEATURES),
            ("encode_categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def build_baseline_preprocessing():
    """Return the standard ColumnTransformer (StandardScaler)."""
    return build_column_transformer(scaler=StandardScaler())


def build_nb_preprocessing():
    """Return a ColumnTransformer with MinMaxScaler for ComplementNB."""
    return build_column_transformer(scaler=MinMaxScaler())


def build_logistic_regression_pipeline():
    """LogisticRegression with preprocessing + ROS."""
    return ImbPipeline([
        ("preprocess", build_baseline_preprocessing()),
        ("sampler", RandomOverSampler(random_state=OVERSAMPLE_RANDOM_STATE)),
        ("model", LogisticRegression(**LR_PARAMS)),
    ])


def build_linear_svc_pipeline():
    """LinearSVC + CalibratedClassifierCV with preprocessing + ROS."""
    base_svc = LinearSVC(
        C=1.0,
        max_iter=1000,
        random_state=RANDOM_STATE,
    )
    calibrated = CalibratedClassifierCV(base_svc, cv=3, method="sigmoid")
    return ImbPipeline([
        ("preprocess", build_baseline_preprocessing()),
        ("sampler", RandomOverSampler(random_state=OVERSAMPLE_RANDOM_STATE)),
        ("model", calibrated),
    ])


def build_complement_nb_pipeline():
    """ComplementNB with MinMaxScaler preprocessing + ROS."""
    return ImbPipeline([
        ("preprocess", build_nb_preprocessing()),
        ("sampler", RandomOverSampler(random_state=OVERSAMPLE_RANDOM_STATE)),
        ("model", ComplementNB()),
    ])


def build_lightgbm_pipeline():
    """LightGBM with preprocessing + ROS."""
    import lightgbm as lgb

    return ImbPipeline([
        ("preprocess", build_baseline_preprocessing()),
        ("sampler", RandomOverSampler(random_state=OVERSAMPLE_RANDOM_STATE)),
        ("model", lgb.LGBMClassifier(**LGBM_PARAMS)),
    ])


MODEL_REGISTRY = {
    "logistic_regression": {
        "name": "LogisticRegression",
        "pipeline_fn": build_logistic_regression_pipeline,
        "artifact_name": "logistic_regression_ensemble.joblib",
    },
    "linear_svc": {
        "name": "LinearSVC (calibrated)",
        "pipeline_fn": build_linear_svc_pipeline,
        "artifact_name": "linear_svc_calibrated.joblib",
    },
    "complement_nb": {
        "name": "ComplementNB",
        "pipeline_fn": build_complement_nb_pipeline,
        "artifact_name": "complement_nb_ensemble.joblib",
    },
    "lightgbm": {
        "name": "LightGBM",
        "pipeline_fn": build_lightgbm_pipeline,
        "artifact_name": "lightgbm_ensemble.joblib",
    },
}


def train_model(key: str, X_train, y_train, output_dir: str) -> dict:
    """Train a single model, save its artifact, return metrics."""
    import joblib

    spec = MODEL_REGISTRY[key]
    pipe = spec["pipeline_fn"]()

    start = time.time()
    pipe.fit(X_train, y_train)
    elapsed = round(time.time() - start, 2)

    # Training predictions (on the training set, for reference only).
    y_pred = pipe.predict(X_train)
    metrics = ev.compute_metrics(y_train, y_pred, pipe.predict_proba(X_train)[:, 1])

    artifact_path = os.path.join(output_dir, spec["artifact_name"])
    joblib.dump(pipe, artifact_path)

    return {
        "key": key,
        "name": spec["name"],
        "artifact": artifact_path,
        "train_metrics": metrics,
        "train_time_s": elapsed,
        "n_train": int(len(y_train)),
    }


def train_all(output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    """Train all tabular models and return combined results."""
    import joblib

    df = ev.load_dataset()
    X_train, X_test, y_train, y_test = ev.make_split(df)
    y = df[ev.TARGET_COLUMN]

    os.makedirs(output_dir, exist_ok=True)

    results = {}
    for key in MODEL_REGISTRY:
        print(f"  Entrenando {MODEL_REGISTRY[key]['name']}...")
        res = train_model(key, X_train, y_train, output_dir)
        results[key] = res
        print(f"    -> {res['artifact']} ({res['train_time_s']}s)")

    # DeBERTa: document limitation.
    results["deberta"] = {
        "key": "deberta",
        "name": "DeBERTa-v3-small",
        "artifact": None,
        "train_metrics": None,
        "train_time_s": None,
        "n_train": int(len(y_train)),
        "limitation": (
            "Dataset has no text column. DeBERTa requires a textual corpus. "
            "The current dataset contains only tabular features (demographics, "
            "clinical indicators). DeBERTa cannot be trained without a "
            "compatible text field."
        ),
    }

    return {
        "models": results,
        "n_total": int(len(y)),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "n_pos_train": int((y_train == 1).sum()),
        "n_pos_test": int((y_test == 1).sum()),
    }


def build_report(results: dict) -> str:
    """Compose the markdown ensemble-training report."""
    models = results["models"]
    pct_pos_train = results["n_pos_train"] / results["n_train"] * 100

    lines: list[str] = []
    lines.append("# Informe — Entrenamiento de Modelos Candidatos para Ensemble")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Entrenamiento de modelos (ML, Issue #049)")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe documenta el entrenamiento de los modelos candidatos "
        "necesarios para construir y comparar un ensemble en el Issue #050. "
        "Cada modelo se entrena con **RandomOverSampler** para mitigar el "
        "desbalance de clases."
    )
    lines.append("")
    lines.append(
        "> **Nota:** las métricas de entrenamiento son referenciales; la "
        "comparación definitiva se realizará en #050."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Entrenar los modelos candidatos (LogisticRegression, LinearSVC "
        "calibrado, ComplementNB, LightGBM) y documentar su configuración, "
        "métricas de entrenamiento y artefactos generados, dejando todo "
        "preparado para la comparación en #050."
    )
    lines.append("")

    lines.append("## 2. Dataset utilizado")
    lines.append("")
    lines.append(
        f"- **Total:** {results['n_total']} registros "
        f"(clase 1 = ~{results['n_pos_train'] + results['n_pos_test']})."
    )
    lines.append(
        f"- **Train:** {results['n_train']} registros "
        f"({results['n_pos_train']} positivos, ~{pct_pos_train:.2f}%)."
    )
    lines.append(
        f"- **Test (reservado):** {results['n_test']} registros "
        f"({results['n_pos_test']} positivos)."
    )
    lines.append("")

    lines.append("## 3. Split utilizado")
    lines.append("")
    lines.append(
        "- **Split:** `train_test_split(test_size=0.20, random_state=42, "
        "stratify=y)` (reutilizado del baseline #017)."
    )
    lines.append(
        "- **Test set:** reservado y nunca utilizado durante el entrenamiento."
    )
    lines.append("")

    lines.append("## 4. Modelos entrenados")
    lines.append("")

    lines.append("| # | Modelo | Artefacto | Tiempo |")
    lines.append("|---|---|---|---:|")
    idx = 1
    for key in ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]:
        m = models[key]
        lines.append(f"| {idx} | {m['name']} | `{m['artifact']}` | {m['train_time_s']}s |")
        idx += 1
    lines.append(f"| — | DeBERTa-v3-small | *(no entrenado)* | — |")
    lines.append("")

    lines.append("## 5. Estrategia de desbalance")
    lines.append("")
    lines.append(
        "Todos los modelos tabulares utilizan **RandomOverSampler** aplicado "
        "dentro de un ``imblearn.Pipeline``, garantizando que el oversampling "
        "se ejecuta **únicamente sobre los datos de entrenamiento** de cada "
        "fold (sin leakage)."
    )
    lines.append("")
    lines.append("- **sampling_strategy:** auto (balancea la clase minoritaria).")
    lines.append(f"- **random_state:** {OVERSAMPLE_RANDOM_STATE}.")
    lines.append("")

    lines.append("## 6. Configuración principal de cada modelo")
    lines.append("")

    lines.append("### 6.1 LogisticRegression")
    lines.append("")
    lines.append(f"- **Preprocessing:** StandardScaler + OneHotEncoder (mismo que baseline).")
    lines.append(f"- **Hiperparámetros:** C={LR_PARAMS['C']}, solver='{LR_PARAMS['solver']}', "
                 f"max_iter={LR_PARAMS['max_iter']}, random_state={LR_PARAMS['random_state']}.")
    lines.append(f"- **Desbalance:** RandomOverSampler.")
    lines.append("")

    lines.append("### 6.2 LinearSVC (calibrado con CalibratedClassifierCV)")
    lines.append("")
    lines.append(f"- **Preprocessing:** StandardScaler + OneHotEncoder.")
    lines.append(f"- **LinearSVC:** C=1.0, max_iter=1000, random_state={RANDOM_STATE}.")
    lines.append(f"- **Calibración:** CalibratedClassifierCV(cv=3, method='sigmoid').")
    lines.append(f"- **Desbalance:** RandomOverSampler.")
    lines.append("")

    lines.append("### 6.3 ComplementNB")
    lines.append("")
    lines.append(f"- **Preprocessing:** MinMaxScaler (features no-negativas) + OneHotEncoder.")
    lines.append(f"- **Hiperparámetros:** default (alpha=1.0).")
    lines.append(f"- **Desbalance:** RandomOverSampler.")
    lines.append("")

    lines.append("### 6.4 LightGBM")
    lines.append("")
    lines.append(f"- **Preprocessing:** StandardScaler + OneHotEncoder.")
    lines.append(f"- **Hiperparámetros:** n_estimators={LGBM_PARAMS['n_estimators']}, "
                 f"learning_rate={LGBM_PARAMS['learning_rate']}, "
                 f"num_leaves={LGBM_PARAMS['num_leaves']}.")
    lines.append(f"- **Desbalance:** RandomOverSampler.")
    lines.append("")

    lines.append("### 6.5 DeBERTa-v3-small")
    lines.append("")
    lines.append(
        "- **No entrenado.** El dataset no contiene una columna de texto "
        "apropiada para un modelo de lenguaje. DeBERTa requiere un corpus "
        "textual; las variables del dataset son puramente tabulares "
        "(demográficas y clínicas)."
    )
    lines.append("")

    lines.append("## 7. Métricas de entrenamiento")
    lines.append("")
    lines.append(
        "Las métricas se calculan sobre el **conjunto de entrenamiento** "
        "(referenceles). La evaluación formal se realizará en #050."
    )
    lines.append("")
    lines.append("| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for key in ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]:
        m = models[key]["train_metrics"]
        lines.append(
            f"| {models[key]['name']} | {m['accuracy']:.4f} | {m['precision']:.4f} | "
            f"{m['recall']:.4f} | {m['f1']:.4f} | {m['auc_roc']:.4f} |"
        )
    lines.append("")

    lines.append("## 8. Artefactos generados")
    lines.append("")
    lines.append("| Archivo | Modelo |")
    lines.append("|---|---|")
    for key in ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]:
        lines.append(f"| `{models[key]['artifact']}` | {models[key]['name']} |")
    lines.append("")
    lines.append(
        "> **No se sobrescribe** el baseline existente: "
        "`artifacts/logistic_regression_baseline.joblib`."
    )
    lines.append("")

    lines.append("## 9. Limitaciones")
    lines.append("")
    lines.append(
        "- Las métricas de entrenamiento son **referenciales** y no deben "
        "interpretarse como rendimiento generalizado."
    )
    lines.append(
        "- **DeBERTa-v3-small** no pudo entrenarse por la ausencia de una "
        "columna de texto en el dataset."
    )
    lines.append(
        "- ComplementNB utiliza MinMaxScaler (en lugar de StandardScaler) para "
        "garantizar features no-negativas. Esto puede afectar la distribución "
        "de las features continuas."
    )
    lines.append(
        "- LightGBM con oversampling puede tener un costo computacional mayor "
        "debido al aumento de muestras."
    )
    lines.append(
        "- No se realizó tuning de hiperparámetros; los valores son defaults "
        "o los mismos del baseline."
    )
    lines.append("")

    lines.append("## 10. Próximo paso")
    lines.append("")
    lines.append(
        "Comparar los modelos entrenados en el Issue #050, evaluando su "
        "rendimiento en el conjunto de **Validación** (o mediante "
        "Cross-Validation) y seleccionando el mejor candidato para el "
        "ensemble definitivo."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train ensemble candidate models (Issue #049)."
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for artifacts."
    )
    parser.add_argument(
        "--output", default=DEFAULT_REPORT, help="Output markdown report path."
    )
    args = parser.parse_args()

    print("Entrenamiento de modelos candidatos para ensemble (Issue #049)")
    results = train_all(output_dir=args.output_dir)

    text = build_report(results)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(text)

    print(f"\nInforme: {args.output}")
    print("\nMétricas de entrenamiento:")
    for key in ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]:
        m = results["models"][key]["train_metrics"]
        print(f"  {results['models'][key]['name']}: "
              f"Acc={m['accuracy']:.4f} Recall={m['recall']:.4f} "
              f"F1={m['f1']:.4f} AUC={m['auc_roc']:.4f}")


if __name__ == "__main__":
    main()