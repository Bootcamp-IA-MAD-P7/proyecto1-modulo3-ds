"""Validation tests for the EDA visualizations (Issue #014).

These tests use the standard library ``unittest`` (no pytest). They verify that
every plot function produces a valid PNG file and that the report is generated
with the correct markdown that embeds each figure.
"""

import os
import struct
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import eda_visualizations as eda  # noqa: E402
from preprocessing import RAW_DATA_PATH  # noqa: E402


def is_png(path: str) -> bool:
    """Return True if the file exists and starts with the PNG magic bytes."""
    if not os.path.exists(path):
        return False
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(RAW_DATA_PATH)

    def test_each_plot_produces_a_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cases = [
                (eda.plot_class_imbalance, "class_imbalance.png"),
                (eda.plot_continuous_distributions, "continuous_distributions.png"),
                (eda.plot_continuous_vs_stroke, "continuous_vs_stroke.png"),
                (eda.plot_categorical_frequencies, "categorical_frequencies.png"),
                (eda.plot_categorical_vs_stroke, "categorical_vs_stroke.png"),
            ]
            for fn, fname in cases:
                with self.subTest(fname=fname):
                    path = fn(self.df, tmpdir)
                    self.assertTrue(is_png(path), f"{fname} no es un PNG válido")


class ReportTests(unittest.TestCase):
    def test_report_embeds_all_figures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fig_dir = os.path.join(tmpdir, "figures")
            out = os.path.join(tmpdir, "visualizations.md")
            figures = eda.generate_all(fig_dir, out)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
            # One section per figure and each is embedded with a relative link.
            for fname in eda.FIGURE_META:
                self.assertIn(fname[1], text)
            rel = os.path.relpath(fig_dir, start=os.path.dirname(out)).replace("\\", "/")
            for path in figures:
                link = os.path.relpath(path, start=os.path.dirname(out)).replace("\\", "/")
                self.assertIn(link, text)
            self.assertEqual(len(figures), len(eda.FIGURE_META))


if __name__ == "__main__":
    unittest.main()
