"""Validation tests for the data preprocessing pipeline.

These tests use the standard library ``unittest`` so that no additional testing
dependency is required. They verify that:

* the pipeline can be built,
* feature columns are classified correctly,
* categorical variables are one-hot encoded,
* numerical variables are processed correctly,
* transformed feature names can be recovered (including the presence of the
  binary and continuous columns, which must never silently disappear),
* the pipeline is reusable,
* preprocessing functions do not modify the DataFrame they receive as input.
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import preprocessing as pp  # noqa: E402

RAW_PATH = os.path.join("data", "raw", "stroke_dataset.csv")

# Columns that must always be present in the transformed features.
EXPECTED_BINARY_FEATURES = ("hypertension", "heart_disease")
EXPECTED_CONTINUOUS_FEATURES = ("age", "avg_glucose_level", "bmi")
EXPECTED_CATEGORICAL_FEATURES = (
    "gender",
    "ever_married",
    "work_type",
    "Residence_type",
    "smoking_status",
)


class BuildPipelineTests(unittest.TestCase):
    def test_pipeline_builds(self):
        pipeline = pp.build_preprocessing_pipeline()
        self.assertIsNotNone(pipeline)
        self.assertIn("preprocess", pipeline.named_steps)

    def test_feature_lists_complete(self):
        all_cols = set(pp.ALL_FEATURE_COLUMNS)
        expected = set(
            EXPECTED_BINARY_FEATURES
            + EXPECTED_CONTINUOUS_FEATURES
            + EXPECTED_CATEGORICAL_FEATURES
        )
        self.assertEqual(all_cols, expected)
        self.assertNotIn(pp.TARGET_COLUMN, all_cols)


class FitPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        df = pd.read_csv(RAW_PATH)
        cls.X = df[pp.ALL_FEATURE_COLUMNS]
        cls.y = df[pp.TARGET_COLUMN]
        cls.pipeline = pp.build_preprocessing_pipeline().fit(cls.X)
        cls.feature_names = pp.get_transformed_feature_names(cls.pipeline)
        cls.transformed = cls.pipeline.transform(cls.X)

    def test_feature_names_are_recovered(self):
        self.assertGreater(len(self.feature_names), 0)

    def test_binary_features_exist(self):
        for column in EXPECTED_BINARY_FEATURES:
            self.assertIn(column, self.feature_names)

    def test_continuous_features_exist(self):
        for column in EXPECTED_CONTINUOUS_FEATURES:
            self.assertIn(column, self.feature_names)

    def test_categorical_features_generate_encoded_features(self):
        for column in EXPECTED_CATEGORICAL_FEATURES:
            encoded = [name for name in self.feature_names if name.startswith(f"{column}_")]
            self.assertGreater(
                len(encoded), 0, msg=f"Expected one-hot features for {column!r}"
            )

    def test_binary_numeric_passthrough(self):
        for column in EXPECTED_BINARY_FEATURES:
            idx = self.feature_names.index(column)
            self.assertLess(idx, self.transformed.shape[1])
            vals = set(np.asarray(self.transformed[:, idx]).tolist())
            self.assertTrue(
                vals.issubset({0.0, 1.0}),
                msg=f"{column!r} should be a 0/1 passthrough, got {vals}",
            )

    def test_continuous_are_scaled(self):
        for column in EXPECTED_CONTINUOUS_FEATURES:
            idx = self.feature_names.index(column)
            std = np.nanstd(np.asarray(self.transformed[:, idx]))
            self.assertAlmostEqual(
                std, 1.0, places=5, msg=f"{column!r} should be standardized"
            )

    def test_row_count_preserved(self):
        self.assertEqual(self.transformed.shape[0], len(self.X))

    def test_pipeline_is_reusable_on_new_data(self):
        sample = self.X.iloc[:5]
        out1 = self.pipeline.transform(sample)
        out2 = self.pipeline.transform(sample)
        np.testing.assert_array_equal(out1, out2)


class NoMutationTests(unittest.TestCase):
    def setUp(self):
        df = pd.read_csv(RAW_PATH)
        self.X = df[pp.ALL_FEATURE_COLUMNS]
        self.X_copy = self.X.copy(deep=True)

    def test_transform_does_not_mutate_input_dataframe(self):
        pipeline = pp.build_preprocessing_pipeline().fit(self.X)
        pipeline.transform(self.X)
        pd.testing.assert_frame_equal(self.X, self.X_copy)


if __name__ == "__main__":
    unittest.main()
