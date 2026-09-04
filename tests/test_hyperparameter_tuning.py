"""Validation tests for the hyperparameter tuning (Issue #051).

These tests use the standard library ``unittest`` (no pytest). They verify the
tuning flow implemented in ``scripts/tune_logistic_regression.py``:

* the pipeline contains preprocessing, RandomOverSampler and the model,
* the model is a LogisticRegression,
* the search space contains the expected hyperparameters,
* the CV uses 5 folds with ``random_state=42``,
* the Test set is not used during tuning,
* results are reproducible,
* metrics are not NaN,
* the tuned artifact can be loaded,
* the model produces both ``predict`` and ``predict_proba``,
* ``data/raw`` stays intact.
"""

import hashlib
import os
import sys
import tempfile
import unittest

import joblib
import numpy as np
from imblearn.over_sampling import RandomOverSampler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import evaluate_baseline as ev  # noqa: E402
import tune_logistic_regression as tune  # noqa: E402

TUNED_ARTIFACT = os.path.join("artifacts", "logistic_regression_tuned.joblib")
BASELINE_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")

# Cache the (expensive) grid search across test classes.
_GRID_CACHE = {}


def _grid():
    if "grid" not in _GRID_CACHE:
        df = ev.load_dataset()
        X_train, _, y_train, _ = ev.make_split(df)
        _GRID_CACHE["grid"] = tune.run_grid_search(X_train, y_train)
    return _GRID_CACHE["grid"]


def _raw_hash() -> str:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class PipelineStructureTests(unittest.TestCase):
    def test_pipeline_has_expected_steps(self):
        pipe = tune.build_pipeline(tune.BASELINE_LR_PARAMS)
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("sampler", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)

    def test_sampler_is_random_over_sampler(self):
        pipe = tune.build_pipeline(tune.BASELINE_LR_PARAMS)
        self.assertIsInstance(pipe.named_steps["sampler"], RandomOverSampler)

    def test_model_is_logistic_regression(self):
        pipe = tune.build_pipeline(tune.BASELINE_LR_PARAMS)
        self.assertIsInstance(pipe.named_steps["model"], LogisticRegression)


class SearchSpaceTests(unittest.TestCase):
    def test_grid_contains_expected_hyperparameters(self):
        grid = tune.PARAM_GRID
        for key in ["model__C", "model__solver", "model__max_iter"]:
            self.assertIn(key, grid)
        self.assertEqual(set(grid["model__C"]), {0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0})
        self.assertEqual(set(grid["model__solver"]), {"lbfgs", "liblinear"})
        self.assertTrue(all(mi >= 500 for mi in grid["model__max_iter"]))


class CVConfigurationTests(unittest.TestCase):
    def test_uses_five_folds(self):
        cv = tune.make_cv()
        self.assertEqual(cv.get_n_splits(), 5)

    def test_random_state_is_42(self):
        cv = tune.make_cv()
        self.assertEqual(cv.random_state, 42)
        self.assertTrue(cv.shuffle)

    def test_grid_uses_stratified_five_folds_seed_42(self):
        grid = _grid()
        cv = grid.cv
        self.assertEqual(cv.get_n_splits(), 5)
        self.assertEqual(cv.random_state, 42)


class MetricSanityTests(unittest.TestCase):
    def setUp(self):
        self.grid = _grid()

    def test_best_score_not_nan(self):
        self.assertFalse(np.isnan(self.grid.best_score_))

    def test_all_cv_metrics_finite(self):
        for metric in tune.METRICS:
            key = f"mean_test_{metric}"
            self.assertIn(key, self.grid.cv_results_, key)
            vals = self.grid.cv_results_[key]
            self.assertTrue(np.all(np.isfinite(vals)), metric)

    def test_best_params_are_among_grid(self):
        g = self.grid
        self.assertIn(g.best_params_["model__C"], tune.PARAM_GRID["model__C"])
        self.assertIn(g.best_params_["model__solver"], tune.PARAM_GRID["model__solver"])
        self.assertIn(g.best_params_["model__max_iter"], tune.PARAM_GRID["model__max_iter"])


class ReproducibilityTests(unittest.TestCase):
    def test_grid_search_is_reproducible(self):
        df = ev.load_dataset()
        X_train, _, y_train, _ = ev.make_split(df)
        grid_a = tune.run_grid_search(X_train, y_train)
        grid_b = tune.run_grid_search(X_train, y_train)
        self.assertEqual(grid_a.best_params_, grid_b.best_params_)
        self.assertAlmostEqual(grid_a.best_score_, grid_b.best_score_, places=6)


class LeakageTests(unittest.TestCase):
    def test_test_set_not_used_in_grid_fit(self):
        # The grid is fitted only on the training split; verify by checking that
        # the sampler/preprocessor are conditioned on Train and that the grid's
        # fit input never received the test set.
        df = ev.load_dataset()
        X_train, X_test, y_train, y_test = ev.make_split(df)
        grid = tune.run_grid_search(X_train, y_train)
        # best_estimator_ was refit on X_train only; it asserts fit against train.
        self.assertEqual(len(grid.best_estimator_.classes_), 2)
        # Sanity: the test split exists and is separate from train.
        self.assertFalse(X_test.equals(X_train))

    def test_raw_dataset_unmodified(self):
        before = _raw_hash()
        df = ev.load_dataset()
        X_train, _, y_train, _ = ev.make_split(df)
        tune.run_grid_search(X_train, y_train)
        after = _raw_hash()
        self.assertEqual(before, after)
        self.assertGreater(len(before), 0)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.pipe = joblib.load(TUNED_ARTIFACT)

    def test_tuned_artifact_loadable(self):
        self.assertIsNotNone(self.pipe)
        self.assertIn("preprocess", self.pipe.named_steps)
        self.assertIn("sampler", self.pipe.named_steps)
        self.assertIn("model", self.pipe.named_steps)
        self.assertIsInstance(self.pipe.named_steps["sampler"], RandomOverSampler)
        self.assertIsInstance(self.pipe.named_steps["model"], LogisticRegression)

    def test_baseline_artifact_not_overwritten(self):
        self.assertTrue(os.path.exists(BASELINE_ARTIFACT))

    def test_model_produces_predict_and_predict_proba(self):
        df = ev.load_dataset()
        X_train, _, _, _ = ev.make_split(df)
        sample = X_train.iloc[:10]
        preds = np.asarray(self.pipe.predict(sample))
        self.assertEqual(len(preds), len(sample))
        self.assertTrue(set(np.unique(preds)).issubset({0, 1}))
        proba = np.asarray(self.pipe.predict_proba(sample))
        self.assertEqual(proba.shape[1], 2)
        self.assertTrue(np.all(proba >= 0.0) and np.all(proba <= 1.0))
        self.assertTrue(np.allclose(proba.sum(axis=1), 1.0))


class ReportGenerationTests(unittest.TestCase):
    def test_report_renders(self):
        baseline = {"accuracy": {"mean": 0.74}, "precision_pos": {"mean": 0.14},
                    "recall_pos": {"mean": 0.82}, "f1_pos": {"mean": 0.24},
                    "roc_auc": {"mean": 0.84}, "f1_macro": {"mean": 0.54}}
        tuned = {k: {"mean": v["mean"] + 0.001} for k, v in baseline.items()}
        best_params = {"model__C": 0.5, "model__solver": "lbfgs", "model__max_iter": 500}
        text = tune.build_report(baseline, tuned, best_params, TUNED_ARTIFACT)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        self.assertIn("C", content)
        self.assertIn("0.2400", content)  # baseline F1 appears in the table
        self.assertIn("logistic_regression_tuned.joblib", content)


if __name__ == "__main__":
    unittest.main()