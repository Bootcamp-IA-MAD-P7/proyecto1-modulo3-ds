"""Unit tests for PDF report i18n (Issue: UI/UX refinements).

Validates WITHOUT any database that:

* categorical *values* (gender, marital status, work type, residence,
  smoking status) are translated ONLY when ``locale='es'``,
* English reports keep the exact raw dataset values,
* the generated PDF bytes are valid and differ between locales.

Run from the repository root:

    python -m unittest tests.test_reports -v
"""

from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone

from backend.models import Assessment, Patient
from backend.reports import (
    _TEXTS,
    _kv_rows,
    _translate_category,
    generate_assessment_pdf,
)

PATIENT_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ASSESSMENT_UUID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _sample_patient() -> Patient:
    return Patient(
        id=PATIENT_UUID,
        created_at=datetime(2026, 9, 8, 12, 8, tzinfo=timezone.utc),
        gender="Male",
        age=40,
        hypertension=1,
        heart_disease=0,
        ever_married="Yes",
        work_type="Self-employed",
        residence_type="Urban",
        avg_glucose_level=90.0,
        bmi=30.0,
        smoking_status="formerly smoked",
    )


def _sample_assessment() -> Assessment:
    return Assessment(
        id=ASSESSMENT_UUID,
        patient_id=PATIENT_UUID,
        created_at=datetime(2026, 9, 8, 12, 8, tzinfo=timezone.utc),
        prediction=0,
        probability=0.15358736951402552,
        risk_level="low",
        model_name="Logistic Regression + RandomOverSampler",
        model_version="final-tuned",
    )


class TranslateCategoryTests(unittest.TestCase):
    """The single centralised categorical mapping used by the PDF."""

    def test_spanish_translates_known_values(self):
        cases = [
            ("gender", "Male", "Hombre"),
            ("gender", "Female", "Mujer"),
            ("gender", "Other", "Otro"),
            ("ever_married", "Yes", "Sí"),
            ("ever_married", "No", "No"),
            ("work_type", "Private", "Privado"),
            ("work_type", "Self-employed", "Autónomo"),
            ("work_type", "Govt_job", "Empleo público"),
            ("work_type", "children", "Niños"),
            ("work_type", "Never_worked", "Nunca ha trabajado"),
            ("residence_type", "Urban", "Urbano"),
            ("residence_type", "Rural", "Rural"),
            ("smoking_status", "formerly smoked", "Exfumador/a"),
            ("smoking_status", "never smoked", "Nunca ha fumado"),
            ("smoking_status", "smokes", "Fumador/a"),
            ("smoking_status", "Unknown", "Desconocido"),
        ]
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                actual = _translate_category(field, value, "es")
                self.assertEqual(actual, expected)

    def test_unknown_values_pass_through_unchanged(self):
        self.assertEqual(_translate_category("gender", "NonBinary", "es"), "NonBinary")
        self.assertEqual(_translate_category("work_type", "NEVER_HEARD", "es"), "NEVER_HEARD")

    def test_english_keeps_raw_dataset_values(self):
        cases = [
            ("gender", "Male"),
            ("ever_married", "Yes"),
            ("work_type", "Self-employed"),
            ("residence_type", "Urban"),
            ("smoking_status", "formerly smoked"),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.assertEqual(_translate_category(field, value, "en"), value)


class KvRowsLocaleTests(unittest.TestCase):
    """The patient information block respects the report language."""

    def setUp(self):
        self.patient = _sample_patient()

    def test_spanish_translates_labels_and_categorical_values(self):
        rows = dict(_kv_rows(self.patient, _TEXTS["es"], "es"))
        self.assertEqual(rows["Género"], "Hombre")
        self.assertEqual(rows["Edad"], "40 años")
        self.assertEqual(rows["Hipertensión"], "Sí")
        self.assertEqual(rows["Enfermedad cardíaca"], "No")
        self.assertEqual(rows["Estado civil"], "Sí")
        self.assertEqual(rows["Tipo de trabajo"], "Autónomo")
        self.assertEqual(rows["Residencia"], "Urbano")
        self.assertEqual(rows["Nivel de glucosa"], "90")
        self.assertEqual(rows["IMC"], "30")
        self.assertEqual(rows["Estado de tabaquismo"], "Exfumador/a")

    def test_english_keeps_labels_and_values_in_english(self):
        rows = dict(_kv_rows(self.patient, _TEXTS["en"], "en"))
        self.assertEqual(rows["Gender"], "Male")
        self.assertEqual(rows["Age"], "40 years")
        self.assertEqual(rows["Hypertension"], "Yes")
        self.assertEqual(rows["Heart disease"], "No")
        self.assertEqual(rows["Marital status"], "Yes")
        self.assertEqual(rows["Work type"], "Self-employed")
        self.assertEqual(rows["Residence"], "Urban")
        self.assertEqual(rows["Glucose level"], "90")
        self.assertEqual(rows["BMI"], "30")
        self.assertEqual(rows["Smoking status"], "formerly smoked")

    def test_default_locale_is_spanish(self):
        rows = dict(_kv_rows(self.patient, _TEXTS["es"]))
        self.assertEqual(rows["Género"], "Hombre")
        self.assertEqual(rows["Estado de tabaquismo"], "Exfumador/a")


class PdfPdfLocaleTests(unittest.TestCase):
    """The generated PDF bytes are valid and respect the locale."""

    def _render(self, locale):
        return generate_assessment_pdf(
            _sample_assessment(),
            _sample_patient(),
            locale=locale,
        )

    def test_pdf_bytes_are_valid_reportlab_output(self):
        data = self._render("es")
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)

    def test_es_and_en_pdfs_differ(self):
        es = self._render("es")
        en = self._render("en")
        self.assertNotEqual(es, en)


if __name__ == "__main__":
    unittest.main()