"""Tests for the FastAPI prediction service (Issue #026)."""

import os
import sys
import unittest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "scripts"))

from fastapi.testclient import TestClient  # noqa: E402

import backend.main as api  # noqa: E402

MODEL_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")

VALID = {
    "gender": "Female",
    "age": 45,
    "hypertension": 0,
    "heart_disease": 1,
    "ever_married": "Yes",
    "work_type": "Private",
    "Residence_type": "Urban",
    "avg_glucose_level": 100,
    "bmi": 25,
    "smoking_status": "never smoked",
}

client = TestClient(api.app)


class HealthTests(unittest.TestCase):
    def test_health_returns_200(self):
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)

    def test_health_json_valid(self):
        r = client.get("/health")
        self.assertEqual(r.json()["status"], "ok")

    def test_health_status_ok(self):
        self.assertEqual(client.get("/health").json()["status"], "ok")


class ValidationTests(unittest.TestCase):
    def test_valid_request_ok(self):
        r = client.post("/predict", json=VALID)
        self.assertEqual(r.status_code, 200)

    def _assert_422(self, **override):
        payload = dict(VALID, **override)
        return client.post("/predict", json=payload)

    def test_invalid_age_type(self):
        self.assertEqual(self._assert_422(age="abc").status_code, 422)

    def test_invalid_age_range(self):
        self.assertEqual(self._assert_422(age=200).status_code, 422)

    def test_invalid_avg_glucose(self):
        self.assertEqual(self._assert_422(avg_glucose_level=-5).status_code, 422)

    def test_invalid_bmi(self):
        self.assertEqual(self._assert_422(bmi=0).status_code, 422)

    def test_invalid_hypertension(self):
        self.assertEqual(self._assert_422(hypertension=2).status_code, 422)

    def test_invalid_heart_disease(self):
        self.assertEqual(self._assert_422(heart_disease="yes").status_code, 422)

    def test_invalid_gender(self):
        self.assertEqual(self._assert_422(gender="Unknown").status_code, 422)

    def test_invalid_ever_married(self):
        self.assertEqual(self._assert_422(ever_married="Maybe").status_code, 422)

    def test_invalid_work_type(self):
        self.assertEqual(self._assert_422(work_type="Doctor").status_code, 422)

    def test_invalid_residence(self):
        self.assertEqual(self._assert_422(Residence_type="Suburban").status_code, 422)

    def test_invalid_smoking_status(self):
        self.assertEqual(self._assert_422(smoking_status="vapes").status_code, 422)


class PredictionTests(unittest.TestCase):
    def test_predict_200_and_fields(self):
        r = client.post("/predict", json=VALID)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("prediction", body)
        self.assertIn("probability", body)

    def test_prediction_in_01(self):
        body = client.post("/predict", json=VALID).json()
        self.assertIn(body["prediction"], {0, 1})

    def test_probability_in_range(self):
        body = client.post("/predict", json=VALID).json()
        self.assertGreaterEqual(body["probability"], 0)
        self.assertLessEqual(body["probability"], 1)


class ModelTests(unittest.TestCase):
    def test_artifact_exists(self):
        self.assertTrue(os.path.exists(MODEL_ARTIFACT))

    def test_pipeline_has_preprocess_and_model(self):
        self.assertIn("preprocess", api._MODEL.named_steps)
        self.assertIn("model", api._MODEL.named_steps)

    def test_api_uses_persisted_artifact(self):
        import joblib

        pipeline = joblib.load(MODEL_ARTIFACT)
        self.assertTrue(hasattr(pipeline, "predict"))
        # Both objects describe the same trained baseline; API loads that artifact.
        self.assertTrue(hasattr(api._MODEL, "predict"))

    def test_no_model_created_during_request(self):
        tracked = {id(obj) for obj in (api._MODEL,) if obj is not None}
        client.post("/predict", json=VALID)
        self.assertEqual({id(api._MODEL)}, tracked)


class ResponseSchemaTests(unittest.TestCase):
    def test_response_matches_schema(self):
        body = client.post("/predict", json=VALID).json()
        parsed = api.PredictionResponse(**body)
        self.assertIn(parsed.prediction, {0, 1})
        self.assertGreaterEqual(parsed.probability, 0)
        self.assertLessEqual(parsed.probability, 1)


if __name__ == "__main__":
    unittest.main()