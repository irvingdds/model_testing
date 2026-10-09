"""Generate a PDF report for TypeSafe/Jev routing results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

REPORT_PATH = Path("reports/laya_jev_comparison.json")
PDF_PATH = Path("reports/laya_jev_comparison.pdf")


def match_label(matched: bool) -> str:
    """Present a Boolean match result in the report table."""
    return "Yes" if matched else "No"


def main() -> None:
    """Create an executive summary and row-by-row Jev evaluation PDF."""
    report: dict[str, Any] = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    summary = report["summary"]
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.fontName = "Helvetica"
    body.fontSize = 6.5
    body.leading = 8
    header = ParagraphStyle(
        "Header",
        parent=body,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
    )
    title = styles["Title"]
    title.fontName = "Helvetica-Bold"
    title.fontSize = 16
    subheading = ParagraphStyle(
        "Subheading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12
    )
    summary_text = ParagraphStyle("Summary", parent=body, fontSize=9, leading=12, spaceAfter=8)

    jev = summary["jev"]
    total = summary["total_questions"]
    overview = (
        f"This evaluation tested TypeSafe/Jev on {total} customer questions and expected "
        "routing labels. "
        f"TypeSafe/Jev matched {jev['matched_expected_agent']} / {total} "
        f"({jev['matched_expected_agent'] / total * 100:.1f}%) with an average classification "
        f"time of {jev['average_classification_time_ms']:.2f} ms. The first request was run "
        "as a warm-up and excluded from the evaluation and timing metrics."
    )
    risk_text = (
        f"Jev returned a score above 0.90 for {jev['score_above_0_9']} / {total} questions. "
        f"Of those high-confidence results, {jev['high_confidence_incorrect']} were incorrect. "
        "The detailed table includes only these high-confidence routings. High-confidence errors "
        "should be prioritized when refining agent definitions or routing rules."
    )
    high_confidence_records = [
        record for record in report["responses"] if record["jev"]["score"] > 0.9
    ]

    rows = [
        [
            Paragraph("Matched", header),
            Paragraph("message", header),
            Paragraph("expected agent", header),
            Paragraph("Jev agent", header),
            Paragraph("Jev score", header),
            Paragraph("Jev time (ms)", header),
        ]
    ]
    for record in high_confidence_records:
        jev_match = match_label(record["jev_matched"])
        rows.append(
            [
                Paragraph(jev_match, body),
                Paragraph(record["message"], body),
                Paragraph(record["expected_agent"], body),
                Paragraph(record["jev"]["agent"], body),
                Paragraph(f"{record['jev']['score']:.4f}", body),
                Paragraph(f"{record['jev']['classification_time_ms']:.2f}", body),
            ]
        )

    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(letter),
        leftMargin=0.275 * inch,
        rightMargin=0.275 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
        title="TypeSafe/Jev Routing Evaluation",
    )
    table = LongTable(
        rows,
        colWidths=[
            0.85 * inch,
            3.9 * inch,
            1.85 * inch,
            1.85 * inch,
            0.9 * inch,
            1.0 * inch,
        ],
        repeatRows=1,
    )
    table.setStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B7C9D6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF5F9")]),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (4, 1), (5, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    for row_number, record in enumerate(high_confidence_records, start=1):
        if record["jev_matched"]:
            table.setStyle(
                [("BACKGROUND", (0, row_number), (-1, row_number), colors.HexColor("#E7F6E7"))]
            )
        else:
            table.setStyle(
                [("BACKGROUND", (0, row_number), (-1, row_number), colors.HexColor("#FDECEC"))]
            )

    document.build(
        [
            Paragraph("TypeSafe/Jev Routing Evaluation", title),
            Spacer(1, 0.16 * inch),
            Paragraph("Overall Analysis", subheading),
            Paragraph(overview, summary_text),
            Paragraph("High-Confidence Error Review", subheading),
            Paragraph(risk_text, summary_text),
            PageBreak(),
            Paragraph("High-Confidence Routing Results (Score > 0.90)", title),
            Spacer(1, 0.16 * inch),
            table,
        ]
    )
    print(f"Comparison PDF written to {PDF_PATH}")


if __name__ == "__main__":
    main()
