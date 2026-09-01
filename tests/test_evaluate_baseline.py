"""Validation tests for the baseline evaluation (Issue #018).

These tests use the standard library ``unittest`` (no pytest). They verify the
evaluation flow implemented in ``scripts/evaluate_baseline.py``:

* model artifact exists and the Pipeline loads,
* the dataset loads and the split reproduces the expected sizes,
* both classes are present in Train and Test,
* ``predict()`` and ``predict_proba()`` produce outputs of the expected size,
* every metric is bounded in [0, 1],
* the report is generated,
* the raw dataset is not modified.
"""

import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import evaluate_baseline as ev  # noqa: E402
from preprocessing import ALL_FEATURE_COLUMNS, RAW_DATA_PATH, TARGET_COLUMN  # noqa: E402

MODEL_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")


def _raw_snapshot() -> bytes:
    with open(RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class ModelArtifactTests(unittest.TestCase):
    def test_artifact_exists(self):
        self.assertTrue(os.path.exists(MODEL_ARTIFACT))

    def test_pipeline_loads(self):
        pipe = ev.load_model()
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)


class DatasetAndSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = ev.make_split(cls.df)

    def test_dataset_loads(self):
        expected = set(ALL_FEATURE_COLUMNS + [TARGET_COLUMN])
        self.assertTrue(expected.issubset(set(self.df.columns)))

    def test_split_sizes(self):
        n = len(self.df)
        # Train + Test must partition the whole dataset.
        self.assertEqual(len(self.X_train) + len(self.X_test), n)
        self.assertEqual(len(self.y_train) + len(self.y_test), n)
        # Reproducible sizes for this dataset/seed (matches #017 training).
        self.assertEqual(len(self.X_train), 3984)
        self.assertEqual(len(self.X_test), 997)

    def test_both_classes_present_in_train_and_test(self):
        self.assertEqual(set(self.y_train.unique()), {0, 1})
        self.assertEqual(set(self.y_test.unique()), {0, 1})


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = ev.make_split(cls.df)
        cls.pipe = ev.load_model()

    def test_predict_outputs(self):
        pred_train = self.pipe.predict(self.X_train)
        pred_test = self.pipe.predict(self.X_test)
        self.assertEqual(len(pred_train), len(self.y_train))
        self.assertEqual(len(pred_test), len(self.y_test))
        self.assertTrue(set(np.unique(pred_train)).issubset({0, 1}))
        self.assertTrue(set(np.unique(pred_test)).issubset({0, 1}))

    def test_predict_proba_outputs(self):
        proba_train = self.pipe.predict_proba(self.X_train)[:, 1]
        proba_test = self.pipe.predict_proba(self.X_test)[:, 1]
        self.assertEqual(len(proba_train), len(self.y_train))
        self.assertEqual(len(proba_test), len(self.y_test))
        self.assertTrue(np.all((proba_train >= 0) & (proba_train <= 1)))
        self.assertTrue(np.all((proba_test >= 0) & (proba_test <= 1)))


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = ev.make_split(cls.df)
        cls.pipe = ev.load_model()
        cls.train_metrics = ev.compute_metrics(
            cls.y_train,
            cls.pipe.predict(cls.X_train),
            cls.pipe.predict_proba(cls.X_train)[:, 1],
        )
        cls.test_metrics = ev.compute_metrics(
            cls.y_test,
            cls.pipe.predict(cls.X_test),
            cls.pipe.predict_proba(cls.X_test)[:, 1],
        )

    def _assert_metrics_bounded(self, metrics):
        for key in ["accuracy", "precision", "recall", "f1", "auc_roc"]:
            self.assertGreaterEqual(metrics[key], 0.0)
            self.assertLessEqual(metrics[key], 1.0)

    def test_train_metrics_bounded(self):
        self._assert_metrics_bounded(self.train_metrics)

    def test_test_metrics_bounded(self):
        self._assert_metrics_bounded(self.test_metrics)


class ReportTests(unittest.TestCase):
    def test_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "baseline-evaluation.md")
            result = ev.evaluate_baseline(report_path=out)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Modelo evaluado",
                "## 3. Dataset y split",
                "## 4. Métricas Train",
                "## 5. Métricas Test",
                "## 6. Classification report",
                "## 7. Comparación Train vs Test",
                "## 8. Observaciones",
            ]:
                self.assertIn(heading, text)
            self.assertIn("train", result)
            self.assertIn("test", result)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_evaluation(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            ev.evaluate_baseline(report_path=os.path.join(tmpdir, "report.md"))
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
