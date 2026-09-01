"""Validation tests for the overfitting analysis (Issue #020).

These tests use the standard library ``unittest`` (no pytest). They verify the
overfitting analysis implemented in ``scripts/analyze_overfitting.py``:

* the model and dataset load,
* the split is reproducible and has data,
* both classes are present in Train and Test,
* metrics are bounded in [0, 1],
* the gap is always >= 0 and its calculation is correct,
* the `< 5 pp` criterion is applied correctly,
* the report is generated,
* the raw dataset is not modified.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import analyze_overfitting as ao  # noqa: E402
import evaluate_baseline as ev  # noqa: E402

MODEL_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class ModelAndDatasetTests(unittest.TestCase):
    def test_model_loads(self):
        pipe = ev.load_model(MODEL_ARTIFACT)
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)

    def test_dataset_loads_and_split_reproducible(self):
        df = ev.load_dataset()
        X_train, X_test, y_train, y_test = ev.make_split(df)
        self.assertEqual(len(X_train) + len(X_test), len(df))
        self.assertEqual(len(X_train), 3984)
        self.assertEqual(len(X_test), 997)
        self.assertGreater(len(X_train), 0)
        self.assertGreater(len(X_test), 0)
        self.assertEqual(set(y_train.unique()), {0, 1})
        self.assertEqual(set(y_test.unique()), {0, 1})


class GapCalculationTests(unittest.TestCase):
    KEYS = ["accuracy", "precision", "recall", "f1", "auc_roc"]

    def test_gap_is_non_negative(self):
        base = {k: 0.9 for k in self.KEYS}
        lower = {k: 0.8 for k in self.KEYS}
        g = ao.compute_gap(base, lower)
        for key in self.KEYS:
            self.assertGreaterEqual(g[key], 0)

    def test_gap_calculation_is_correct(self):
        train = {"accuracy": 0.9506, "precision": 1.0, "recall": 0.0051,
                 "f1": 0.0101, "auc_roc": 0.8463}
        test = {"accuracy": 0.9498, "precision": 0.0, "recall": 0.0,
                "f1": 0.0, "auc_roc": 0.8459}
        gaps = ao.compute_gap(train, test)
        self.assertEqual(gaps["accuracy"], round(abs(0.9506 - 0.9498) * 100, 2))
        self.assertEqual(gaps["precision"], 100.0)
        self.assertEqual(gaps["recall"], round(abs(0.0051 - 0.0) * 100, 2))

    def test_criterion_applied_correctly(self):
        gaps = {"a": 4.9, "b": 5.0, "c": 0.0}
        res = ao.apply_criterio(gaps)
        self.assertEqual(res, {"a": "PASS", "b": "FAIL", "c": "PASS"})

    def test_metrics_bounded_and_gap_ge_0_on_real_data(self):
        df = ev.load_dataset()
        X_train, X_test, y_train, y_test = ev.make_split(df)
        p = ev.load_model(MODEL_ARTIFACT)
        mtr = ev.compute_metrics(y_train, p.predict(X_train), p.predict_proba(X_train)[:, 1])
        mte = ev.compute_metrics(y_test, p.predict(X_test), p.predict_proba(X_test)[:, 1])
        for key in ["accuracy", "precision", "recall", "f1", "auc_roc"]:
            self.assertGreaterEqual(mtr[key], 0.0)
            self.assertLessEqual(mtr[key], 1.0)
            self.assertGreaterEqual(mte[key], 0.0)
            self.assertLessEqual(mte[key], 1.0)
        gaps = ao.compute_gap(mtr, mte)
        for key in gaps:
            self.assertGreaterEqual(gaps[key], 0.0)


class ReportTests(unittest.TestCase):
    def test_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "baseline-overfitting.md")
            result = ao.analyze_overfitting(report_path=out)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Modelo evaluado",
                "## 3. Dataset y split",
                "## 4. Métricas Train/Test",
                "## 5. Tabla de gaps",
                "## 6. Criterio de aceptación",
                "## 7. Resultado PASS/FAIL",
                "## 8. Interpretación",
                "## 9. Conclusión",
            ]:
                self.assertIn(heading, text)
            self.assertIn("gaps", result)
            self.assertIn("results", result)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_analysis(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            ao.analyze_overfitting(report_path=os.path.join(tmpdir, "report.md"))
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()