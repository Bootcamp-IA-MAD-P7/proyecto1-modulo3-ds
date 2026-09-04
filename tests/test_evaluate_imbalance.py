"""Validation tests for the imbalance-mitigation evaluation (Issue #048).

These tests use the standard library ``unittest`` (no pytest). They verify the
imbalance-mitigation flow implemented in ``scripts/evaluate_imbalance.py``:

* the split reproduces the baseline Train/Test boundary and derives a
  Validation subset from Train without touching Test,
* both classes are present in every fold,
* oversampling is applied ONLY to the training fold (estimate grows),
* metrics are bounded in [0, 1] and reported per strategy/threshold,
* the recommendation is driven by stroke F1/Recall (never accuracy alone),
* the threshold sweep covers the full ``0.30..0.70`` range,
* the report is generated,
* the raw dataset is not modified.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import evaluate_imbalance as ei  # noqa: E402
import evaluate_baseline as ev  # noqa: E402


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        (
            cls.X_train, cls.X_val, cls.X_test,
            cls.y_train, cls.y_val, cls.y_test,
        ) = ei.make_validation_split(cls.df)

    def test_split_partitions_the_dataset(self):
        n = len(self.df)
        self.assertEqual(
            len(self.X_train) + len(self.X_val) + len(self.X_test), n
        )
        self.assertEqual(len(self.y_train), len(self.X_train))
        self.assertEqual(len(self.y_val), len(self.X_val))
        self.assertEqual(len(self.y_test), len(self.X_test))

    def test_test_size_matches_baseline(self):
        # The reserved Test must keep the baseline size (997).
        self.assertEqual(len(self.X_test), 997)

    def test_train_val_test_cover_original_split(self):
        # Train + Val must equal the baseline Train (3984), Test untouched.
        self.assertEqual(len(self.X_train) + len(self.X_val), 3984)

    def test_both_classes_present_in_every_fold(self):
        self.assertEqual(set(self.y_train.unique()), {0, 1})
        self.assertEqual(set(self.y_val.unique()), {0, 1})
        self.assertEqual(set(self.y_test.unique()), {0, 1})


class StrategyExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = ei.run_strategies(cls.df)

    def test_expected_strategies_present(self):
        for key in ["baseline", "class_weight", "threshold", "oversampling"]:
            self.assertIn(key, self.res)

    def test_threshold_sweep_covers_full_range(self):
        sweep = self.res["threshold"]["sweep"]
        self.assertEqual(list(sweep.keys()), ei.THRESHOLDS)
        for t in ei.THRESHOLDS:
            for metric in ["precision", "recall", "f1"]:
                self.assertIn(metric, sweep[t])

    def test_oversampling_grows_the_estimator_input(self):
        # RandomOverSampler must be applied only on the training fold, so the
        # number of rows fed to the estimator grows vs. the baseline model.
        over_size = self.res["oversampling"]["estimator_input_size"]
        self.assertGreater(over_size, self.res["n_train"])

    def test_metrics_are_bounded(self):
        for strategy in ["baseline", "class_weight", "oversampling"]:
            for fold in ["train", "val", "test"]:
                m = self.res[strategy][fold]
                for key in ["accuracy", "precision", "recall", "f1", "f1_macro", "auc_roc"]:
                    self.assertGreaterEqual(m[key], 0.0)
                    self.assertLessEqual(m[key], 1.0)

    def test_confusion_matrix_is_2x2(self):
        cm = self.res["baseline"]["val"]["confusion_matrix"]
        self.assertEqual(len(cm), 2)
        self.assertTrue(all(len(row) == 2 for row in cm))


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = ei.run_strategies(cls.df)
        cls.rec = ei._recommendation(cls.res)

    def test_recommendation_returns_expected_keys(self):
        for key in ["ranking", "best_name", "best_f1", "best_recall", "best_threshold"]:
            self.assertIn(key, self.rec)

    def test_best_name_is_in_ranking_head(self):
        self.assertEqual(self.rec["ranking"][0], self.rec["best_name"])

    def test_recommendation_not_driven_by_accuracy_alone(self):
        # If the recommendation were accuracy-driven it would always pick a
        # high-accuracy (degenerate) strategy. We assert the chosen strategy has
        # a strictly positive stroke recall on Validation, i.e. it is not the
        # accuracy-maximal degenerate classifier.
        best = self.rec["best_name"]
        val_rows = ei.val_rows(self.res)
        self.assertGreater(val_rows[best]["recall"], 0.0)


class ReportTests(unittest.TestCase):
    def test_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "imbalance-mitigation.md")
            result = ei.evaluate_imbalance(report_path=out)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Dataset y split",
                "## 3. Estrategias evaluadas",
                "## 4. Resultados principales (Validación)",
                "## 5. Barrido de umbral (baseline)",
                "## 6. Métricas detalladas por estrategia",
                "## 8. Verificación en Test (post-selección, informativo)",
                "## 9. Recomendación",
            ]:
                self.assertIn(heading, text)
            for t in ei.THRESHOLDS:
                self.assertIn(f"| {t:.2f} |", text)
            self.assertIn("recommendation", result)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_evaluation(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            ei.evaluate_imbalance(report_path=os.path.join(tmpdir, "report.md"))
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()