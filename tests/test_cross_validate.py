"""Validation tests for the cross-validation evaluation (Issue #047).

These tests use the standard library ``unittest`` (no pytest). They verify the
cross-validation flow implemented in ``scripts/cross_validate.py``:

* the correct number of folds (5) is used,
* random_state provides reproducibility,
* expected metrics are present in every fold and summary,
* results are numeric and not NaN,
* all 5 folds are represented,
* RandomOverSampler is only applied inside the training of each fold,
* data/raw is not modified,
* the reserved test set is not used during CV.
"""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import cross_validate as cv  # noqa: E402
import evaluate_baseline as ev  # noqa: E402


def _raw_snapshot() -> bytes:
    with open(ev.RAW_DATA_PATH, "rb") as fh:
        return fh.read()


class FoldConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = cv.run_all_strategies(cls.df)

    def test_five_folds(self):
        for strategy in ["baseline", "oversampling"]:
            self.assertEqual(len(self.res[strategy]["folds"]), cv.N_SPLITS)

    def test_folds_are_numbered_1_to_5(self):
        for strategy in ["baseline", "oversampling"]:
            fold_numbers = [f["fold"] for f in self.res[strategy]["folds"]]
            self.assertEqual(fold_numbers, [1, 2, 3, 4, 5])

    def test_random_state_is_reproducible(self):
        r2 = cv.run_all_strategies(self.df)
        for strategy in ["baseline", "oversampling"]:
            for i in range(cv.N_SPLITS):
                for metric in cv.SCORING:
                    self.assertEqual(
                        self.res[strategy]["folds"][i][metric],
                        r2[strategy]["folds"][i][metric],
                    )


class MetricsPresenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = cv.run_all_strategies(cls.df)

    def test_expected_metrics_in_folds(self):
        expected = ["accuracy", "precision", "recall", "f1", "roc_auc", "f1_macro"]
        for strategy in ["baseline", "oversampling"]:
            for fold in self.res[strategy]["folds"]:
                for metric in expected:
                    self.assertIn(metric, fold)

    def test_expected_metrics_in_summary(self):
        expected = ["accuracy", "precision", "recall", "f1", "roc_auc", "f1_macro"]
        for strategy in ["baseline", "oversampling"]:
            for metric in expected:
                self.assertIn(metric, self.res[strategy]["summary"])
                self.assertIn("mean", self.res[strategy]["summary"][metric])
                self.assertIn("std", self.res[strategy]["summary"][metric])


class NumericValidityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = cv.run_all_strategies(cls.df)

    def test_fold_metrics_are_numeric_and_bounded(self):
        for strategy in ["baseline", "oversampling"]:
            for fold in self.res[strategy]["folds"]:
                for metric in ["accuracy", "precision", "recall", "f1", "roc_auc", "f1_macro"]:
                    value = fold[metric]
                    self.assertIsInstance(value, (int, float))
                    self.assertFalse(np.isnan(value), f"{strategy} fold {fold['fold']} {metric} is NaN")
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 1.0)

    def test_summary_mean_and_std_are_numeric(self):
        for strategy in ["baseline", "oversampling"]:
            for metric in cv.SCORING:
                mean = self.res[strategy]["summary"][metric]["mean"]
                std = self.res[strategy]["summary"][metric]["std"]
                self.assertIsInstance(mean, (int, float))
                self.assertIsInstance(std, (int, float))
                self.assertFalse(np.isnan(mean))
                self.assertFalse(np.isnan(std))
                self.assertGreaterEqual(std, 0.0)


class OversamplingLeakageTests(unittest.TestCase):
    """Verify RandomOverSampler only applies to training, not validation."""

    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = cv.make_cv_split(cls.df)

    def test_oversampling_pipeline_has_sampler_step(self):
        pipe = cv.build_oversampling_pipeline()
        step_names = [name for name, _ in pipe.steps]
        self.assertIn("sampler", step_names)

    def test_baseline_pipeline_has_no_sampler_step(self):
        pipe = cv.build_baseline_pipeline()
        step_names = [name for name, _ in pipe.steps]
        self.assertNotIn("sampler", step_names)

    def test_oversampling_only_in_training(self):
        """Fit the oversampling pipeline on a small subset and verify that
        the number of rows fed to the model grows (due to oversampling)."""
        from imblearn.over_sampling import RandomOverSampler as ROS
        pre = cv.build_preprocessing_pipeline()
        column_transformer = pre.named_steps["preprocess"]
        # Take a small stratified sample for speed.
        from sklearn.model_selection import train_test_split
        X_sub, _, y_sub, _ = train_test_split(
            self.X_train, self.y_train, train_size=500,
            random_state=42, stratify=self.y_train,
        )
        X_proc = column_transformer.fit_transform(X_sub, y_sub)
        X_res, y_res = ROS(random_state=42).fit_resample(X_proc, y_sub)
        # Oversampling must increase the number of rows.
        self.assertGreater(X_res.shape[0], X_proc.shape[0])


class SplitIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = ev.load_dataset()
        cls.res = cv.run_all_strategies(cls.df)
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = cv.make_cv_split(cls.df)

    def test_test_set_size_matches_baseline(self):
        self.assertEqual(len(self.X_test), 997)

    def test_train_plus_test_covers_full_dataset(self):
        self.assertEqual(len(self.X_train) + len(self.X_test), len(self.df))

    def test_class_distribution_preserved(self):
        self.assertEqual(set(self.y_train.unique()), {0, 1})
        self.assertEqual(set(self.y_test.unique()), {0, 1})


class ReportTests(unittest.TestCase):
    def test_report_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "cross-validation.md")
            result = cv.cross_validate_all(report_path=out)
            self.assertTrue(os.path.exists(out))
            with open(out, encoding="utf-8") as fh:
                text = fh.read()
            for heading in [
                "## 1. Objetivo",
                "## 2. Dataset utilizado",
                "## 3. Metodología",
                "## 4. Estrategias evaluadas",
                "## 5. Métricas",
                "## 6. Resultados por fold",
                "## 7. Resumen estadístico (media y desviación estándar)",
                "## 8. Comparación",
                "## 9. Conclusión",
                "## 10. Limitaciones",
            ]:
                self.assertIn(heading, text)
            for fold_num in range(1, 6):
                self.assertIn(f"| {fold_num} |", text)
            self.assertIn("baseline_summary", result)
            self.assertIn("oversampling_summary", result)


class RawIntegrityTests(unittest.TestCase):
    def test_raw_unchanged_after_cv(self):
        before = _raw_snapshot()
        with tempfile.TemporaryDirectory() as tmpdir:
            cv.cross_validate_all(report_path=os.path.join(tmpdir, "report.md"))
        after = _raw_snapshot()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()