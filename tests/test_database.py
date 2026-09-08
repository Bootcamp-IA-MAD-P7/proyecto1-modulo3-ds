"""Persistence layer tests for F5 RiskAI (Issue: database integration).

Strategy (aísla): the whole suite uses an in-memory SQLite database wired
through dependency overrides — the same code paths as PostgreSQL (same ORM)
without needing a local server. PostgreSQL remains the production target
(see backend/alembic for the migrations).

The prediction itself is exercised end-to-end (real Pipeline artifact) so the
persisted values are exactly the values returned by POST /predict.

Run from the repository root:

    python -m unittest tests.test_database -v
"""

from __future__ import annotations

import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models as models_module  # noqa: F401  (register tables)
from backend.database import Base, get_db, get_db_optional, storage_available
from backend.main import app
from backend.risk import risk_level_from_probability

# ---------------------------------------------------------------------------
# Isolated SQLite (in-memory) session factory + dependency overrides.
# ---------------------------------------------------------------------------

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_db_optional] = _override_get_db

VALID_PAYLOAD = {
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


class RiskLevelThresholdsTest(unittest.TestCase):
    """The canonical thresholds (LOW < 0.45, MEDIUM 0.45..0.72, HIGH >= 0.72)."""

    def test_threshold_boundaries(self):
        cases = [
            (0.26, "low"),   # spec example
            (0.30, "low"),   # old frontend 0.30 threshold no longer applies
            (0.44, "low"),
            (0.45, "medium"),  # lower inclusive bound
            (0.60, "medium"),  # spec example
            (0.71, "medium"),
            (0.72, "high"),  # upper inclusive bound
            (0.80, "high"),  # spec example
        ]
        for probability, expected in cases:
            with self.subTest(probability=probability):
                self.assertEqual(risk_level_from_probability(probability), expected)


class PersistenceApiTest(unittest.TestCase):
    """End-to-end persistence through the public API (SQLite in-memory)."""

    def setUp(self):
        # A fresh client keeps the shared in-memory DB, so purge between tests
        # to keep every test independent and deterministic.
        db = TestingSessionLocal()
        try:
            db.query(models_module.Assessment).delete()
            db.query(models_module.Patient).delete()
            db.commit()
        finally:
            db.close()
        self.client = TestClient(app)

    def _predict(self, payload=None):
        return self.client.post("/predict", json=payload or VALID_PAYLOAD)

    def test_predict_response_includes_risk_level_and_assessment_id(self):
        response = self._predict()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("prediction", body)
        self.assertIn("probability", body)
        self.assertIn("risk_level", body)
        self.assertIn("assessment_id", body)
        self.assertIn(body["risk_level"], ("low", "medium", "high"))
        # assessment_id must be a valid uuid when storage is enabled.
        uuid.UUID(body["assessment_id"])

    def test_persisted_assessment_matches_prediction_response(self):
        response = self._predict()
        body = response.json()

        patients = self.client.get("/patients").json()
        self.assertEqual(len(patients), 1)
        patient = patients[0]
        self.assertEqual(patient["age"], VALID_PAYLOAD["age"])
        self.assertEqual(patient["smoking_status"], VALID_PAYLOAD["smoking_status"])

        assessments = self.client.get("/assessments").json()
        self.assertEqual(len(assessments), 1)
        saved = assessments[0]
        self.assertEqual(saved["id"], body["assessment_id"])
        self.assertEqual(saved["prediction"], body["prediction"])
        self.assertAlmostEqual(saved["probability"], body["probability"])
        self.assertEqual(saved["risk_level"], body["risk_level"])

    def test_duplicate_patient_reuses_the_same_row(self):
        first = self._predict()
        second = self._predict()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.json()["assessment_id"], second.json()["assessment_id"])

        patients = self.client.get("/patients").json()
        assessments = self.client.get("/assessments").json()
        self.assertEqual(len(patients), 1)        # same clinical fingerprint
        self.assertEqual(len(assessments), 2)     # but two evaluations

    def test_patient_out_includes_last_assessment(self):
        self._predict()
        patient = self.client.get("/patients").json()[0]
        self.assertIsNotNone(patient["last_assessment"])
        self.assertIn("risk_level", patient["last_assessment"])

    def test_assessments_are_ordered_newest_first(self):
        first = self._predict().json()["assessment_id"]
        second = self._predict().json()["assessment_id"]
        ids = [a["id"] for a in self.client.get("/assessments").json()]
        # The second evaluation was created after the first.
        self.assertEqual(ids, [second, first])

    def test_get_assessment_detail_includes_patient_snapshot(self):
        assessment_id = self._predict().json()["assessment_id"]
        response = self.client.get(f"/assessments/{assessment_id}")
        self.assertEqual(response.status_code, 200)
        detail = response.json()
        self.assertEqual(detail["id"], assessment_id)
        self.assertEqual(detail["patient"]["age"], VALID_PAYLOAD["age"])
        self.assertEqual(detail["patient"]["residence_type"], VALID_PAYLOAD["Residence_type"])
        self.assertEqual(detail["patient"]["gender"], VALID_PAYLOAD["gender"])

    def test_missing_assessment_returns_404(self):
        response = self.client.get(f"/assessments/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_report_pdf_is_generated_from_real_data(self):
        assessment_id = self._predict().json()["assessment_id"]
        response = self.client.get(f"/assessments/{assessment_id}/report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("attachment", response.headers["content-disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_report_for_missing_assessment_returns_404(self):
        response = self.client.get(f"/assessments/{uuid.uuid4()}/report")
        self.assertEqual(response.status_code, 404)


@unittest.skipIf(
    storage_available,
    "Requires an environment WITHOUT DATABASE_URL (degraded storage behaviour).",
)
class DegradedStorageTest(unittest.TestCase):
    """App behaviour when no storage is configured (the default repo state)."""

    def setUp(self):
        # Remove the overrides so the real (unconfigured) dependencies run.
        app.dependency_overrides.clear()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_db_optional] = _override_get_db

    def test_storage_endpoints_return_friendly_503(self):
        for path in ("/patients", "/assessments"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json()["detail"],
                    "No se ha podido conectar con el almacenamiento.",
                )

    def test_predict_still_works_without_storage(self):
        response = self.client.post("/predict", json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("prediction", body)
        self.assertIn("probability", body)
        self.assertEqual(body["risk_level"] in ("low", "medium", "high"), True)
        self.assertIsNone(body["assessment_id"])


if __name__ == "__main__":
    unittest.main()