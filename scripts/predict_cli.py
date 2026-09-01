"""Interactive command-line interface for F5 RiskAI stroke prediction (Issue #022).

This CLI asks the user for a patient's data, validates it, loads the baseline
Pipeline artifact (preprocessing + LogisticRegression) trained in Issue #017,
and shows the predicted class together with the probability of ``stroke=1``.

Design notes:

* Interaction (``input``/``print``) is separated from prediction logic so that
  tests can call pure functions (e.g. ``validate_input``,
  ``build_dataframe``, ``predict``) without an interactive session.
* It reuses the existing preprocessing inside the loaded Pipeline (no parallel
  pipeline is rebuilt) and the feature definitions from
  ``scripts/preprocessing.py``.
* The model is loaded as-is; it is never re-trained, re-fit, balanced, tuned
  or re-thresholded. The raw dataset is never modified.

Run from the repository root::

    python scripts/predict_cli.py
"""

from __future__ import annotations

import os
from typing import Callable

import joblib
import pandas as pd

import evaluate_baseline as ev
from preprocessing import (
    ALL_FEATURE_COLUMNS,
    RAW_DATA_PATH,
)

DEFAULT_MODEL_PATH = ev.DEFAULT_MODEL_PATH
POSITIVE_LABEL = 1  # stroke = 1

# Validation ranges. These are input sanity checks, not medical rules.
AGE_MIN, AGE_MAX = 0, 130
BMI_MIN, BMI_MAX = 5, 100

CATEGORICAL_VALUES: dict[str, list[str]] = {
    "gender": ["Female", "Male"],
    "ever_married": ["No", "Yes"],
    "work_type": ["Govt_job", "Private", "Self-employed", "children"],
    "Residence_type": ["Rural", "Urban"],
    "smoking_status": ["Unknown", "formerly smoked", "never smoked", "smokes"],
}


class ModelUnavailableError(FileNotFoundError):
    """Raised when the baseline artifact is missing or unusable."""


def load_model(path: str = DEFAULT_MODEL_PATH):
    """Load the trained Pipeline artifact, raising a clear error if missing."""
    if not os.path.exists(path):
        raise ModelUnavailableError(
            f"No existe el artefacto del modelo en '{path}'. Ejecuta antes "
            f"'scripts/train_baseline.py' (Issue #017)."
        )
    pipeline = joblib.load(path)
    if "model" not in getattr(pipeline, "named_steps", {}):
        raise ValueError("El artefacto no es un Pipeline con un paso 'model'.")
    return pipeline


def validate_input(data: dict[str, str]) -> dict:
    """Validate raw string inputs and return typed values or raise ValueError.

    Raises ValueError with a user-friendly Spanish message on the first invalid
    field. Returns a dict mapping feature column names to typed Python values.
    """
    errors: dict[str, str] = {}

    # Binary numeric fields.
    for key in ("hypertension", "heart_disease"):
        if str(data.get(key, "")).strip() not in {"0", "1"}:
            errors[key] = f"'{data.get(key)}' no es válido. Introduzca 0 o 1."

    # Continuous numeric fields with reasonable ranges.
    if not _is_number(data.get("age")):
        errors["age"] = "Valor no válido. Introduzca una edad numérica."
    else:
        age = float(data["age"])
        if not AGE_MIN <= age <= AGE_MAX:
            errors["age"] = f"La edad debe estar entre {AGE_MIN} y {AGE_MAX}."

    if not _is_number(data.get("avg_glucose_level")):
        errors["avg_glucose_level"] = (
            "Valor no válido. Introduzca un nivel medio de glucosa numérico."
        )
    else:
        glucose = float(data["avg_glucose_level"])
        if glucose < 0:
            errors["avg_glucose_level"] = "El nivel de glucosa no puede ser negativo."

    if not _is_number(data.get("bmi")):
        errors["bmi"] = "Valor no válido. Introduzca un BMI numérico."
    else:
        bmi = float(data["bmi"])
        if not BMI_MIN <= bmi <= BMI_MAX:
            errors["bmi"] = f"El BMI debe estar entre {BMI_MIN} y {BMI_MAX}."

    # Categorical fields against known categories.
    for key, values in CATEGORICAL_VALUES.items():
        raw = str(data.get(key, "")).strip()
        if raw not in values:
            errors[key] = (
                f"'{raw}' no es válido. Valores permitidos: {', '.join(values)}."
            )

    if errors:
        raise ValueError(_format_errors(errors))

    return {
        "hypertension": int(data["hypertension"]),
        "heart_disease": int(data["heart_disease"]),
        "age": float(data["age"]),
        "avg_glucose_level": float(data["avg_glucose_level"]),
        "bmi": float(data["bmi"]),
        "gender": str(data["gender"]),
        "ever_married": str(data["ever_married"]),
        "work_type": str(data["work_type"]),
        "Residence_type": str(data["Residence_type"]),
        "smoking_status": str(data["smoking_status"]),
    }


def _is_number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _format_errors(errors: dict[str, str]) -> str:
    return "\n".join(f"- {field}: {msg}" for field, msg in errors.items())


def build_dataframe(values: dict) -> pd.DataFrame:
    """Build a single-row DataFrame with exactly the expected feature columns."""
    if set(values) != set(ALL_FEATURE_COLUMNS):
        raise ValueError(
            "La entrada debe contener exactamente las features esperadas por el pipeline."
        )
    return pd.DataFrame([{col: values[col] for col in ALL_FEATURE_COLUMNS}])


def predict(pipeline, data: dict) -> dict:
    """Return the predicted class and the probability of ``stroke=1``.

    ``data`` must be a validated dict produced by ``validate_input`` (or typed
    values with the expected keys).
    """
    df = build_dataframe(data)
    pred = int(pipeline.predict(df)[0])
    proba = float(pipeline.predict_proba(df)[0][POSITIVE_LABEL])
    return {"prediction": pred, "probability": proba}


def _prompt(prompt_text: str, convert: Callable[[str], str] = str) -> str:
    """Read user input in an interactive session."""
    return convert(input(prompt_text).strip())


def run_interactive(
    model_path: str = DEFAULT_MODEL_PATH, file_cfg: dict | None = None
) -> dict:
    """Run the interactive CLI end-to-end and return the prediction dict.

    ``file_cfg`` is an optional mapping of field name -> pre-supplied value used
    only for tests; it should never be set in real interactive use.
    """
    try:
        pipeline = load_model(model_path)
    except ModelUnavailableError as exc:
        print(f"Error: {exc}")
        print("No se creará un modelo alternativo. Entrena antes el modelo (Issue #017).")
        raise SystemExit(1)

    print("F5 RiskAI — Stroke Risk Prediction")
    print("[Introduzca los datos del paciente; se validarán antes de predecir.]")
    print()

    fields = [
        ("gender", "Gender [Male/Female]: "),
        ("age", "Age [number, e.g. 45]: "),
        ("hypertension", "Hypertension [0/1]: "),
        ("heart_disease", "Heart disease [0/1]: "),
        ("ever_married", "Ever married [Yes/No]: "),
        ("work_type", "Work type [Govt_job/Private/Self-employed/children]: "),
        ("Residence_type", "Residence type [Rural/Urban]: "),
        ("avg_glucose_level", "Average glucose level [number, e.g. 100]: "),
        ("bmi", "BMI [number, e.g. 25]: "),
        ("smoking_status", "Smoking status [never smoked/formerly smoked/smokes/Unknown]: "),
    ]

    raw: dict[str, str] = {}
    for key, text in fields:
        raw[key] = file_cfg.get(key, "") if file_cfg else _prompt(text)

    # Keep asking until all values are valid.
    while True:
        try:
            values = validate_input(raw)
            break
        except ValueError as exc:
            print("Valores no válidos. Corríjalos:")
            print(exc)
            for key, text in fields:
                raw[key] = file_cfg.get(key, "") if file_cfg else _prompt(text)

    result = predict(pipeline, values)
    print_result(result)
    return result


def print_result(result: dict) -> None:
    """Print a clear, cautious result block to the user."""
    prediction = int(result["prediction"])
    proba = float(result["probability"])
    label = "Possible positive class" if prediction == 1 else "Negative class"

    print()
    print("-----------------------------------")
    print("F5 RiskAI — Prediction Result")
    print("-----------------------------------")
    print(f"Prediction: {prediction}")
    print(f"Prediction: {label}")
    print(f"Probability of stroke: {proba * 100:.1f}%")
    print()
    print("This prototype is for predictive analysis and is not a medical diagnosis.")
    print("-----------------------------------")


if __name__ == "__main__":
    run_interactive()