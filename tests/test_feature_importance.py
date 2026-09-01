"""Tests for the baseline feature importance analysis (Issue #021)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import analyze_feature_importance as afi  # noqa: E402
import evaluate_baseline as ev  # noqa: E402
from preprocessing import get_transformed_feature_names  # noqa: E402


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = ev.load_model()
        cls.model, cls.coef, cls.feature_names = afi.load_model_and_coefficients()

    def test_model_loads(self):
        self.assertIsNotNone(self.pipeline)

    def test_pipeline_contains_logistic_regression(self):
        self.assertIn("model", self.pipeline.named_steps)
        name = type(self.pipeline.named_steps["model"]).__name__
        self.assertEqual(name, "LogisticRegression")

    def test_coef_exists(self):
        self.assertTrue(hasattr(self.pipeline.named_steps["model"], "coef_"))

    def test_coef_count_matches_features(self):
        model_coef = self.pipeline.named_steps["model"].coef_
        expected_columns = get_transformed_feature_names(
            self.pipeline.named_steps["preprocess"]
        )
        self.assertEqual(model_coef.shape[1], len(expected_columns))

    def test_feature_names_recovered(self):
        self.assertEqual(len(self.feature_names), len(self.coef))
        self.assertIn("age", self.feature_names)
        self.assertIn("work_type_children", self.feature_names)
        self.assertEqual(len(self.feature_names), 19)


class CoefficientTableTests(unittest.TestCase):
    def setUp(self):
        _, coef, names = afi.load_model_and_coefficients()
        self.table = afi.build_coefficient_table(coef, names)

    def test_table_has_expected_columns(self):
        self.assertEqual(
            list(self.table.columns),
            ["feature", "coefficient", "abs_coefficient"],
        )

    def test_table_sorted_desc_by_abs(self):
        abs_vals = list(self.table["abs_coefficient"])
        self.assertEqual(abs_vals, sorted(abs_vals, reverse=True))

    def test_ties_reference(self):
        first = self.table.iloc[0]
        self.assertEqual(first["feature"], "age")


class RankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, coef, names = afi.load_model_and_coefficients()
        cls.table = afi.build_coefficient_table(coef, names)
        cls.top_pos = afi.top_n(cls.table, positive=True)
        cls.top_neg = afi.top_n(cls.table, positive=False)
        cls.top_abs = afi.top_by_magnitude(cls.table)

    def test_top_positive_are_positive(self):
        self.assertTrue((self.top_pos["coefficient"] > 0).all())
        self.assertGreaterEqual(len(self.top_pos), 1)

    def test_top_negative_are_negative(self):
        self.assertTrue((self.top_neg["coefficient"] < 0).all())
        self.assertGreaterEqual(len(self.top_neg), 1)

    def test_top_abs_sorted(self):
        self.assertEqual(
            list(self.top_abs["abs_coefficient"]),
            sorted(self.top_abs["abs_coefficient"], reverse=True),
        )

    def test_ranking_dynamic(self):
        self.assertEqual(len(self.top_abs), min(afi.N_TOP, len(self.table)))


class ArtifactTests(unittest.TestCase):
    def test_figure_and_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fig = os.path.join(tmpdir, "figures", "baseline-feature-coefficients.png")
            rep = os.path.join(tmpdir, "baseline-feature-importance.md")
            res = afi.analyze_feature_importance(report_path=rep, figure_path=fig)
            with open(fig, "rb") as fh:
                self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")
            with open(rep, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Modelo",
                "## 3. Cómo se obtienen los coeficientes",
                "## 4. Tabla de coeficientes",
                "## 5. Top features positivas",
                "## 6. Top features negativas",
                "## 7. Interpretación",
                "## 8. Limitaciones",
                "## 9. Conclusión",
            ]:
                self.assertIn(heading, text)
            self.assertEqual(res["figure_path"], fig)
            self.assertEqual(res["report_path"], rep)


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_analysis(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            afi.analyze_feature_importance(
                report_path=os.path.join(tmpdir, "report.md"),
                figure_path=os.path.join(tmpdir, "fig.png"),
            )
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()