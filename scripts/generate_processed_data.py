"""Generate the processed (transformed) train/test datasets for F5 RiskAI.

This script validates and documents a reproducible flow that produces
transformed data WITHOUT introducing data leakage. It reuses the preprocessing
pipeline built in :mod:`preprocessing` (Issue #008); it does not duplicate any
transformation logic.

Conceptual flow::

    Raw Dataset
        |
        v
    Train / Test Split   (stratified on ``stroke``, fixed random_state)
        |
        +---> Train --> Pipeline.fit(Train) ................. fit only on Train
        |                 |                                   |
        |                 +--> Pipeline.transform(Train)  --> X_train
        |
        +--> Test  --> Pipeline.transform(Test) (using the fitted pipeline)
                              |
                              v
                          X_test

The preprocessing pipeline is intentionally fitted on the TRAIN split only, so
that no information from the test set leaks into the transformation statistics
(means/standard deviations of ``StandardScaler`` and the categories learned by
``OneHotEncoder``).

.. note::

    Artifacts generated:

    * ``data/processed/X_train.csv``
    * ``data/processed/y_train.csv``
    * ``data/processed/X_test.csv``
    * ``data/processed/y_test.csv``
    * ``data/processed/feature_names.json``
    * ``data/processed/split_description.json``

    How they were obtained:
        ``X_train``/``X_test`` are the pipeline transformed features. The
        pipeline was fitted ONLY on ``X_train`` (raw training features before
        transformation). ``y_train``/``y_test`` are the separated ``stroke``
        targets.

    What they may be used for:
        Feeding a future supervised model: ``X_train``/``y_train`` train the
        model, ``X_test``/``y_test`` evaluate it.

    What they must NOT be used for:
        ``X_test`` must never be used to fit or tune the model. Neither
        ``X_train`` nor ``X_test`` may be merged back into a single file and
        refit on the whole; doing so would reintroduce data leakage.
"""

from __future__ import annotations

import argparse
import json
import os

import pandas as pd
from sklearn.model_selection import train_test_split

from preprocessing import (
    ALL_FEATURE_COLUMNS,
    RAW_DATA_PATH,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    get_transformed_feature_names,
)

# Output paths (relative to the repository root).
PROCESSED_DIR = os.path.join("data", "processed")
X_TRAIN_PATH = os.path.join(PROCESSED_DIR, "X_train.csv")
Y_TRAIN_PATH = os.path.join(PROCESSED_DIR, "y_train.csv")
X_TEST_PATH = os.path.join(PROCESSED_DIR, "X_test.csv")
Y_TEST_PATH = os.path.join(PROCESSED_DIR, "y_test.csv")
FEATURE_NAMES_PATH = os.path.join(PROCESSED_DIR, "feature_names.json")
SPLIT_DESCRIPTION_PATH = os.path.join(PROCESSED_DIR, "split_description.json")

DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42


def generate_processed_data(
    input_path: str = RAW_DATA_PATH,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    output_dir: str = PROCESSED_DIR,
) -> dict:
    """Run the full train/test transformation flow and save the artifacts.

    Returns a summary dict describing the flow, shapes and class proportions.
    """
    df = pd.read_csv(input_path)

    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Reproducible, stratified split (stratify preserved because stroke is
    # heavily imbalanced ~5%).
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    # Fit the pipeline ONLY on the raw training features, then transform both.
    pipeline = build_preprocessing_pipeline()
    pipeline.fit(X_train_raw)

    X_train = pipeline.transform(X_train_raw)
    X_test = pipeline.transform(X_test_raw)

    feature_names = get_transformed_feature_names(pipeline)
    X_train = pd.DataFrame(X_train, columns=feature_names)
    X_test = pd.DataFrame(X_test, columns=feature_names)

    os.makedirs(output_dir, exist_ok=True)
    X_train.to_csv(os.path.join(output_dir, "X_train.csv"), index=False)
    y_train.to_csv(os.path.join(output_dir, "y_train.csv"), index=False)
    X_test.to_csv(os.path.join(output_dir, "X_test.csv"), index=False)
    y_test.to_csv(os.path.join(output_dir, "y_test.csv"), index=False)

    with open(os.path.join(output_dir, "feature_names.json"), "w", encoding="utf-8") as fh:
        json.dump(feature_names, fh, indent=2)

    description = {
        "n_rows": len(df),
        "test_size": test_size,
        "random_state": random_state,
        "stratified": True,
        "split_column": TARGET_COLUMN,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "n_features_transformed": int(X_train.shape[1]),
        "train_stroke_positive": int((y_train == 1).sum()),
        "train_stroke_negative": int((y_train == 0).sum()),
        "test_stroke_positive": int((y_test == 1).sum()),
        "test_stroke_negative": int((y_test == 0).sum()),
        "pipeline_fitted_on": "X_train_raw (training split only)",
        "feature_names": feature_names,
        "warning": (
            "X_test must not be used to fit or tune the model. Do not merge "
            "X_train/X_test and refit on the whole set; that reintroduces data "
            "leakage."
        ),
    }

    with open(os.path.join(output_dir, "split_description.json"), "w", encoding="utf-8") as fh:
        json.dump(description, fh, indent=2, ensure_ascii=False)

    return {
        "n_train": description["n_train"],
        "n_test": description["n_test"],
        "n_features": description["n_features_transformed"],
        "train_stroke_positive": description["train_stroke_positive"],
        "train_stroke_negative": description["train_stroke_negative"],
        "test_stroke_positive": description["test_stroke_positive"],
        "test_stroke_negative": description["test_stroke_negative"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate transformed train/test datasets without data leakage."
    )
    parser.add_argument("--input", default=RAW_DATA_PATH, help="Raw CSV input path.")
    parser.add_argument(
        "--test-size", type=float, default=DEFAULT_TEST_SIZE, help="Fraction for the test split."
    )
    parser.add_argument(
        "--random-state", type=int, default=DEFAULT_RANDOM_STATE, help="Random seed for the split."
    )
    parser.add_argument(
        "--output-dir", default=PROCESSED_DIR, help="Directory where artifacts are saved."
    )
    args = parser.parse_args()

    summary = generate_processed_data(
        input_path=args.input,
        test_size=args.test_size,
        random_state=args.random_state,
        output_dir=args.output_dir,
    )
    print(f"Train rows: {summary['n_train']} (positive={summary['train_stroke_positive']})")
    print(f"Test rows:  {summary['n_test']} (positive={summary['test_stroke_positive']})")
    print(f"Features:   {summary['n_features']}")
    print("Artefactos guardados en:", args.output_dir)


if __name__ == "__main__":
    main()
