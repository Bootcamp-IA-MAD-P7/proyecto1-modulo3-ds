"""PDF report generation for a stored assessment (ReportLab).

The PDF is built exclusively from REAL persisted data (patient + assessment);
no individual metric is invented. The document follows the app aesthetic
(white / light gray / soft gold) and includes the mandatory support-tool
disclaimer.

Supports i18n: a ``locale`` parameter (``"es"`` | ``"en"``) controls every
visible text in the PDF. Clinical values from the database are always
displayed as-is; only labels, headers, booleans and units are translated.

Endpoint: ``GET /assessments/{assessment_id}/report`` (see ``backend/main.py``).
"""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.models import Assessment, Patient

# Soft-gold accent matching the UI palette.
GOLD = colors.HexColor("#C9A227")
INK = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748b")
HAIRLINE = colors.HexColor("#E2E8F0")

# ── PDF i18n ────────────────────────────────────────────────────────────────
# Translation dictionary for every visible string in the PDF report.
# Clinical *values* (e.g. "Male", "Private", "never smoked") are always
# kept as-is from the database; only labels, booleans and units are translated.

_TEXTS: dict[str, dict[str, str]] = {
    "es": {
        "subtitle": "Informe de evaluación de riesgo de ictus",
        "docTitle": "F5 RiskAI — Informe de evaluación",
        "patientInfo": "Información del paciente",
        "result": "Resultado",
        "model": "Modelo",
        "modelOptimized": "Modelo final optimizado",
        "estProbability": "Probabilidad estimada:",
        "riskLevel": "Nivel de riesgo:",
        "prediction": "Predicción:",
        "assessDate": "Fecha de evaluación:",
        "disclaimer": (
            "Esta herramienta es un sistema de apoyo basado en Machine Learning "
            "y no constituye un diagnóstico médico."
        ),
        "yes": "Sí",
        "no": "No",
        "years": "años",
        "riskLow": "BAJO",
        "riskMedium": "MEDIO",
        "riskHigh": "ALTO",
        "predNoRisk": "Sin indicios de riesgo",
        "predRisk": "Riesgo estimado",
        # Patient field labels
        "fGender": "Género",
        "fAge": "Edad",
        "fHypertension": "Hipertensión",
        "fHeartDisease": "Enfermedad cardíaca",
        "fMarried": "Estado civil",
        "fWorkType": "Tipo de trabajo",
        "fResidence": "Residencia",
        "fGlucose": "Nivel de glucosa",
        "fBmi": "IMC",
        "fSmoking": "Estado de tabaquismo",
    },
    "en": {
        "subtitle": "Stroke Risk Assessment Report",
        "docTitle": "F5 RiskAI — Assessment Report",
        "patientInfo": "Patient Information",
        "result": "Result",
        "model": "Model",
        "modelOptimized": "Optimized final model",
        "estProbability": "Estimated probability:",
        "riskLevel": "Risk level:",
        "prediction": "Prediction:",
        "assessDate": "Assessment date:",
        "disclaimer": (
            "This tool is a Machine Learning-based support system "
            "and does not constitute a medical diagnosis."
        ),
        "yes": "Yes",
        "no": "No",
        "years": "years",
        "riskLow": "LOW",
        "riskMedium": "MEDIUM",
        "riskHigh": "HIGH",
        "predNoRisk": "No elevated risk detected",
        "predRisk": "Risk estimated",
        # Patient field labels
        "fGender": "Gender",
        "fAge": "Age",
        "fHypertension": "Hypertension",
        "fHeartDisease": "Heart disease",
        "fMarried": "Marital status",
        "fWorkType": "Work type",
        "fResidence": "Residence",
        "fGlucose": "Glucose level",
        "fBmi": "BMI",
        "fSmoking": "Smoking status",
    },
}

_RISK_LABELS = {"low": "riskLow", "medium": "riskMedium", "high": "riskHigh"}
_PREDICTION_LABELS = {0: "predNoRisk", 1: "predRisk"}

# ── Categorical value translations (PDF i18n) ───────────────────────────────
# Centralised map of the REAL dataset values (as stored by POST /predict) to
# their Spanish equivalents. English reports keep the exact raw values
# (Male, Self-employed, formerly smoked...). Values not present in the map
# pass through untouched. Unknown passthrough keeps reports honest.
_CATEGORY_ES: dict[str, dict[str, str]] = {
    "gender": {
        "Male": "Hombre",
        "Female": "Mujer",
        "Other": "Otro",
    },
    "ever_married": {
        "Yes": "Sí",
        "No": "No",
    },
    "work_type": {
        "Private": "Privado",
        "Self-employed": "Autónomo",
        "Govt_job": "Empleo público",
        "children": "Niños",
        "Never_worked": "Nunca ha trabajado",
    },
    "residence_type": {
        "Urban": "Urbano",
        "Rural": "Rural",
    },
    "smoking_status": {
        "formerly smoked": "Exfumador/a",
        "never smoked": "Nunca ha fumado",
        "smokes": "Fumador/a",
        "Unknown": "Desconocido",
    },
}


def _translate_category(field: str, value: str, locale: str) -> str:
    """Translate one categorical *value* for the Spanish PDF locale.

    For ``locale='en'`` the exact dataset value is returned unchanged.
    """
    if locale != "es":
        return value
    return _CATEGORY_ES.get(field, {}).get(value, value)


def _style(*, size: float, color=INK, bold: bool = False, center: bool = False) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"st{size}{int(bold)}{int(center)}",
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        textColor=color,
        leading=size * 1.35,
        alignment=TA_CENTER if center else 0,
    )


def _kv_rows(
    patient: Patient,
    texts: dict[str, str],
    locale: str = "es",
) -> list[tuple[str, str]]:
    """Patient information block, ordered as the report spec requires.

    Categorical *values* (gender, marital status, work type, residence,
    smoking status) are translated only when ``locale='es'``; English keeps
    the raw dataset values.
    """
    yn = lambda v: texts["yes"] if v == 1 else texts["no"]  # noqa: E731
    cat = lambda field, value: _translate_category(field, value, locale)  # noqa: E731
    return [
        (texts["fGender"], cat("gender", patient.gender)),
        (texts["fAge"], f"{patient.age:g} {texts['years']}"),
        (texts["fHypertension"], yn(patient.hypertension)),
        (texts["fHeartDisease"], yn(patient.heart_disease)),
        (texts["fMarried"], cat("ever_married", patient.ever_married)),
        (texts["fWorkType"], cat("work_type", patient.work_type)),
        (texts["fResidence"], cat("residence_type", patient.residence_type)),
        (texts["fGlucose"], f"{patient.avg_glucose_level:g}"),
        (texts["fBmi"], f"{patient.bmi:g}"),
        (texts["fSmoking"], cat("smoking_status", patient.smoking_status)),
    ]


def _section_header(text: str) -> Paragraph:
    return Paragraph(
        f'<font color="#C9A227"><b>{text}</b></font>',
        _style(size=11.5, bold=True),
    )


def generate_assessment_pdf(
    assessment: Assessment,
    patient: Patient,
    *,
    locale: str = "es",
) -> bytes:
    """Build the PDF bytes for one assessment (no side effects)."""
    texts = _TEXTS.get(locale, _TEXTS["es"])
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=f"{texts['docTitle']} ({assessment.id})",
        author="F5 RiskAI",
    )

    h1 = _style(size=19, bold=True, center=True)
    h2 = _style(size=11.5, color=MUTED, center=True)
    label_style = _style(size=10.5, color=MUTED)
    value_style = _style(size=10.5, bold=True)
    risk_value = _style(size=15, bold=True, color=GOLD, center=True)

    story: list = []

    # Header
    story.append(Paragraph("F5 RISKAI", h1))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(texts["subtitle"], h2))
    story.append(Spacer(1, 3 * mm))
    story.append(
        Table(
            [["", ""]],
            colWidths=[doc.width / 2, doc.width / 2],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, 0), (1, 0), 0.8, GOLD),
                ]
            ),
        )
    )
    story.append(Spacer(1, 6 * mm))

    # Patient information
    story.append(_section_header(texts["patientInfo"]))
    story.append(Spacer(1, 2 * mm))
    rows = [[Paragraph(k, label_style), Paragraph(v, value_style)] for k, v in _kv_rows(patient, texts, locale)]
    info_table = Table(rows, colWidths=[doc.width * 0.38, doc.width * 0.62])
    info_table.setStyle(
        TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, HAIRLINE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 6 * mm))

    # Result
    story.append(_section_header(texts["result"]))
    story.append(Spacer(1, 3 * mm))
    proba_pct = f"{assessment.probability * 100:.2f}".rstrip("0").rstrip(".")
    story.append(Paragraph(f"{texts['estProbability']}  {proba_pct} %", _style(size=13)))
    story.append(Spacer(1, 1.5 * mm))
    risk_key = _RISK_LABELS.get(assessment.risk_level, assessment.risk_level)
    risk_label = texts.get(risk_key, str(assessment.risk_level))
    story.append(Paragraph(f"{texts['riskLevel']}  {risk_label}", risk_value))
    story.append(Spacer(1, 1.5 * mm))
    pred_key = _PREDICTION_LABELS.get(assessment.prediction)
    pred_label = texts.get(pred_key, str(assessment.prediction)) if pred_key else str(assessment.prediction)
    story.append(Paragraph(f"{texts['prediction']}  {pred_label}", _style(size=13)))
    story.append(Spacer(1, 6 * mm))

    # Model
    story.append(_section_header(texts["model"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(assessment.model_name, _style(size=13, bold=True)))
    story.append(Paragraph(texts["modelOptimized"], _style(size=10.5, color=MUTED)))
    story.append(Spacer(1, 6 * mm))

    # Date
    created = assessment.created_at
    if created.tzinfo is not None:
        created = created.astimezone()
    story.append(Paragraph(f"{texts['assessDate']}  {created:%d/%m/%Y %H:%M}", _style(size=10.5)))

    doc.build(story, onFirstPage=_footer(locale))
    return buf.getvalue()


def _footer(locale: str = "es"):
    """Return a page-footer callback that renders disclaimer · page number."""
    texts = _TEXTS.get(locale, _TEXTS["es"])

    def _draw(canvas, _doc) -> None:
        canvas.saveState()
        width = _doc.pagesize[0]
        y = 16 * mm
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(width / 2, y, texts["disclaimer"])
        # Optional: draw a gold rule above the disclaimer.
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.8)
        canvas.line(width * 0.2, y + 4 * mm, width * 0.8, y + 4 * mm)
        canvas.restoreState()

    return _draw