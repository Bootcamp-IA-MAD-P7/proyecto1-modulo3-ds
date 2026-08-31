"""Validation tests for the feature-distribution analysis (Issue #012).

These tests use the standard library ``unittest`` (no extra dependencies) and
verify that the distribution metrics are computed correctly and directly from
the raw dataset (no hardcoded results):

* continuous metrics (shape, dispersion, outliers via the IQR rule),
* categorical frequency tables and dominant / infrequent categories,
* the report can be generated correctly.
"""

import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eda_distributions as eda  # noqa: E402
from preprocessing import RAW_DATA_PATH  # noqa: E402


class ContinuousMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_metrics_computed_from_data(self):
        for col in eda.CONTINUOUS_FEATURES:
            with self.subTest(col=col):
                r = eda.continuous_distribution(self.df, col)
                s = self.df[col].dropna()
                self.assertEqual(r["count"], int(s.count()))
                self.assertEqual(r["mean"], round(float(s.mean()), 3))
                self.assertEqual(r["median"], round(float(s.median()), 3))
                self.assertEqual(r["skewness"], round(float(s.skew()), 3))
                self.assertEqual(r["min"], round(float(s.min()), 3))
                self.assertEqual(r["max"], round(float(s.max()), 3))
                self.assertEqual(r["iqr"], round(float(s.quantile(0.75)) - float(s.quantile(0.25)), 3))

    def test_outliers_via_iqr_rule(self):
        for col in eda.CONTINUOUS_FEATURES:
            with self.subTest(col=col):
                r = eda.continuous_distribution(self.df, col)
                s = self.df[col].dropna()
                q1 = float(s.quantile(0.25))
                q3 = float(s.quantile(0.75))
                iqr = q3 - q1
                expected = s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)]
                self.assertEqual(r["n_outliers"], int(expected.size))
                self.assertEqual(
                    r["pct_outliers"],
                    round(expected.size / s.size * 100, 2),
                )


class CategoricalMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_counts_match_value_counts(self):
        for col in eda.CATEGORICAL_FEATURES:
            with self.subTest(col=col):
                table, dom = eda.categorical_distribution(self.df, col)
                real = self.df[col].value_counts().sort_values(ascending=False)
                self.assertEqual(table["count"].to_dict(), real.astype(int).to_dict())
                self.assertEqual(dom, str(real.idxmax()))

    def test_dominant_share_is_first_row(self):
        for col in eda.CATEGORICAL_FEATURES:
            with self.subTest(col=col):
                table, _ = eda.categorical_distribution(self.df, col)
                self.assertEqual(
                    table["percentage"].iloc[0],
                    table["share_dominant_pct"].iloc[0],
                )
                self.assertGreaterEqual(table["percentage"].iloc[0], table["percentage"].iloc[-1])

    def test_binary_features_have_two_values(self):
        for col in eda.BINARY_FEATURES:
            with self.subTest(col=col):
                self.assertEqual(len(self.df[col].value_counts()), 2)


class ReportGenerationTests(unittest.TestCase):
    def test_report_generates_successfully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "feature-distributions.md")
            text = eda.generate_report(out)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(len(text), 0)
            self.assertIn("Variables continuas", text)
            self.assertIn("Variables categóricas", text)
            for col in eda.CONTINUOUS_FEATURES:
                self.assertIn(col, text)
            for col in eda.CATEGORICAL_FEATURES:
                self.assertIn(col, text)


if __name__ == "__main__":
    unittest.main()
