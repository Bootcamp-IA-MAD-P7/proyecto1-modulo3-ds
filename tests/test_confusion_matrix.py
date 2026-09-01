"""Validation tests for the confusion-matrix analysis (Issue #019).

These tests use the standard library ``unittest`` (no pytest). They verify the
confusion-matrix analysis implemented in ``scripts/analyze_confusion_matrix.py``:

* the model loads,
* the split is reproducible,
* predictions have the expected size,
* the confusion matrix is 2x2 and sums to the number of Test samples,
* all four components are non-negative,
* derived metrics are bounded in [0, 1],
* the figure is generated,
* the report is generated,
* the raw dataset is not modified.
"""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import analyze_confusion_matrix as acm  # noqa: E402
import evaluate_baseline as ev  # noqa: E402

MODEL_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class ModelTests(unittest.TestCase):
    def test_model_loads(self):
        pipe = acm.ev.load_model()
        self.assertIn("preprocess", pipe.named_steps)
        self.assertIn("model", pipe.named_steps)


class SplitAndPredictionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = acm.ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = acm.ev.make_split(cls.df)
        cls.pipe = acm.ev.load_model()
        cls.pred_test = cls.pipe.predict(cls.X_test)

    def test_split_reproducible(self):
        n = len(self.df)
        self.assertEqual(len(self.X_train) + len(self.X_test), n)
        self.assertEqual(len(self.X_train), 3984)
        self.assertEqual(len(self.X_test), 997)

    def test_predictions_have_expected_size(self):
        self.assertEqual(len(self.pred_test), len(self.y_test))


class ConfusionMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = acm.ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = acm.ev.make_split(cls.df)
        cls.pipe = acm.ev.load_model()
        cls.cm = acm.compute_confusion_matrix(cls.y_test, cls.pipe.predict(cls.X_test))
        cls.comp = acm.components(cls.cm)

    def test_cm_is_2x2(self):
        self.assertEqual(self.cm.shape, (2, 2))

    def test_cm_sums_to_test_size(self):
        self.assertEqual(int(self.cm.sum()), len(self.y_test))

    def test_components_non_negative(self):
        for key in ["tn", "fp", "fn", "tp"]:
            self.assertGreaterEqual(self.comp[key], 0)

    def test_component_split_matches_cm(self):
        expected = {"tn": int(self.cm[0, 0]), "fp": int(self.cm[0, 1]),
                    "fn": int(self.cm[1, 0]), "tp": int(self.cm[1, 1])}
        self.assertEqual(self.comp, expected)


class DerivedMetricsTests(unittest.TestCase):
    def test_metrics_bounded(self):
        comp = {"tn": 100, "fp": 10, "fn": 5, "tp": 50}
        for key, val in acm.derived_metrics(comp).items():
            self.assertGreaterEqual(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_zero_division_handled(self):
        comp = {"tn": 100, "fp": 0, "fn": 50, "tp": 0}
        deriv = acm.derived_metrics(comp)
        self.assertEqual(deriv, {"precision": 0.0, "recall": 0.0, "f1": 0.0})


class ArtifactTests(unittest.TestCase):
    def test_figure_and_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fig = os.path.join(tmpdir, "figures", "baseline-confusion-matrix.png")
            report = os.path.join(tmpdir, "confusion-matrix-analysis.md")
            result = acm.analyze_confusion_matrix(report_path=report, figure_path=fig)
            # Figure is a valid PNG.
            with open(fig, "rb") as fh:
                self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")
            # Report contains required sections.
            with open(report, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Modelo utilizado",
                "## 3. Dataset y split",
                "## 4. Confusion matrix",
                "## 5. TN / FP / FN / TP",
                "## 6. Interpretación de errores",
                "## 7. Relación con Precision / Recall / F1",
                "## 8. Principales conclusiones",
            ]:
                self.assertIn(heading, text)
            # The report must embed the generated figure via a relative link.
            self.assertIn(os.path.basename(fig), text)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_analysis(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            acm.analyze_confusion_matrix(
                report_path=os.path.join(tmpdir, "report.md"),
                figure_path=os.path.join(tmpdir, "fig.png"),
            )
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()