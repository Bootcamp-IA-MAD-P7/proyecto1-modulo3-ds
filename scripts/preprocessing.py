"""Reusable data preprocessing pipeline for F5 RiskAI.

This module provides the preprocessing pipeline factory reused across the
project. It does NOT train any model, does not modify the raw data, and does
not apply oversampling/undersampling or SMOTE.

Pipeline steps for the feature matrix (target ``stroke`` is excluded):

* Continuous numeric features (``age``, ``avg_glucose_level``, ``bmi``)
  are standardised with :class:`~sklearn.preprocessing.StandardScaler`.
* Binary numeric features (``hypertension``, ``heart_disease``) are passed
  through unchanged (they are already 0/1 indicators, scaling adds no value).
* Categorical features are one-hot encoded with
  :class:`~sklearn.preprocessing.OneHotEncoder` configured with
  ``handle_unknown="ignore"`` so that unseen categories in future data do not
  raise errors (robust to new data, avoids leaking category knowledge from the
  fit set at prediction time).

.. warning::

    **Data leakage.** Never fit this pipeline on the whole dataset and then use
    the resulting transformed artifact to train a model. That leaks information
    from the test set into training and biases the evaluation.

    The correct flow is::

        Raw dataset
              |
              v
        Train/Test Split   (stratified, fixed random_state)
              |
              +--> Train --> Pipeline.fit(Train) ........ fit only on Train
              |               |
              |               +--> Pipeline.transform(Train) --> X_train
              |
              +--> Test --> Pipeline.transform(Test) --> X_test

    See :mod:`generate_processed_data` for the reproducible implementation of
    this flow.
"""

from __future__ import annotations

import os

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RAW_DATA_PATH = os.path.join("data", "raw", "stroke_dataset.csv")

TARGET_COLUMN = "stroke"

CONTINUOUS_FEATURES = ["age", "avg_glucose_level", "bmi"]
BINARY_FEATURES = ["hypertension", "heart_disease"]
CATEGORICAL_FEATURES = [
    "gender",
    "ever_married",
    "work_type",
    "Residence_type",
    "smoking_status",
]

ALL_FEATURE_COLUMNS = BINARY_FEATURES + CONTINUOUS_FEATURES + CATEGORICAL_FEATURES


def build_preprocessing_pipeline() -> Pipeline:
    """Return a reusable ColumnTransformer wrapped in a scikit-learn Pipeline."""
    continuous_transformer = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
        ]
    )

    column_transformer = ColumnTransformer(
        transformers=[
            ("scale_continuous", continuous_transformer, CONTINUOUS_FEATURES),
            ("binary_passthrough", "passthrough", BINARY_FEATURES),
            ("encode_categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )

    return Pipeline(steps=[("preprocess", column_transformer)])


def get_transformed_feature_names(
    pipeline: Pipeline, feature_names: list[str] | None = None
) -> list[str]:
    """Return the names of the columns produced after transformation.

    The pipeline must already be fitted so that the one-hot encoder knows its
    categories.
    """
    transformer: ColumnTransformer = pipeline.named_steps["preprocess"]
    names: list[str] = []

    for name, _, columns in transformer.transformers_:
        if name == "scale_continuous":
            names.extend(CONTINUOUS_FEATURES)
        elif name == "binary_passthrough":
            names.extend(BINARY_FEATURES)
        elif name == "encode_categorical":
            encoder: OneHotEncoder = transformer.named_transformers_[name]
            categories = encoder.categories_
            for column, cats in zip(columns, categories):
                names.extend(f"{column}_{cat}" for cat in cats)

    return names
