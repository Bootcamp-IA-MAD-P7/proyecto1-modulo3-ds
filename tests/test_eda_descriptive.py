"""Validation tests for the descriptive statistics report (Issue #010).

These tests use the standard library ``unittest`` (no extra dependencies) and
verify that:

* expected columns exist,
* the total number of records is 4981,
* binary-variable tables cover all records,
* categorical-variable tables cover all records,
* percentages in each table sum to ~100%,
* the markdown report can be generated correctly,
* the "most dispersed" conclusion is data-driven (not hardcoded).
"""

import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eda_descriptive as eda  # noqa: E402
from preprocessing import RAW_DATA_PATH  # noqa: E402

EXPECTED_COLUMNS = {
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "ever_married",
    "work_type",
    "Residence_type",
    "avg_glucose_level",
    "bmi",
    "smoking_status",
    "stroke",
}


class DatasetColumnsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_expected_columns_exist(self):
        self.assertTrue(EXPECTED_COLUMNS.issubset(set(self.df.columns)))

    def test_total_records_is_4981(self):
        self.assertEqual(len(self.df), 4981)

    def test_no_missing_value_or_duplicates(self):
        self.assertEqual(int(self.df.isnull().sum().sum()), 0)
        self.assertEqual(int(self.df.duplicated().sum()), 0)


class BinaryTablesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)
        cls.tables = eda.build_binary_tables(cls.df)

    def test_binary_columns_present(self):
        self.assertEqual(set(self.tables.keys()), set(eda.BINARY_FEATURES))

    def test_binary_tables_conserve_all_records(self):
        for col in eda.BINARY_FEATURES:
            total = int(self.tables[col]["count"].sum())
            self.assertEqual(total, len(self.df), msg=f"{col!r} count sum mismatch")

    def test_binary_percentages_sum_to_100(self):
        for col in eda.BINARY_FEATURES:
            total = float(self.tables[col]["percentage"].sum())
            self.assertAlmostEqual(total, 100.0, places=1, msg=f"{col!r} percentages")


class CategoricalTablesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)
        cls.tables = eda.build_categorical_tables(cls.df)

    def test_categorical_columns_present(self):
        self.assertEqual(set(self.tables.keys()), set(eda.CATEGORICAL_FEATURES))

    def test_categorical_tables_conserve_all_records(self):
        for col in eda.CATEGORICAL_FEATURES:
            table = self.tables[col][0]
            total = int(table["count"].sum())
            self.assertEqual(total, len(self.df), msg=f"{col!r} count sum mismatch")

    def test_categorical_percentages_sum_to_100(self):
        for col in eda.CATEGORICAL_FEATURES:
            table = self.tables[col][0]
            total = float(table["percentage"].sum())
            self.assertAlmostEqual(total, 100.0, places=1, msg=f"{col!r} percentages")

    def test_unknown_kept_as_valid_category(self):
        table = self.tables["smoking_status"][0]
        self.assertIn("Unknown", table.index)


class ContinuousAndDispersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)
        cls.continuous = eda.build_continuous_table(cls.df)

    def test_continuous_columns_expected(self):
        self.assertEqual(
            set(self.continuous.index), set(eda.CONTINUOUS_FEATURES)
        )

    def test_continuous_table_conserves_all_records(self):
        for col in eda.CONTINUOUS_FEATURES:
            self.assertEqual(int(self.continuous.loc[col, "count"]), len(self.df))

    def test_relative_dispersion_is_data_driven(self):
        cv = eda.relative_dispersion(self.df)
        self.assertEqual(set(cv.keys()), set(eda.CONTINUOUS_FEATURES))
        most = eda.find_most_dispersed(self.df)
        # The most dispersed must be the one with the highest CV.
        self.assertEqual(cv[most], max(cv.values()))


class ReportGenerationTests(unittest.TestCase):
    def test_report_generates_successfully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "report.md")
            text = eda.generate_report(out)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(len(text), 0)
            # Report must be data-driven: no hardcoded "estimado" phrasing.
            self.assertNotIn("estimado", text.lower())


if __name__ == "__main__":
    unittest.main()
