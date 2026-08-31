"""Validation tests for the feature-vs-stroke relationship analysis (#013).

These tests use the standard library ``unittest`` (no extra dependencies) and
verify that the relationship metrics are computed correctly and directly from
the raw dataset (no hardcoded results):

* continuous: per-class mean / median and Cohen's d,
* binary: per-class rate of the indicator,
* categorical: per-class category breakdown and shift,
* the report can be generated correctly.
"""

import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eda_relationships as eda  # noqa: E402
from preprocessing import (  # noqa: E402
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONTINUOUS_FEATURES,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)


class ContinuousRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_matches_per_class_means(self):
        for col in CONTINUOUS_FEATURES:
            with self.subTest(col=col):
                r = eda.continuous_relationship(self.df, col)
                pos = self.df.loc[self.df[TARGET_COLUMN] == 1, col]
                neg = self.df.loc[self.df[TARGET_COLUMN] == 0, col]
                self.assertEqual(r["mean_0"], round(float(neg.mean()), 3))
                self.assertEqual(r["mean_1"], round(float(pos.mean()), 3))
                self.assertEqual(r["median_0"], round(float(neg.median()), 3))
                self.assertEqual(r["median_1"], round(float(pos.median()), 3))
                self.assertEqual(
                    r["delta_mean"], round(float(pos.mean() - neg.mean()), 3)
                )

    def test_cohens_d_recomputed(self):
        for col in CONTINUOUS_FEATURES:
            with self.subTest(col=col):
                r = eda.continuous_relationship(self.df, col)
                d = eda.cohens_d(
                    self.df.loc[self.df[TARGET_COLUMN] == 1, col],
                    self.df.loc[self.df[TARGET_COLUMN] == 0, col],
                )
                self.assertEqual(r["d"], d)


class BinaryRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_rate_matches_per_class_means(self):
        for col in BINARY_FEATURES:
            with self.subTest(col=col):
                r = eda.binary_relationship(self.df, col)
                rate0 = float(self.df.loc[self.df[TARGET_COLUMN] == 0, col].mean())
                rate1 = float(self.df.loc[self.df[TARGET_COLUMN] == 1, col].mean())
                self.assertEqual(r["rate_1_given_0"], round(rate0, 3))
                self.assertEqual(r["rate_1_given_1"], round(rate1, 3))
                self.assertEqual(r["delta_rate"], round(rate1 - rate0, 3))


class CategoricalRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_shift_is_signed_difference(self):
        for col in CATEGORICAL_FEATURES:
            with self.subTest(col=col):
                table, max_shift = eda.categorical_relationship(self.df, col)
                tab = pd.crosstab(self.df[col], self.df[TARGET_COLUMN], normalize="columns") * 100
                for idx in table.index:
                    expected = round(tab[1][idx] - tab[0][idx], 3)
                    self.assertAlmostEqual(float(table.loc[idx, "shift_pp"]), expected, places=2)
                self.assertEqual(max_shift, round(float(table["shift_pp"].abs().max()), 3))

    def test_counts_per_class(self):
        for col in CATEGORICAL_FEATURES:
            with self.subTest(col=col):
                table, _ = eda.categorical_relationship(self.df, col)
                n0 = self.df.loc[self.df[TARGET_COLUMN] == 0, col].value_counts()
                n1 = self.df.loc[self.df[TARGET_COLUMN] == 1, col].value_counts()
                for idx in table.index:
                    self.assertEqual(int(table.loc[idx, "n_stroke0"]), int(n0[idx]))
                    self.assertEqual(int(table.loc[idx, "n_stroke1"]), int(n1[idx]))


class ReportGenerationTests(unittest.TestCase):
    def test_report_generates_successfully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "feature-relationships.md")
            text = eda.generate_report(out)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(len(text), 0)
            self.assertIn("Variables continuas", text)
            self.assertIn("Variables binarias", text)
            self.assertIn("Variables categóricas", text)
            for col in CONTINUOUS_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES:
                self.assertIn(col, text)


if __name__ == "__main__":
    unittest.main()
