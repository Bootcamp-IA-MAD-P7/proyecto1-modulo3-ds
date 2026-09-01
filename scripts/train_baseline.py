"""Train the Logistic Regression baseline for F5 RiskAI (Issue #017).

This script implements, exactly, the baseline specification defined in
``docs/ml-baseline-specification.md`` (#016). It trains a reproducible
:class:`sklearn.linear_model.LogisticRegression` baseline and saves the complete
pipeline (preprocessing + model) as a ``joblib`` artifact plus a metadata JSON.

The pipeline is a single :class:`sklearn.pipeline.Pipeline` containing the
existing preprocessing (:mod:`preprocessing`, Issue #008) and the model, so the
saved artifact can later receive raw data directly.

Flow (no data leakage)::

    Raw Dataset
        v
    X = features, y = stroke
        v
    train_test_split(test_size=0.2, random_state=42, stratify=y)
        |
        +--> Train --> pipeline.fit(X_train_raw, y_train)  (fit only on Train)
        |
        +--> Test  --> reserved for later evaluation (no fit)

The test split is NOT used during any ``fit`` step. No balancing technique is
applied (baseline without class_weight/SMOTE/oversampling/undersampling).

Run from the repository root::

    python scripts/train_baseline.py [--output-dir artifacts]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from preprocessing import (
    ALL_FEATURE_COLUMNS,
    RAW_DATA_PATH,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    get_transformed_feature_names,
)

DEFAULT_OUTPUT_DIR = os.path.join("artifacts")
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42

MODEL_FILENAME = "logistic_regression_baseline.joblib"
METADATA_FILENAME = "logistic_regression_baseline_metadata.json"


def load_dataset(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load and validate the raw dataset, raising clear errors."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No existe el dataset en '{path}'. Verifica la ruta o ejecuta desde la raíz del repo."
        )
    df = pd.read_csv(path)
    expected_columns = ALL_FEATURE_COLUMNS + [TARGET_COLUMN]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas esperadas en '{path}': {missing}. "
            f"Columnas presentes: {list(df.columns)}."
        )
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Falta la variable objetivo '{TARGET_COLUMN}'.")
    return df


def build_baseline_pipeline() -> Pipeline:
    """Return a single Pipeline: preprocessing + LogisticRegression."""
    preprocessing_pipeline = build_preprocessing_pipeline()
    model = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=100,
        random_state=DEFAULT_RANDOM_STATE,
        class_weight=None,
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessing_pipeline),
            ("model", model),
        ]
    )


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def train_baseline(
    input_path: str = RAW_DATA_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> dict:
    """Run the full baseline training flow and save the artifacts.

    Returns a metadata dict describing the run.
    """
    df = load_dataset(input_path)

    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Reproducible, stratified split BEFORE any preprocessing fit.
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X,
        y,
        test_size=DEFAULT_TEST_SIZE,
        random_state=DEFAULT_RANDOM_STATE,
        stratify=y,
    )

    pipeline = build_baseline_pipeline()
    # Fit only on Train (preprocessing + model). Test is never used in fit.
    pipeline.fit(X_train_raw, y_train)

    # Number of transformed features (post-preprocessing), for metadata.
    transformed = pipeline.named_steps["preprocess"].transform(X_train_raw)
    n_transformed = int(np.asarray(transformed).shape[1])
    feature_names = get_transformed_feature_names(pipeline.named_steps["preprocess"])

    # Prediction sanity check using the trained model on Train (not evaluation).
    pred_train = pipeline.predict(X_train_raw)
    if len(pred_train) != len(y_train):
        raise RuntimeError("Las predicciones de entrenamiento no tienen el tamaño esperado.")

    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, MODEL_FILENAME)
    metadata_path = os.path.join(output_dir, METADATA_FILENAME)

    joblib.dump(pipeline, model_path)

    model_params = pipeline.named_steps["model"].get_params()
    logreg_params = {k: v for k, v in model_params.items() if not k.startswith("_")}

    metadata = {
        "model_name": "logistic_regression_baseline",
        "model_type": "LogisticRegression",
        "target": TARGET_COLUMN,
        "dataset_path": input_path,
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "test_size": DEFAULT_TEST_SIZE,
        "random_state": DEFAULT_RANDOM_STATE,
        "stratify": True,
        "preprocessing_reference": "scripts/preprocessing.py::build_preprocessing_pipeline (Issue #008)",
        "logistic_regression_parameters": logreg_params,
        "features_before_preprocessing": ALL_FEATURE_COLUMNS,
        "number_of_transformed_features": n_transformed,
        "transformed_feature_names": feature_names,
        "python_version": platform.python_version(),
        "sklearn_version": _sklearn_version(),
        "timestamp": _iso_timestamp(),
    }

    with open(metadata_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False, default=str)

    return {
        "model_path": model_path,
        "metadata_path": metadata_path,
        "train_rows": metadata["train_rows"],
        "test_rows": metadata["test_rows"],
        "n_transformed": n_transformed,
        "train_stroke_positive": int((y_train == 1).sum()),
        "test_stroke_positive": int((y_test == 1).sum()),
        "logreg_params": logreg_params,
    }


def _sklearn_version() -> str:
    import sklearn

    return sklearn.__version__


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Logistic Regression baseline.")
    parser.add_argument("--input", default=RAW_DATA_PATH, help="Raw CSV input path.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Artifacts directory.")
    args = parser.parse_args()

    metadata = train_baseline(input_path=args.input, output_dir=args.output_dir)

    print("Entrenamiento del baseline completado")
    print(f"  Artefacto modelo:  {metadata['model_path']}")
    print(f"  Metadata:          {metadata['metadata_path']}")
    print(f"  Train rows:        {metadata['train_rows']} (stroke=1: {metadata['train_stroke_positive']})")
    print(f"  Test rows:         {metadata['test_rows']} (stroke=1: {metadata['test_stroke_positive']})")
    print(f"  Features post-preproc: {metadata['n_transformed']}")
    print("  Baseline sin técnica de balanceo.")


if __name__ == "__main__":
    main()
