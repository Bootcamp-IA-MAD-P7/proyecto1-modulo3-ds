"""Validation tests for the Logistic Regression baseline training (Issue #017).

These tests use the standard library ``unittest`` (no pytest). They verify the
training flow implemented in ``scripts/train_baseline.py``:

* dataset loading and expected columns,
* a reproducible, stratified train/test split,
* a single pipeline containing preprocessing + LogisticRegression (target not a
  feature),
* the model trains and predicts binary outputs of the expected size,
* artifacts are persisted and the pipeline can be reloaded and re-used,
* no explicit balancing (``class_weight`` is not ``"balanced"``, no SMOTE /
  oversampling / undersampling),
* the raw dataset is not modified.
"""

import json
import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import train_baseline as tb  # noqa: E402
from preprocessing import ALL_FEATURE_COLUMNS, RAW_DATA_PATH, TARGET_COLUMN  # noqa: E402


def _raw_snapshot() -> bytes:
    with open(RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class DatasetTests(unittest.TestCase):
    def test_raw_file_exists(self):
        self.assertTrue(os.path.exists(RAW_DATA_PATH))

    def test_dataset_loads_and_has_expected_columns(self):
        df = pd.read_csv(RAW_DATA_PATH)
        for col in ALL_FEATURE_COLUMNS + [TARGET_COLUMN]:
            self.assertIn(col, df.columns)

    def test_load_dataset_succeeds(self):
        df = tb.load_dataset()
        expected = set(ALL_FEATURE_COLUMNS + [TARGET_COLUMN])
        self.assertTrue(expected.issubset(set(df.columns)))
        self.assertGreaterEqual(len(df.columns), len(expected))

    def test_missing_dataset_raises(self):
        with self.assertRaises(FileNotFoundError):
            tb.load_dataset("no_such_file.csv")


class PipelineTests(unittest.TestCase):
    def test_pipeline_contains_preprocess_and_model(self):
        pipe = tb.build_baseline_pipeline()
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)
        model = pipe.named_steps["model"]
        self.assertEqual(model.__class__.__name__, "LogisticRegression")

    def test_pipeline_is_single_sklearn_pipeline(self):
        from sklearn.pipeline import Pipeline as SkPipe

        self.assertIsInstance(tb.build_baseline_pipeline(), SkPipe)

    def test_target_not_a_feature(self):
        df = tb.load_dataset()
        X = df[ALL_FEATURE_COLUMNS]
        self.assertNotIn(TARGET_COLUMN, X.columns)


class BalancelessConfigTests(unittest.TestCase):
    def test_no_explicit_balancing(self):
        pipe = tb.build_baseline_pipeline()
        model = pipe.named_steps["model"]
        self.assertIsNone(model.get_params().get("class_weight"))
        # No balancing transformers/samplers in the pipeline.
        for step_name in pipe.named_steps:
            cls_name = pipe.named_steps[step_name].__class__.__name__
            self.assertNotIn("SMOTE", cls_name)
            self.assertNotIn("RandomOverSampler", cls_name)
            self.assertNotIn("RandomUnderSampler", cls_name)


class TrainingTests(unittest.TestCase):
    def test_training_and_prediction(self):
        df = tb.load_dataset()
        X = df[ALL_FEATURE_COLUMNS]
        y = df[TARGET_COLUMN]

        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=tb.DEFAULT_TEST_SIZE,
            random_state=tb.DEFAULT_RANDOM_STATE,
            stratify=y,
        )

        self.assertGreater(len(X_train), 0)
        self.assertGreater(len(X_test), 0)
        # Both classes present.
        self.assertEqual(set(y_train.unique()), {0, 1})
        self.assertEqual(set(y_test.unique()), {0, 1})
        # Stratification approx. preserves target proportion.
        train_ratio = (y_train == 1).mean()
        test_ratio = (y_test == 1).mean()
        self.assertAlmostEqual(train_ratio, test_ratio, delta=0.02)

        pipe = tb.build_baseline_pipeline()
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        self.assertEqual(len(preds), len(y_test))
        self.assertTrue(set(np.unique(preds)).issubset({0, 1}))

    def test_metadata_written_with_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = tb.train_baseline(output_dir=tmpdir)
            with open(meta["metadata_path"], encoding="utf-8") as fh:
                data = json.load(fh)
            for key in [
                "model_name",
                "model_type",
                "target",
                "dataset_path",
                "train_rows",
                "test_rows",
                "test_size",
                "random_state",
                "stratify",
                "preprocessing_reference",
                "logistic_regression_parameters",
                "features_before_preprocessing",
                "number_of_transformed_features",
                "python_version",
                "sklearn_version",
            ]:
                self.assertIn(key, data)

    def test_artifacts_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = tb.train_baseline(output_dir=tmpdir)
            self.assertTrue(os.path.exists(meta["model_path"]))
            pipe = joblib.load(meta["model_path"])
            self.assertIn("preprocess", pipe.named_steps)
            self.assertIn("model", pipe.named_steps)
            # Loaded pipeline can predict on raw data.
            df = pd.read_csv(RAW_DATA_PATH).head(10)
            preds = pipe.predict(df[ALL_FEATURE_COLUMNS])
            self.assertEqual(len(preds), 10)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_training(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            tb.train_baseline(output_dir=tmpdir)
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
