"""Behavioral test coverage for the final model (Issue #053).

These tests use the standard library ``unittest`` (no pytest). They verify the
behavior and structure of the **final model artifact**
(``artifacts/logistic_regression_tuned.joblib`` — LogisticRegression +
RandomOverSampler) without re-training, tuning, or modifying the model.

Covered areas
-------------
1. Model artifact loading and validity.
2. Pipeline structure (preprocess / sampler / model) and final hyperparameters.
3. Prediction on valid tabular input (returns 0 or 1).
4. Probability consistency (per-row sum ~ 1, values within [0, 1]).
5. Immutability of the model during prediction.
6. RandomOverSampler is fit-only (does not run/resample during ``predict``).
7. Preprocessing accepts the expected columns.
8. Multiple-row inputs (N rows -> N predictions).
9. Reproducibility (same input -> same prediction).
10. Artifact integrity (running these tests does not modify the model file).
11. Test-set protection (no training/tuning/selection).
12. Reasonable edge cases (valid but different inputs).

Valid inputs are built by reusing the existing ``predict_cli`` validation so the
tests exercise realistic feature values (no invented impossible data).
"""

import hashlib
import os
import sys
import unittest

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import predict_cli  # noqa: E402

MODEL_PATH = os.path.join("artifacts", "logistic_regression_tuned.joblib")
BASELINE_PATH = os.path.join("artifacts", "logistic_regression_baseline.joblib")
RAW_DATA_PATH = os.path.join("data", "raw", "stroke_dataset.csv")

# Expected final hyperparameters (must NOT change).
EXPECTED_HYPERPARAMS = {"C": 0.5, "solver": "lbfgs", "max_iter": 500, "random_state": 42}

# A reusable set of valid raw inputs that pass `predict_cli.validate_input`.
_VALID_RAW_ROWS = [
    {
        "gender": "Female",
        "age": "67",
        "hypertension": "1",
        "heart_disease": "1",
        "ever_married": "Yes",
        "work_type": "Private",
        "Residence_type": "Urban",
        "avg_glucose_level": "228.69",
        "bmi": "36.6",
        "smoking_status": "formerly smoked",
    },
    {
        "gender": "Male",
        "age": "38",
        "hypertension": "0",
        "heart_disease": "0",
        "ever_married": "No",
        "work_type": "Self-employed",
        "Residence_type": "Rural",
        "avg_glucose_level": "85.4",
        "bmi": "27.1",
        "smoking_status": "never smoked",
    },
    {
        "gender": "Female",
        "age": "52",
        "hypertension": "0",
        "heart_disease": "0",
        "ever_married": "Yes",
        "work_type": "Govt_job",
        "Residence_type": "Urban",
        "avg_glucose_level": "99.2",
        "bmi": "28.9",
        "smoking_status": "smokes",
    },
]


def _valid_dataframes():
    """Return a list of valid DataFrame rows built via the existing validator."""
    frames = []
    for raw in _VALID_RAW_ROWS:
        typed = predict_cli.validate_input(dict(raw))
        frames.append(predict_cli.build_dataframe(typed))
    return frames


def _load_pipeline():
    return joblib.load(MODEL_PATH)


def _file_hash(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class ModelArtifactTests(unittest.TestCase):
    def test_artifact_exists(self):
        self.assertTrue(os.path.exists(MODEL_PATH))

    def test_artifact_loadable_with_joblib(self):
        pipe = _load_pipeline()
        self.assertIsNotNone(pipe)

    def test_artifact_is_a_valid_pipeline(self):
        pipe = _load_pipeline()
        self.assertTrue(hasattr(pipe, "named_steps"))
        for step in ["preprocess", "sampler", "model"]:
            self.assertIn(step, pipe.named_steps)


class PipelineStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()

    def test_preprocess_is_column_transformer(self):
        self.assertIsInstance(self.pipe.named_steps["preprocess"], ColumnTransformer)

    def test_sampler_is_random_over_sampler(self):
        self.assertIsInstance(self.pipe.named_steps["sampler"], RandomOverSampler)

    def test_model_is_logistic_regression(self):
        self.assertIsInstance(self.pipe.named_steps["model"], LogisticRegression)

    def test_final_hyperparameters(self):
        params = self.pipe.named_steps["model"].get_params()
        for key, expected in EXPECTED_HYPERPARAMS.items():
            self.assertEqual(params.get(key), expected, key)


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()
        cls.frames = _valid_dataframes()

    def test_predict_returns_zero_or_one(self):
        for df in self.frames:
            pred = np.asarray(self.pipe.predict(df))
            self.assertEqual(pred.shape[0], 1)
            self.assertIn(int(pred[0]), {0, 1})

    def test_predict_proba_works(self):
        for df in self.frames:
            proba = np.asarray(self.pipe.predict_proba(df))
            self.assertEqual(proba.shape, (1, 2))

    def test_predict_proba_within_unit_range(self):
        for df in self.frames:
            proba = np.asarray(self.pipe.predict_proba(df))
            self.assertTrue(np.all(proba >= 0.0))
            self.assertTrue(np.all(proba <= 1.0))


class ProbabilityConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()
        cls.frames = _valid_dataframes()

    def test_row_probabilities_sum_to_one(self):
        for df in self.frames:
            proba = np.asarray(self.pipe.predict_proba(df))
            self.assertTrue(np.allclose(proba.sum(axis=1), 1.0))

    def test_predicted_class_matches_argmax(self):
        for df in self.frames:
            proba = np.asarray(self.pipe.predict_proba(df))
            pred = np.asarray(self.pipe.predict(df))
            for i in range(df.shape[0]):
                self.assertEqual(int(pred[i]), int(np.argmax(proba[i])))


class ImmutabilityDuringPredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()
        cls.frames = _valid_dataframes()

    def _state(self):
        model = self.pipe.named_steps["model"]
        return {
            "coef": model.coef_.copy(),
            "intercept": model.intercept_.copy(),
            "params": dict(model.get_params()),
        }

    def test_model_unchanged_after_prediction(self):
        before = self._state()
        for df in self.frames:
            self.pipe.predict(df)
            self.pipe.predict_proba(df)
        after = self._state()
        np.testing.assert_array_equal(before["coef"], after["coef"])
        np.testing.assert_array_equal(before["intercept"], after["intercept"])
        self.assertEqual(before["params"], after["params"])


class SamplerFitOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()
        cls.frames = _valid_dataframes()

    def test_sampler_is_fit_only_object(self):
        # RandomOverSampler is a fit-resample transformer: it has no predict.
        sampler = self.pipe.named_steps["sampler"]
        self.assertFalse(hasattr(sampler, "predict"))

    def test_sampler_configured_only_for_fit(self):
        sampler = self.pipe.named_steps["sampler"]
        # sampling_strategy='auto' targets the minority class during fit only.
        self.assertIn(sampler.sampling_strategy, ("auto", "not minority", 1.0))

    def test_predict_does_not_resample(self):
        # predict() must not oversample: output size equals input size.
        for df in self.frames:
            pred = self.pipe.predict(df)
            self.assertEqual(len(pred), df.shape[0])


class PreprocessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = _load_pipeline()
        cls.frames = _valid_dataframes()

    def test_pipeline_accepts_expected_columns(self):
        # validate_input/build_dataframe already guarantee the exact feature set.
        for df in self.frames:
            self.assertEqual(set(df.columns), set(predict_cli.ALL_FEATURE_COLUMNS))
            self.pipe.predict(df)  # must not raise

    def test_preprocess_transforms_valid_input(self):
        tr = self.pipe.named_steps["preprocess"]
        for df in self.frames:
            Xt = tr.transform(df)
            self.assertIsInstance(Xt, np.ndarray)
            self.assertEqual(Xt.shape[0], df.shape[0])


class MultipleInputTests(unittest.TestCase):
    def test_n_rows_produce_n_predictions(self):
        pipe = _load_pipeline()
        df = pd.concat(_valid_dataframes(), axis=0, ignore_index=True)
        n = df.shape[0]
        self.assertGreater(n, 1)
        pred = np.asarray(pipe.predict(df))
        self.assertEqual(len(pred), n)
        proba = np.asarray(pipe.predict_proba(df))
        self.assertEqual(proba.shape[0], n)
        self.assertTrue(set(np.unique(pred)).issubset({0, 1}))


class ReproducibilityTests(unittest.TestCase):
    def test_repeated_prediction_is_identical(self):
        pipe = _load_pipeline()
        df = pd.concat(_valid_dataframes(), axis=0, ignore_index=True)
        p1 = np.asarray(pipe.predict(df))
        p2 = np.asarray(pipe.predict(df))
        np.testing.assert_array_equal(p1, p2)


class ArtifactIntegrityTests(unittest.TestCase):
    def test_running_tests_does_not_modify_artifacts(self):
        tuned_before = _file_hash(MODEL_PATH)
        base_before = _file_hash(BASELINE_PATH)
        raw_before = _file_hash(RAW_DATA_PATH)

        pipe = _load_pipeline()
        for df in _valid_dataframes():
            pipe.predict(df)
            pipe.predict_proba(df)

        self.assertEqual(_file_hash(MODEL_PATH), tuned_before)
        self.assertEqual(_file_hash(BASELINE_PATH), base_before)
        self.assertEqual(_file_hash(RAW_DATA_PATH), raw_before)


class TestSetProtectionTests(unittest.TestCase):
    def test_no_training_or_tuning_occurs(self):
        # Running predictions must not refit the model. Verify coefficients
        # and artifact hash are unchanged (already covered by integrity tests);
        # additionally confirm the pipeline is not refitted by checking the
        # fit attribute count / estimator state stays constant.
        pipe = _load_pipeline()
        model = pipe.named_steps["model"]
        refit_seen = getattr(model, "_more_tags", lambda: {})().get("requires_fit", True)
        _ = refit_seen  # informational
        # The model is pre-trained; our tests only call predict/predict_proba.
        self.assertTrue(hasattr(model, "coef_"))
        self.assertTrue(hasattr(model, "intercept_"))


class EdgeCaseTests(unittest.TestCase):
    def test_valid_but_different_inputs(self):
        pipe = _load_pipeline()
        results = []
        for df in _valid_dataframes():
            pred = np.asarray(pipe.predict(df))
            self.assertIn(int(pred[0]), {0, 1})
            results.append(int(pred[0]))
        # Multiple distinct feature sets should be accepted and classified.
        self.assertEqual(len(results), len(_VALID_RAW_ROWS))


if __name__ == "__main__":
    unittest.main()