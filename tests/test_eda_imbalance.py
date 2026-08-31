"""Validation tests for the class imbalance analysis (Issue #011).

These tests use the standard library ``unittest`` (no extra dependencies) and
verify that the imbalance metrics are computed correctly and directly from the
raw dataset (no hardcoded results):

* records per class,
* percentages per class,
* majority / minority class identification,
* imbalance ratio,
* the report can be generated correctly.
"""

import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eda_imbalance as eda  # noqa: E402
from preprocessing import RAW_DATA_PATH, TARGET_COLUMN  # noqa: E402


class ImbalanceMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)
        cls.m = eda.compute_imbalance(cls.df)

    def test_counts_computed_from_data(self):
        real_counts = self.df[TARGET_COLUMN].value_counts().sort_index()
        expected = {int(k): int(v) for k, v in real_counts.items()}
        self.assertEqual(self.m["counts"], expected)

    def test_total_matches_dataset(self):
        self.assertEqual(self.m["total"], len(self.df))
        self.assertEqual(sum(self.m["counts"].values()), self.m["total"])

    def test_percentages_sum_to_100(self):
        total = sum(self.m["percentages"].values())
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_majority_and_minority_classes(self):
        real_counts = self.df[TARGET_COLUMN].value_counts()
        self.assertEqual(self.m["majority_value"], int(real_counts.idxmax()))
        self.assertEqual(self.m["minority_value"], int(real_counts.idxmin()))
        self.assertNotEqual(self.m["majority_value"], self.m["minority_value"])

    def test_imbalance_ratio_is_correct_and_ge_1(self):
        ratio = self.m["majority_count"] / self.m["minority_count"]
        self.assertAlmostEqual(self.m["imbalance_ratio"], round(ratio, 2))
        self.assertGreaterEqual(self.m["imbalance_ratio"], 1.0)

    def test_ratio_matches_known_proportions(self):
        # Sanity: ~95% vs ~5% implies a ratio close to 19x.
        self.assertAlmostEqual(self.m["majority_pct"], 95.0, delta=3.0)
        self.assertAlmostEqual(self.m["imbalance_ratio"], 19.0, delta=2.0)


class ReportGenerationTests(unittest.TestCase):
    def test_report_generates_successfully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "class-imbalance.md")
            text = eda.generate_report(out)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(len(text), 0)
            self.assertIn("Ratio de desbalance", text)
            # No hardcoded results; value is computed at runtime.
            self.assertNotIn("estimado", text.lower())


if __name__ == "__main__":
    unittest.main()
