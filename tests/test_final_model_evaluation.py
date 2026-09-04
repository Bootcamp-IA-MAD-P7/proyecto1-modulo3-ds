"""Validation tests for the final model evaluation (Issue #052).

These tests use the standard library ``unittest`` (no pytest). They verify the
final evaluation flow implemented in ``scripts/evaluate_final_model.py``:

* the optimized artifact exists and can be loaded,
* the Test set contains exactly 997 records,
* the Test set is not used to train,
* the expected metrics are generated,
* metrics are numeric and within ``[0, 1]``,
* the confusion matrix has binary (2x2) structure,
* the report is generated correctly,
* ``data/raw`` is not modified,
* the baseline and tuned artifacts are not modified,
* results are reproducible (``random_state=42``).
"""

import hashlib
import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import evaluate_baseline as ev  # noqa: E402
import evaluate_final_model as efm  # noqa: E402
from imblearn.over_sampling import RandomOverSampler  # noqa: E402

TUNED_ARTIFACT = efm.DEFAULT_MODEL_PATH
BASELINE_ARTIFACT = efm.BASELINE_ARTIFACT

# Cache the (expensive) CV reference computation across test classes.
_CV_CACHE = {}


def _cv_ref():
    if "cv" not in _CV_CACHE:
        df = ev.load_dataset()
        _CV_CACHE["cv"] = efm.cv_reference(df)
    return _CV_CACHE["cv"]


def _raw_hash() -> str:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _artifact_hash(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class ArtifactTests(unittest.TestCase):
    def test_tuned_artifact_exists(self):
        self.assertTrue(os.path.exists(TUNED_ARTIFACT))

    def test_tuned_artifact_loadable(self):
        pipe = efm.load_model(TUNED_ARTIFACT)
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("sampler", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)
        self.assertIsInstance(pipe.named_steps["sampler"], RandomOverSampler)
        self.assertIsInstance(pipe.named_steps["model"], LogisticRegression)

    def test_artifacts_not_modified(self):
        self.assertTrue(os.path.exists(BASELINE_ARTIFACT))
        self.assertTrue(os.path.exists(TUNED_ARTIFACT))


class SplitTests(unittest.TestCase):
    def test_test_set_has_exactly_997_records(self):
        df = ev.load_dataset()
        _, X_test, _, y_test = ev.make_split(df)
        self.assertEqual(len(X_test), 997)
        self.assertEqual(len(y_test), 997)

    def test_test_set_not_used_for_training(self):
        # The final evaluation only loads the pre-trained artifact and predicts;
        # verify that the pipeline is not refit on the test data.
        df = ev.load_dataset()
        pipe = efm.load_model(TUNED_ARTIFACT)
        before_coef = np.array(pipe.named_steps["model"].coef_).copy()
        efm.evaluate_on_test(df, pipe)
        after_coef = np.array(pipe.named_steps["model"].coef_)
        np.testing.assert_array_equal(before_coef, after_coef)


class MetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        df = ev.load_dataset()
        cls.pipe = efm.load_model(TUNED_ARTIFACT)
        cls.result = efm.evaluate_on_test(df, cls.pipe)
        cls.metrics = cls.result["metrics"]
        cls.cm = cls.result["confusion_matrix"]

    def test_expected_metrics_present(self):
        for key in ["accuracy", "precision", "recall", "f1", "f1_macro", "roc_auc"]:
            self.assertIn(key, self.metrics)

    def test_metrics_are_numeric(self):
        for key, val in self.metrics.items():
            self.assertIsInstance(val, (int, float), key)

    def test_metrics_within_unit_range(self):
        for key, val in self.metrics.items():
            self.assertGreaterEqual(val, 0.0, key)
            self.assertLessEqual(val, 1.0, key)

    def test_confusion_matrix_binary_structure(self):
        self.assertEqual(self.cm.shape, (2, 2))
        # TN, FP, FN, TP all non-negative integers.
        for cell in self.cm.ravel():
            self.assertIsInstance(cell, (int, np.integer))
            self.assertGreaterEqual(cell, 0)
        # Sum of the matrix equals the Test set size.
        self.assertEqual(int(self.cm.sum()), 997)

    def test_positive_class_recall_reasonable(self):
        # Sanity: the minority-class recall should be far from 0 given ROS.
        self.assertGreater(self.metrics["recall"], 0.5)


class ReproducibilityTests(unittest.TestCase):
    def test_evaluation_reproducible(self):
        df = ev.load_dataset()
        pipe = efm.load_model(TUNED_ARTIFACT)
        r1 = efm.evaluate_on_test(df, pipe)
        r2 = efm.evaluate_on_test(df, pipe)
        for key in r1["metrics"]:
            self.assertEqual(r1["metrics"][key], r2["metrics"][key], key)
        np.testing.assert_array_equal(r1["confusion_matrix"], r2["confusion_matrix"])


class ReportTests(unittest.TestCase):
    def test_report_generates_correctly(self):
        df = ev.load_dataset()
        pipe = efm.load_model(TUNED_ARTIFACT)
        result = efm.evaluate_on_test(df, pipe)
        cv = _cv_ref()
        text = efm.build_report(
            df,
            result,
            cv,
            n_train=3984,
            n_test=997,
            model_path=TUNED_ARTIFACT,
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "repo.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        for section in [
            "# Evaluación Final del Modelo",
            "## 8. Comparación Cross-Validation vs Test",
            "## 7. Matriz de Confusión",
            "## 10. Conclusión",
        ]:
            self.assertIn(section, content)


class DataIntegrityTests(unittest.TestCase):
    def test_raw_dataset_unmodified(self):
        before = _raw_hash()
        df = ev.load_dataset()
        pipe = efm.load_model(TUNED_ARTIFACT)
        efm.evaluate_on_test(df, pipe)
        after = _raw_hash()
        self.assertEqual(before, after)
        self.assertGreater(len(before), 0)

    def test_artifacts_hash_unchanged_by_evaluation(self):
        tuned_before = _artifact_hash(TUNED_ARTIFACT)
        base_before = _artifact_hash(BASELINE_ARTIFACT)
        df = ev.load_dataset()
        pipe = efm.load_model(TUNED_ARTIFACT)
        efm.evaluate_on_test(df, pipe)
        self.assertEqual(_artifact_hash(TUNED_ARTIFACT), tuned_before)
        self.assertEqual(_artifact_hash(BASELINE_ARTIFACT), base_before)


if __name__ == "__main__":
    unittest.main()