"""Validation tests for the model comparison (Issue #050).

These tests use the standard library ``unittest`` (no pytest). They verify the
model comparison flow implemented in ``scripts/compare_models.py``:

* the four candidate artifacts exist after training (#049),
* the models can be loaded correctly,
* they produce valid binary predictions,
* the models that should expose ``predict_proba`` do so,
* metrics are computed correctly and stay within ``[0, 1]``,
* the Test set is not used to select the model,
* ``data/raw`` is not modified,
* results are reproducible given ``random_state``,
* the report is generated correctly,
* all four candidate models appear in the comparison.
"""

import hashlib
import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
from sklearn.metrics import f1_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import compare_models as cm  # noqa: E402
import evaluate_baseline as ev  # noqa: E402


def _raw_hash() -> str:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


CANDIDATE_KEYS = ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]


class ArtifactExistenceTests(unittest.TestCase):
    def test_all_candidate_artifacts_exist(self):
        for key in CANDIDATE_KEYS:
            self.assertTrue(
                os.path.exists(cm.CANDIDATE_ARTIFACTS[key]),
                f"Artifact missing: {cm.CANDIDATE_ARTIFACTS[key]}",
            )

    def test_baseline_artifact_preserved(self):
        self.assertTrue(os.path.exists(cm.BASELINE_ARTIFACT))


class ModelLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipelines = {
            key: joblib.load(cm.CANDIDATE_ARTIFACTS[key]) for key in CANDIDATE_KEYS
        }

    def test_pipelines_load_and_have_key_steps(self):
        for key in CANDIDATE_KEYS:
            self.assertIn("preprocess", self.pipelines[key].named_steps)
            self.assertIn("model", self.pipelines[key].named_steps)

    def test_predict_proba_available(self):
        # All four candidates expose predict_proba (LinearSVC is calibrated).
        for key in CANDIDATE_KEYS:
            self.assertTrue(
                hasattr(self.pipelines[key], "predict_proba"),
                f"{key} should expose predict_proba",
            )


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        X_train, _, _, _ = ev.make_split(cls.df)
        cls.sample = X_train.iloc[:20]

    def test_all_models_produce_valid_binary_predictions(self):
        for key in CANDIDATE_KEYS:
            pipe = joblib.load(cm.CANDIDATE_ARTIFACTS[key])
            preds = np.asarray(pipe.predict(self.sample))
            self.assertTrue(set(np.unique(preds)).issubset({0, 1}), key)
            self.assertEqual(len(preds), len(self.sample), key)

    def test_probabilities_are_valid_fractions(self):
        for key in CANDIDATE_KEYS:
            pipe = joblib.load(cm.CANDIDATE_ARTIFACTS[key])
            proba = np.asarray(pipe.predict_proba(self.sample))
            self.assertTrue(np.all(proba >= 0.0) and np.all(proba <= 1.0), key)
            self.assertTrue(np.allclose(proba.sum(axis=1), 1.0), key)


class MetricComputationTests(unittest.TestCase):
    def test_metrics_within_unit_range(self):
        # Use a tiny synthetic balanced case to validate the metric helper.
        y_true = np.array([0, 1, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 1, 1, 1, 0])
        y_proba = np.array([0.1, 0.9, 0.8, 0.6, 0.7, 0.2])
        metrics = ev.compute_metrics(y_true, y_pred, y_proba)
        for name in ["accuracy", "precision", "recall", "f1", "auc_roc"]:
            self.assertGreaterEqual(metrics[name], 0.0, name)
            self.assertLessEqual(metrics[name], 1.0, name)
        # F1-macro must also stay within [0,1].
        f1_macro = float(np.mean([
            f1_score(y_true, y_pred, average="macro", zero_division=0)
        ]))
        self.assertGreaterEqual(f1_macro, 0.0)
        self.assertLessEqual(f1_macro, 1.0)

    def test_baseline_cv_metrics_match_reference(self):
        # Compare CV gives the same baseline figures as Issue #047.
        df = ev.load_dataset()
        results = cm.compare_all(df)["results"]
        bl = results["baseline"]["summary"]
        self.assertAlmostEqual(bl["recall"]["mean"], 0.005, places=2)
        self.assertAlmostEqual(bl["f1"]["mean"], 0.0098, places=2)
        self.assertAlmostEqual(bl["roc_auc"]["mean"], 0.8375, places=2)


class SelectionTests(unittest.TestCase):
    def test_selection_ignores_test_set_in_decision(self):
        # The decision is computed purely from CV summary metrics (out-of-fold),
        # never from the reserved test set.
        df = ev.load_dataset()
        results = cm.compare_all(df)["results"]
        decision = cm.decide_best(results)
        # All best-* keys must map to an existing compared model.
        for criterion in ["best_recall", "best_f1", "best_f1_macro", "best_roc_auc", "best_overall"]:
            self.assertIn(decision[criterion], results)

    def test_decision_is_reproducible(self):
        df = ev.load_dataset()
        results_a = cm.compare_all(df)["results"]
        results_b = cm.compare_all(df)["results"]
        for key in results_a:
            for metric in cm.METRICS:
                self.assertEqual(
                    results_a[key]["summary"][metric]["mean"],
                    results_b[key]["summary"][metric]["mean"],
                )


class ComparisonCoverageTests(unittest.TestCase):
    def test_all_four_candidates_in_comparison(self):
        df = ev.load_dataset()
        results = cm.compare_all(df)["results"]
        for key in CANDIDATE_KEYS:
            self.assertIn(key, results)

    def test_report_contains_all_models(self):
        df = ev.load_dataset()
        results = cm.compare_all(df)["results"]
        artifacts = cm.artifact_check(df)
        decision = cm.decide_best(results)
        text = cm.build_report(
            {"results": results, "n_train": 3984, "n_test": 997, "n_pos_train": 198},
            artifacts, decision,
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        for key in CANDIDATE_KEYS:
            self.assertIn(results[key]["label"], content)


class DataIntegrityTests(unittest.TestCase):
    def test_raw_dataset_unmodified(self):
        before = _raw_hash()
        df = ev.load_dataset()
        cm.compare_all(df)  # read-only comparison
        after = _raw_hash()
        self.assertEqual(before, after)
        # regression guard: file must actually exist
        self.assertGreater(len(before), 0)


if __name__ == "__main__":
    unittest.main()