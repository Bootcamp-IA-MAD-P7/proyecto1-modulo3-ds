"""Compare trained ensemble candidate models for F5 RiskAI (Issue #050).

This script compares the candidate models trained in Issue #049 using
**out-of-fold predictions from Stratified 5-Fold Cross-Validation** on the
training set. This is the established validation flow (Issue #047): each model
is re-fitted inside every fold, so every validation prediction comes from data
the model did not train on. The reserved Test set is **not** used to select a
model.

Models compared
---------------
1. **Original Baseline**: LogisticRegression, no ROS (reference from #017/#018).
2. **LogisticRegression + ROS** (#049).
3. **LinearSVC + CalibratedClassifierCV + ROS** (#049).
4. **ComplementNB + ROS** (#049).
5. **LightGBM + ROS** (#049).

Approach note
-------------
The #049 artifacts were trained on the full training set (3984 rows). To obtain
metrics on data those models did not see, we re-run each candidate model
configuration through Stratified 5-Fold Cross-Validation on the training set
(same methodology as Issue #047). The already-trained artifacts are loaded and
validated (existence, load, prediction format) and reported as the deliverables
of #049; the selection is based on the out-of-fold comparison.

Metrics
-------
Accuracy, Precision, Recall, F1, ROC-AUC, F1-macro (positive class
``stroke = 1``). The best model is selected by a composite score that weighs
stroke recall, stroke F1, F1-macro and ROC-AUC — **never Accuracy alone**.

Run from the repository root::

    python scripts/compare_models.py [--output reports/model-comparison.md]
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_validate

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import evaluate_baseline as ev  # noqa: E402
import train_ensemble as te  # noqa: E402

DEFAULT_REPORT = os.path.join("reports", "model-comparison.md")

# Cross-validation configuration (same as Issue #047).
N_SPLITS = 5
CV_RANDOM_STATE = 42
POSITIVE_LABEL = 1  # stroke = 1

# Metric scoring (make_scorer with zero_division=0 to avoid warnings).
SCORING = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "recall": make_scorer(recall_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "f1": make_scorer(f1_score, pos_label=POSITIVE_LABEL, zero_division=0),
    "roc_auc": "roc_auc",
    "f1_macro": make_scorer(f1_score, average="macro", zero_division=0),
}

METRICS = ["accuracy", "precision", "recall", "f1", "roc_auc", "f1_macro"]

BASELINE_ARTIFACT = os.path.join("artifacts", "logistic_regression_baseline.joblib")

# The four candidate artifacts trained in #049.
CANDIDATE_ARTIFACTS = {
    "logistic_regression": os.path.join("artifacts", "logistic_regression_ensemble.joblib"),
    "linear_svc": os.path.join("artifacts", "linear_svc_calibrated.joblib"),
    "complement_nb": os.path.join("artifacts", "complement_nb_ensemble.joblib"),
    "lightgbm": os.path.join("artifacts", "lightgbm_ensemble.joblib"),
}

CANDIDATE_LABELS = {
    "logistic_regression": "LogisticRegression + ROS",
    "linear_svc": "LinearSVC + ROS",
    "complement_nb": "ComplementNB + ROS",
    "lightgbm": "LightGBM + ROS",
}


def build_baseline_pipeline():
    """Return the original baseline pipeline (no ROS), for reference."""
    return ImbPipeline([
        ("preprocess", te.build_baseline_preprocessing()),
        ("model", LogisticRegression(**te.LR_PARAMS)),
    ])


def build_candidate_pipeline(key: str):
    """Return the pipeline factory for a candidate model (reuses #049)."""
    factories = {
        "logistic_regression": te.build_logistic_regression_pipeline,
        "linear_svc": te.build_linear_svc_pipeline,
        "complement_nb": te.build_complement_nb_pipeline,
        "lightgbm": te.build_lightgbm_pipeline,
    }
    return factories[key]()


def run_cv_metrics(pipeline, X, y, cv, label: str) -> dict:
    """Run CV for a pipeline and return summary (mean/std) per metric."""
    results = cross_validate(pipeline, X, y, cv=cv, scoring=SCORING)
    summary = {}
    for metric in METRICS:
        values = results[f"test_{metric}"]
        summary[metric] = {
            "mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values)), 4),
        }
    return {"label": label, "summary": summary}


def compare_all(df: pd.DataFrame) -> dict:
    """Run CV for the baseline and all candidates, returning combined results."""
    X_train, X_test, y_train, y_test = ev.make_split(df)

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=CV_RANDOM_STATE)

    results = {}
    results["baseline"] = run_cv_metrics(
        build_baseline_pipeline(), X_train, y_train, skf, "Original Baseline"
    )
    for key in CANDIDATE_ARTIFACTS:
        results[key] = run_cv_metrics(
            build_candidate_pipeline(key), X_train, y_train, skf, CANDIDATE_LABELS[key]
        )

    return {
        "results": results,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "n_pos_train": int((y_train == POSITIVE_LABEL).sum()),
    }


def _artifact_valid_prediction(key: str, X_sample) -> bool:
    """Load a #049 artifact and verify it produces valid binary predictions."""
    import joblib
    pipe = joblib.load(CANDIDATE_ARTIFACTS[key])
    preds = pipe.predict(X_sample)
    return set(np.unique(preds)).issubset({0, 1})


def artifact_check(df: pd.DataFrame) -> dict:
    """Verify all candidate artifacts load and predict on the train format."""
    X_train, _, _, _ = ev.make_split(df)
    sample = X_train.iloc[:10]
    check = {}
    for key in CANDIDATE_ARTIFACTS:
        import joblib
        pipe = joblib.load(CANDIDATE_ARTIFACTS[key])
        preds = np.asarray(pipe.predict(sample))
        check[key] = {
            "exists": os.path.exists(CANDIDATE_ARTIFACTS[key]),
            "has_predict_proba": hasattr(pipe, "predict_proba"),
            "valid_binary": set(np.unique(preds)).issubset({0, 1}),
            "loads": True,
        }
    return check


def _score_model(metrics: dict) -> float:
    """Composite selection score (~not accuracy-driven).

    Weighs stroke recall, stroke F1, F1-macro and ROC-AUC.
    """
    return (
        metrics["recall"] * 0.30
        + metrics["f1"] * 0.30
        + metrics["f1_macro"] * 0.20
        + metrics["roc_auc"] * 0.20
    )


def decide_best(results: dict) -> dict:
    """Return per-criterion leaders and the overall best model."""
    def _best(metric):
        return max(
            [k for k in results if metric in results[k]["summary"]],
            key=lambda k: results[k]["summary"][metric]["mean"],
        )

    best_recall = _best("recall")
    best_f1 = _best("f1")
    best_f1_macro = _best("f1_macro")
    best_roc_auc = _best("roc_auc")

    overall_scores = {
        key: _score_model({m: results[key]["summary"][m]["mean"] for m in METRICS})
        for key in results
    }
    best_overall = max(overall_scores, key=overall_scores.get)

    return {
        "best_recall": best_recall,
        "best_f1": best_f1,
        "best_f1_macro": best_f1_macro,
        "best_roc_auc": best_roc_auc,
        "best_overall": best_overall,
        "scores": overall_scores,
    }


def _row(results: dict, key: str) -> str:
    s = results[key]["summary"]
    return (
        f"| {results[key]['label']} | {s['accuracy']['mean']:.4f} | "
        f"{s['precision']['mean']:.4f} | {s['recall']['mean']:.4f} | "
        f"{s['f1']['mean']:.4f} | {s['roc_auc']['mean']:.4f} | "
        f"{s['f1_macro']['mean']:.4f} |"
    )


def build_report(results: dict, artifacts: dict, decision: dict) -> str:
    """Compose the markdown model-comparison report."""
    res = results["results"]

    lines: list[str] = []
    lines.append("# Informe — Comparación de Modelos (Ensemble)")
    lines.append("")
    lines.append("**Proyecto:** F5 RiskAI")
    lines.append("**Fase:** Comparación de modelos (ML, Issue #050)")
    lines.append(f"**Fuente de datos:** `{ev.RAW_DATA_PATH}`")
    lines.append("")
    lines.append(
        "> Este informe compara los modelos candidatos entrenados en #049 usando "
        "**Cross-Validation out-of-fold** sobre el conjunto de entrenamiento. El "
        "conjunto Test se mantiene reservado y NO se utiliza para seleccionar el "
        "modelo."
    )
    lines.append("")
    lines.append(
        "> **Nota:** las métricas no implican rendimiento clínico ni relación causal."
    )
    lines.append("")

    lines.append("## 1. Objetivo")
    lines.append("")
    lines.append(
        "Identificar, mediante comparación objetiva sobre datos no utilizados "
        "para entrenar, qué modelo candidato presenta el mejor equilibrio y "
        "debería pasar a la siguiente fase de optimización."
    )
    lines.append("")

    lines.append("## 2. Dataset y split")
    lines.append("")
    lines.append(
        f"- **Total:** {results['n_train'] + results['n_test']} registros."
    )
    lines.append(f"- **Train (CV):** {results['n_train']} registros "
                 f"({results['n_pos_train']} positivos).")
    lines.append(f"- **Test (reservado):** {results['n_test']} registros.")
    lines.append("- **Test no se usa para seleccionar el modelo.**")
    lines.append("")

    lines.append("## 3. Metodología")
    lines.append("")
    lines.append(
        "- **StratifiedKFold(5, shuffle=True, random_state=42)** sobre Train."
    )
    lines.append(
        "- Cada modelo se re-ajusta dentro de cada fold; las predicciones de "
        "validación siempre provienen de datos no vistos en el entrenamiento."
    )
    lines.append(
        "- Se informa **media y desviación estándar** por métrica a través de "
        "los 5 folds."
    )
    lines.append("")

    lines.append("## 4. Modelos comparados")
    lines.append("")
    for key in ["baseline", *CANDIDATE_ARTIFACTS]:
        lines.append(f"- **{res[key]['label']}**.")
    lines.append("")

    lines.append("## 5. Métricas")
    lines.append("")
    lines.append(
        "Accuracy, Precision, Recall, F1 (clase `stroke=1`), ROC-AUC y F1-macro. "
        "Se prioriza Recall/F1 de `stroke`, F1-macro y ROC-AUC."
    )
    lines.append("")

    lines.append("## 6. Tabla de comparación (métricas out-of-fold)")
    lines.append("")
    lines.append("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | F1-macro |")
    lines.append("|------|----------|-----------|--------|----|---------|----------|")
    for key in ["baseline", *CANDIDATE_ARTIFACTS]:
        lines.append(_row(res, key))
    lines.append("")

    lines.append("## 7. Desviación estándar entre folds (estabilidad)")
    lines.append("")
    lines.append("| Model | Acc Std | Prec Std | Rec Std | F1 Std | AUC Std | Macro Std |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for key in ["baseline", *CANDIDATE_ARTIFACTS]:
        s = res[key]["summary"]
        lines.append(
            f"| {res[key]['label']} | {s['accuracy']['std']:.4f} | {s['precision']['std']:.4f} | "
            f"{s['recall']['std']:.4f} | {s['f1']['std']:.4f} | {s['roc_auc']['std']:.4f} | "
            f"{s['f1_macro']['std']:.4f} |"
        )
    lines.append("")

    lines.append("## 8. Análisis por métrica")
    lines.append("")
    def _label(key):
        return res[key]["label"]
    lines.append(f"- **Mejor Recall (stroke):** {_label(decision['best_recall'])} "
                 f"= {res[decision['best_recall']]['summary']['recall']['mean']:.4f}.")
    lines.append(f"- **Mejor F1 (stroke):** {_label(decision['best_f1'])} "
                 f"= {res[decision['best_f1']]['summary']['f1']['mean']:.4f}.")
    lines.append(f"- **Mejor F1-macro:** {_label(decision['best_f1_macro'])} "
                 f"= {res[decision['best_f1_macro']]['summary']['f1_macro']['mean']:.4f}.")
    lines.append(f"- **Mejor ROC-AUC:** {_label(decision['best_roc_auc'])} "
                 f"= {res[decision['best_roc_auc']]['summary']['roc_auc']['mean']:.4f}.")
    lines.append("")

    lines.append("## 9. Selección del modelo")
    lines.append("")
    total = {k: res[k]["summary"] for k in res}
    lines.append(
        f"El **mejor equilibrio general** (score compuesto que pondera Recall, F1, "
        f"F1-macro y ROC-AUC) corresponde a **{_label(decision['best_overall'])}**."
    )
    lines.append("")
    lines.append("| Model | Score compuesto |")
    lines.append("|---|---:|")
    for key, sc in sorted(decision["scores"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| {_label(key)} | {sc:.4f} |")
    lines.append("")

    lines.append("## 10. Comparación con el baseline original")
    lines.append("")
    bl = res["baseline"]["summary"]
    lines.append(
        f"El baseline original alcanza Recall(stroke)={bl['recall']['mean']:.4f} y "
        f"F1(stroke)={bl['f1']['mean']:.4f}. Los modelos con ROS mejoran "
        "drásticamente la detección de la clase minoritaria manteniendo ROC-AUC "
        "comparable."
    )
    lines.append("")

    lines.append("## 11. Recomendación")
    lines.append("")
    lines.append(
        f"Se recomienda llevar **{_label(decision['best_overall'])}** al siguiente "
        "ticket de optimización."
    )
    lines.append("")

    lines.append("## 12. Verificación de artefactos (#049)")
    lines.append("")
    lines.append("| Modelo | Existe | predict_proba | Predicción binaria |")
    lines.append("|---|---|---|---|")
    for key in CANDIDATE_ARTIFACTS:
        a = artifacts[key]
        lines.append(
            f"| {_label(key)} | {'sí' if a['exists'] else 'no'} | "
            f"{'sí' if a['has_predict_proba'] else 'no'} | "
            f"{'sí' if a['valid_binary'] else 'no'} |"
        )
    lines.append("")

    lines.append("## 13. Limitaciones")
    lines.append("")
    lines.append(
        "- La comparación se realiza re-ejecutando cada configuración en CV; los "
        "artefactos #049 quedan validados pero la selección usa out-of-fold."
    )
    lines.append(
        "- El dataset tiene fuerte desbalance; las métricas de la clase "
        "minoritaria tienen mayor varianza."
    )
    lines.append(
        "- DeBERTa-v3-small no se compara por ausencia de columna de texto."
    )
    lines.append(
        "- No se realiza tuning ni ensemble combinado en este ticket."
    )
    lines.append(
        "- Los resultados son descriptivos del modelo sobre los datos actuales; "
        "no implican rendimiento clínico ni relación causal."
    )
    return "\n".join(lines)


def compare_models(report_path: str = DEFAULT_REPORT) -> dict:
    """Run the full comparison and write the markdown report."""
    df = ev.load_dataset()
    results = compare_all(df)
    artifacts = artifact_check(df)
    decision = decide_best(results["results"])

    text = build_report(results, artifacts, decision)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    return {
        "report_path": report_path,
        "results": results["results"],
        "decision": decision,
        "artifacts": artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare trained ensemble candidate models (Issue #050)."
    )
    parser.add_argument(
        "--output", default=DEFAULT_REPORT, help="Output markdown report path."
    )
    args = parser.parse_args()

    result = compare_models(report_path=args.output)
    print("Comparación de modelos completada")
    print(f"  Informe: {args.output}")
    print("  Mejor modelo global:", result["decision"]["best_overall"])
    print("  Mejor Recall:", result["decision"]["best_recall"])
    print("  Mejor F1:", result["decision"]["best_f1"])
    print("  Mejor F1-macro:", result["decision"]["best_f1_macro"])
    print("  Mejor ROC-AUC:", result["decision"]["best_roc_auc"])


if __name__ == "__main__":
    main()