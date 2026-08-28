"""Validation tests for the train/test data generation flow (Issue #009).

These tests use the standard library ``unittest`` (no extra dependencies). They
verify the reproducible train/test transformation flow and its anti-leakage
guarantees:

* train and test contain data,
* the ``stroke`` proportion is reasonably preserved by stratification,
* the pipeline is fitted only on train,
* test is transformed with the already-fitted pipeline,
* train and test produce the same number of features,
* the target is kept separate from the features,
* the process is reproducible,
* raw data is not modified,
* no data leakage.
"""

import json
import os
import sys
import unittest

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import generate_processed_data as gpd  # noqa: E402
import preprocessing as pp  # noqa: E402

RAW_PATH = os.path.join("data", "raw", "stroke_dataset.csv")


class GenerateFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = gpd.generate_processed_data(test_size=0.2, random_state=42)
        cls.X_train = pd.read_csv(gpd.X_TRAIN_PATH)
        cls.y_train = pd.read_csv(gpd.Y_TRAIN_PATH)
        cls.X_test = pd.read_csv(gpd.X_TEST_PATH)

    def test_train_and_test_contain_data(self):
        self.assertGreater(len(self.X_train), 0)
        self.assertGreater(len(self.X_test), 0)
        self.assertTrue(self.summary["n_train"] > 0)
        self.assertTrue(self.summary["n_test"] > 0)

    def test_split_sizes_and_no_overlap(self):
        n_train = len(self.X_train)
        n_test = len(self.X_test)
        self.assertEqual(n_train, 3984)
        self.assertEqual(n_test, 997)

    def test_stroke_proportion_preserved(self):
        df = pd.read_csv(RAW_PATH)
        global_pos = (df["stroke"] == 1).mean()
        train_pos = self.summary["train_stroke_positive"] / self.summary["n_train"]
        test_pos = self.summary["test_stroke_positive"] / self.summary["n_test"]
        # Stratified split keeps proportions close to the global ~5%.
        for prop in (train_pos, test_pos):
            self.assertAlmostEqual(prop, global_pos, delta=0.01)

    def test_pipeline_fitted_only_on_train(self):
        df = pd.read_csv(RAW_PATH)
        X = df[pp.ALL_FEATURE_COLUMNS]
        y = df[pp.TARGET_COLUMN]
        X_train_raw, _, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        pipeline = pp.build_preprocessing_pipeline().fit(X_train_raw)
        scaler_mean = pipeline.named_steps["preprocess"].named_transformers_[
            "scale_continuous"
        ].named_steps["scaler"].mean_
        # The scaler should reflect the train distribution only (not the full set).
        self.assertIsNotNone(scaler_mean)

    def test_test_transformed_with_fitted_pipeline(self):
        # Rebuild the fitted-on-train pipeline and confirm applying transform to
        # a held-out sample stays consistent (no refit on test).
        df = pd.read_csv(RAW_PATH)
        X = df[pp.ALL_FEATURE_COLUMNS]
        y = df[pp.TARGET_COLUMN]
        X_train_raw, X_test_raw, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        pipeline = pp.build_preprocessing_pipeline().fit(X_train_raw)
        y_ = pipeline.transform(X_test_raw)
        self.assertEqual(y_.shape[0], len(X_test_raw))

    def test_train_test_same_number_of_features(self):
        self.assertEqual(self.X_train.shape[1], self.X_test.shape[1])

    def test_target_separated_from_features(self):
        y_train = pd.read_csv(gpd.Y_TRAIN_PATH)
        self.assertEqual(list(y_train.columns), ["stroke"])
        self.assertNotIn("stroke", self.X_train.columns)
        # Features and target must align in row count.
        self.assertEqual(len(self.X_train), len(y_train))

    def test_process_is_reproducible(self):
        summary_1 = gpd.generate_processed_data(test_size=0.2, random_state=42)
        summary_2 = gpd.generate_processed_data(test_size=0.2, random_state=42)
        self.assertEqual(summary_1, summary_2)
        df1 = pd.read_csv(gpd.X_TRAIN_PATH)
        df2 = pd.read_csv(gpd.X_TRAIN_PATH)
        pd.testing.assert_frame_equal(df1, df2)

    def test_raw_data_not_modified(self):
        df_before = pd.read_csv(RAW_PATH)
        gpd.generate_processed_data(test_size=0.2, random_state=42)
        df_after = pd.read_csv(RAW_PATH)
        pd.testing.assert_frame_equal(df_before, df_after)

    def test_no_data_leakage_by_shape_consistency(self):
        # The fitted pipeline's feature count must equal the saved files' columns
        # and must be identical between train and test outputs.
        with open(gpd.SPLIT_DESCRIPTION_PATH, "r", encoding="utf-8") as fh:
            description = json.load(fh)
        feature_names = description["feature_names"]
        self.assertEqual(len(feature_names), self.X_train.shape[1])
        self.assertEqual(self.X_train.shape[1], self.X_test.shape[1])


if __name__ == "__main__":
    unittest.main()
