"""Tests for the F5 RiskAI prediction CLI (Issue #022)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import predict_cli as cli
from preprocessing import ALL_FEATURE_COLUMNS, TARGET_COLUMN
from preprocessing import RAW_DATA_PATH

MODEL_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")
MODEL_METADATA = os.path.join(
    "artifacts", "logistic_regression_baseline_metadata.json"
)

VALID_INPUT = {
    "gender": "Female",
    "age": "45",
    "hypertension": "0",
    "heart_disease": "1",
    "ever_married": "Yes",
    "work_type": "Private",
    "Residence_type": "Urban",
    "avg_glucose_level": "100",
    "bmi": "25",
    "smoking_status": "never smoked",
}


class ModelTests(unittest.TestCase):
    def test_artifact_exists(self):
        self.assertTrue(os.path.exists(MODEL_ARTIFACT))

    def test_model_loads(self):
        pipeline = cli.load_model()
        self.assertIsNotNone(pipeline)

    def test_pipeline_contains_preprocess_and_model(self):
        pipeline = cli.load_model()
        self.assertIn("preprocess", pipeline.named_steps)
        self.assertIn("model", pipeline.named_steps)


class InputTests(unittest.TestCase):
    def test_valid_input_becomes_dataframe(self):
        values = cli.validate_input(VALID_INPUT)
        df = cli.build_dataframe(values)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)

    def test_columns_are_correct(self):
        values = cli.validate_input(VALID_INPUT)
        df = cli.build_dataframe(values)
        self.assertEqual(list(df.columns), ALL_FEATURE_COLUMNS)

    def test_stroke_not_in_features(self):
        values = cli.validate_input(VALID_INPUT)
        df = cli.build_dataframe(values)
        self.assertNotIn(TARGET_COLUMN, df.columns)


class ValidationTests(unittest.TestCase):
    def test_invalid_age_rejected(self):
        data = dict(VALID_INPUT, age="abc")
        with self.assertRaises(ValueError):
            cli.validate_input(data)

    def test_out_of_range_age_rejected(self):
        data = dict(VALID_INPUT, age="200")
        with self.assertRaises(ValueError):
            cli.validate_input(data)

    def test_invalid_avg_glucose_rejected(self):
        data = dict(VALID_INPUT, avg_glucose_level="abc")
        with self.assertRaises(ValueError):
            cli.validate_input(data)

    def test_invalid_bmi_rejected(self):
        data = dict(VALID_INPUT, bmi="abc")
        with self.assertRaises(ValueError):
            cli.validate_input(data)

    def test_invalid_hypertension_rejected(self):
        for val in ("2", "yes"):
            with self.assertRaises(ValueError):
                cli.validate_input(dict(VALID_INPUT, hypertension=val))

    def test_invalid_heart_disease_rejected(self):
        for val in ("3", "true"):
            with self.assertRaises(ValueError):
                cli.validate_input(dict(VALID_INPUT, heart_disease=val))

    def test_invalid_gender_rejected(self):
        with self.assertRaises(ValueError):
            cli.validate_input(dict(VALID_INPUT, gender="Unknown"))

    def test_invalid_ever_married_rejected(self):
        with self.assertRaises(ValueError):
            cli.validate_input(dict(VALID_INPUT, ever_married="Maybe"))

    def test_invalid_work_type_rejected(self):
        with self.assertRaises(ValueError):
            cli.validate_input(dict(VALID_INPUT, work_type="Doctor"))

    def test_invalid_residence_rejected(self):
        with self.assertRaises(ValueError):
            cli.validate_input(dict(VALID_INPUT, Residence_type="Suburban"))

    def test_invalid_smoking_status_rejected(self):
        with self.assertRaises(ValueError):
            cli.validate_input(dict(VALID_INPUT, smoking_status="vapes"))


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = cli.load_model()
        cls.values = cli.validate_input(VALID_INPUT)
        cls.result = cli.predict(cls.pipeline, cls.values)

    def test_predict_produces_valid_class(self):
        self.assertIn(self.result["prediction"], {0, 1})

    def test_predict_proba_works(self):
        self.assertIsNotNone(self.result["probability"])

    def test_probability_between_0_and_1(self):
        self.assertGreaterEqual(self.result["probability"], 0)
        self.assertLessEqual(self.result["probability"], 1)


class IntegrationTests(unittest.TestCase):
    def test_full_flow(self):
        pipeline = cli.load_model()
        values = cli.validate_input(VALID_INPUT)
        df = cli.build_dataframe(values)
        result = cli.predict(pipeline, values)
        self.assertIn(result["prediction"], {0, 1})
        self.assertGreaterEqual(result["probability"], 0)
        self.assertLessEqual(result["probability"], 1)
        self.assertEqual(len(df), 1)

    def test_missing_model_raises_clear_error(self):
        with self.assertRaises(cli.ModelUnavailableError):
            cli.load_model(os.path.join("artifacts", "does_not_exist.joblib"))


class IntegrityTests(unittest.TestCase):
    def test_raw_unchanged(self):
        before = _raw_snapshot()
        pipeline = cli.load_model()
        cli.predict(pipeline, cli.validate_input(VALID_INPUT))
        after = _raw_snapshot()
        self.assertEqual(before, after)

    def test_artifacts_unchanged(self):
        model_before = _file_snapshot(MODEL_ARTIFACT)
        meta_before = _file_snapshot(MODEL_METADATA)
        pipeline = cli.load_model()
        cli.predict(pipeline, cli.validate_input(VALID_INPUT))
        self.assertEqual(_file_snapshot(MODEL_ARTIFACT), model_before)
        self.assertEqual(_file_snapshot(MODEL_METADATA), meta_before)


def _raw_snapshot() -> bytes:
    with open(RAW_DATA_PATH, "rb") as fh:
        return fh.read()


def _file_snapshot(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


if __name__ == "__main__":
    unittest.main()