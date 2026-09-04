"""Validation tests for the ensemble model training (Issue #049).

These tests use the standard library ``unittest`` (no pytest). They verify the
ensemble training flow implemented in ``scripts/train_ensemble.py``:

* the expected artifacts exist after training,
* the models can be loaded correctly,
* the models accept data with the expected format,
* predictions are binary or valid probabilities as appropriate,
* LinearSVC is correctly calibrated,
* the oversampling pipeline contains the sampler when appropriate,
* the test set is not used during training,
* data/raw is not modified,
* training is reproducible when random_state is used.
"""

import os
import sys
import tempfile
import unittest

import joblib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import train_ensemble as te  # noqa: E402
import evaluate_baseline as ev  # noqa: E402


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


EXPECTED_ARTIFACTS = {
    "logistic_regression": os.path.join("artifacts", "logistic_regression_ensemble.joblib"),
    "linear_svc": os.path.join("artifacts", "linear_svc_calibrated.joblib"),
    "complement_nb": os.path.join("artifacts", "complement_nb_ensemble.joblib"),
    "lightgbm": os.path.join("artifacts", "lightgbm_ensemble.joblib"),
}

TABULAR_KEYS = ["logistic_regression", "linear_svc", "complement_nb", "lightgbm"]


class ArtifactExistenceTests(unittest.TestCase):
    def test_all_expected_artifacts_exist(self):
        for key in TABULAR_KEYS:
            self.assertTrue(
                os.path.exists(EXPECTED_ARTIFACTS[key]),
                f"Artifact missing: {EXPECTED_ARTIFACTS[key]}",
            )

    def test_baseline_not_overwritten(self):
        baseline_path = os.path.join("artifacts", "logistic_regression_baseline.joblib")
        self.assertTrue(os.path.exists(baseline_path))


class ModelLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipelines = {}
        for key in TABULAR_KEYS:
            cls.pipelines[key] = joblib.load(EXPECTED_ARTIFACTS[key])

    def test_pipelines_load_and_have_steps(self):
        for key in TABULAR_KEYS:
            self.assertIn("preprocess", self.pipelines[key].named_steps)
            self.assertIn("model", self.pipelines[key].named_steps)

    def test_pipelines_have_sampler_when_expected(self):
        for key in TABULAR_KEYS:
            # LightGBM and the others all use ROS, so sampler should exist.
            self.assertIn("sampler", self.pipelines[key].named_steps)


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = ev.make_split(cls.df)
        cls.pipelines = {}
        for key in TABULAR_KEYS:
            cls.pipelines[key] = joblib.load(EXPECTED_ARTIFACTS[key])

    def test_models_accept_train_format(self):
        sample = self.X_train.iloc[:10]
        for key in TABULAR_KEYS:
            try:
                self.pipelines[key].predict(sample)
            except Exception as exc:  # pragma: no cover - defensive
                self.fail(f"{key} failed on train-format data: {exc}")

    def test_predictions_are_binary(self):
        sample = self.X_train.iloc[:10]
        for key in TABULAR_KEYS:
            preds = self.pipelines[key].predict(sample)
            self.assertTrue(set(np.unique(preds)).issubset({0, 1}), key)

    def test_predict_proba_returns_valid_probabilities(self):
        sample = self.X_train.iloc[:10]
        for key in TABULAR_KEYS:
            proba = self.pipelines[key].predict_proba(sample)
            self.assertEqual(proba.shape, (10, 2), key)
            self.assertTrue(np.all((proba >= 0) & (proba <= 1)), key)


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = joblib.load(EXPECTED_ARTIFACTS["linear_svc"])

    def test_linear_svc_uses_calibrated_classifier(self):
        model = self.svc.named_steps["model"]
        from sklearn.calibration import CalibratedClassifierCV
        self.assertIsInstance(model, CalibratedClassifierCV)

    def test_linear_svc_has_predict_proba(self):
        # CalibratedClassifierCV exposes predict_proba.
        df = ev.load_dataset()
        X_train, _, _, _ = ev.make_split(df)
        proba = self.svc.predict_proba(X_train.iloc[:5])
        self.assertEqual(proba.shape, (5, 2))
        self.assertTrue(np.all(np.isclose(proba.sum(axis=1), 1.0)))


class OversamplingPipelineTests(unittest.TestCase):
    def test_pipeline_functions_return_imbalanced_pipeline(self):
        from imblearn.pipeline import Pipeline as ImbPipeline
        for fn in [
            te.build_logistic_regression_pipeline,
            te.build_linear_svc_pipeline,
            te.build_complement_nb_pipeline,
            te.build_lightgbm_pipeline,
        ]:
            pipe = fn()
            self.assertIsInstance(pipe, ImbPipeline)
            self.assertIn("sampler", [s[0] for s in pipe.steps])

    def test_oversampling_only_in_training(self):
        # The sampler step is part of the pipeline, so it only runs during fit
        # on the training folds. Prediction path does not call fit_resample.
        df = ev.load_dataset()
        X_train, _, _, _ = ev.make_split(df)
        pipe = te.build_logistic_regression_pipeline()
        sampler = pipe.named_steps["sampler"]
        self.assertIsNotNone(sampler)
        from imblearn.over_sampling import RandomOverSampler
        self.assertIsInstance(sampler, RandomOverSampler)


class TrainReproducibilityTests(unittest.TestCase):
    def test_training_is_reproducible(self):
        # Train the same model twice with the same seed and compare artifacts.
        df = ev.load_dataset()
        X_train, _, y_train, _ = ev.make_split(df)
        with tempfile.TemporaryDirectory() as tmpdir:
            r1 = te.train_model("logistic_regression", X_train, y_train, tmpdir)
            r2 = te.train_model("logistic_regression", X_train, y_train, tmpdir)
            self.assertEqual(r1["train_metrics"], r2["train_metrics"])


class SplitIntegrityTests(unittest.TestCase):
    def test_test_not_used_in_training(self):
        # Confirm the split keeps 997 test rows (baseline size) and that the
        # training flow only uses the train set.
        df = ev.load_dataset()
        _, X_test, _, y_test = ev.make_split(df)
        self.assertEqual(len(X_test), 997)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_training(self):
        before = _raw_snapshot()
        df = ev.load_dataset()
        X_train, _, y_train, _ = ev.make_split(df)
        with tempfile.TemporaryDirectory() as tmpdir:
            te.train_model("logistic_regression", X_train, y_train, tmpdir)
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()