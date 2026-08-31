"""Validation tests for the consolidated EDA report (Issue #015).

These tests use the standard library ``unittest`` (no pytest). They verify that
the consolidated report is generated correctly from the raw data (no hardcoded
results) and embeds the figures produced in Issue #014.
"""

import os
import re
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eda_report as eda  # noqa: E402
from preprocessing import RAW_DATA_PATH, TARGET_COLUMN  # noqa: E402


class ReportContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmpdir:
            cls.out = os.path.join(tmpdir, "eda-report.md")
            cls.text = eda.generate_report(cls.out)

    def test_all_sections_present(self):
        for heading in [
            "Resumen ejecutivo",
            "Datos y calidad",
            "Desbalance de clases",
            "Distribución de las variables",
            "Relaciones con `stroke`",
            "Frecuencias de categorías",
            "Conclusiones y siguientes pasos",
        ]:
            self.assertIn(heading, self.text)

    def test_imbalance_numbers_matched_from_data(self):
        df = pd.read_csv(RAW_DATA_PATH)
        counts = df[TARGET_COLUMN].value_counts().sort_index()
        ratio = counts[0] / counts[1]
        self.assertIn(f"{ratio:.2f}x", self.text)
        for v in counts.values:
            self.assertIn(str(int(v)), self.text)

    def test_figures_embedded(self):
        for fname in [
            "class_imbalance.png",
            "continuous_distributions.png",
            "categorical_frequencies.png",
            "continuous_vs_stroke.png",
            "categorical_vs_stroke.png",
        ]:
            self.assertIn(fname, self.text)

    def test_all_feature_names_referenced(self):
        df = pd.read_csv(RAW_DATA_PATH)
        for col in df.columns:
            self.assertIn(col, self.text)

    def test_no_hardcoded_results_in_source_templates(self):
        # The computed ratio must not be frozen as a literal in the template.
        with open(eda.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("19.08", src)
        self.assertNotIn("4733", src)


if __name__ == "__main__":
    unittest.main()
