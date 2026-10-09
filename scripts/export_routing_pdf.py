"""Export the 100-question Laya routing evaluation as a PDF table."""

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

REPORT_PATH = Path("reports/routing_evaluation.json")
PDF_PATH = Path("reports/routing_evaluation.pdf")


def format_match(is_matched: bool) -> str:
    """Return a clear result label for the evaluation comparison."""
    return "Yes" if is_matched else "No"


def main() -> None:
    """Generate a paginated PDF table in the requested column order."""
    report: dict[str, Any] = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    styles = getSampleStyleSheet()
    body_style = styles["BodyText"]
    body_style.fontName = "Helvetica"
    body_style.fontSize = 7
    body_style.leading = 8.5
    header_style = ParagraphStyle(
        "TableHeader",
        parent=body_style,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=10.5,
        textColor=colors.white,
    )
    heading_style = styles["Title"]
    heading_style.fontName = "Helvetica-Bold"
    heading_style.fontSize = 16
    summary_heading_style = ParagraphStyle(
        "SummaryHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceAfter=8,
    )
    summary_style = ParagraphStyle(
        "SummaryText",
        parent=body_style,
        fontSize=9,
        leading=12,
        spaceAfter=8,
    )

    table_rows = [
        [
            Paragraph("Matched", header_style),
            Paragraph("message", header_style),
            Paragraph("agent", header_style),
            Paragraph("score", header_style),
            Paragraph("time (ms)", header_style),
            Paragraph("agent suggested after analysis", header_style),
        ]
    ]
    for record in report["responses"]:
        response_summary = record["resp"]
        agent = record["predicted_agent"]
        table_rows.append(
            [
                Paragraph(format_match(record["matched_expected_agent"]), body_style),
                Paragraph(response_summary["message"], body_style),
                Paragraph(agent, body_style),
                Paragraph(f"{response_summary[agent]:.4f}", body_style),
                Paragraph(f"{response_summary['classification_time_ms']:.2f}", body_style),
                Paragraph(record["expected_agent"], body_style),
            ]
        )

    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(letter),
        leftMargin=0.275 * inch,
        rightMargin=0.275 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
        title="Laya Routing Evaluation",
    )
    table = LongTable(
        table_rows,
        colWidths=[
            0.99 * inch,
            3.72 * inch,
            1.72 * inch,
            0.74 * inch,
            0.85 * inch,
            2.43 * inch,
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
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
    for row_number, record in enumerate(report["responses"], start=1):
        if not record["matched_expected_agent"]:
            table.setStyle(
                [("BACKGROUND", (0, row_number), (-1, row_number), colors.HexColor("#FDECEC"))]
            )
    summary = report["summary"]
    total_questions = summary["total_questions"]
    matched_questions = summary["matched_expected_agent"]
    match_percentage = matched_questions / total_questions * 100
    high_confidence_mismatches = [
        record
        for record in report["responses"]
        if not record["matched_expected_agent"]
        and record["resp"][record["predicted_agent"]] > 0.9
    ]
    analysis_text = (
        f"Results: {matched_questions} / {total_questions} matched the expected agent "
        f"({match_percentage:.1f}%), with an average classification time of "
        f"{summary['average_classification_time_ms']:.2f} ms. Unmatched table rows are "
        "highlighted light red."
    )
    high_confidence_text = (
        f"Laya made {len(high_confidence_mismatches)} incorrect prediction(s) with confidence "
        "greater than 0.90. These cases deserve priority review because the model selected an "
        "unexpected route with high certainty."
    )
    high_confidence_rows = [
        [
            Paragraph("<b>message</b>", body_style),
            Paragraph("<b>Laya agent</b>", body_style),
            Paragraph("<b>expected agent</b>", body_style),
            Paragraph("<b>confidence</b>", body_style),
        ]
    ]
    for record in high_confidence_mismatches:
        response_summary = record["resp"]
        predicted_agent = record["predicted_agent"]
        high_confidence_rows.append(
            [
                Paragraph(response_summary["message"], body_style),
                Paragraph(predicted_agent, body_style),
                Paragraph(record["expected_agent"], body_style),
                Paragraph(f"{response_summary[predicted_agent]:.4f}", body_style),
            ]
        )
    high_confidence_table = LongTable(
        high_confidence_rows,
        colWidths=[3.4 * inch, 1.6 * inch, 1.6 * inch, 0.8 * inch],
        repeatRows=1,
    )
    high_confidence_table.setStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A1F1F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5A6A6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FDECEC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
    document.build(
        [
            Paragraph("Laya Routing Evaluation: Executive Summary", heading_style),
            Spacer(1, 0.16 * inch),
            Paragraph("Overall Analysis", summary_heading_style),
            Paragraph(analysis_text, summary_style),
            Paragraph("Incorrect High-Confidence Predictions", summary_heading_style),
            Paragraph(high_confidence_text, summary_style),
            high_confidence_table,
            PageBreak(),
            Paragraph("Laya Routing Evaluation Results", heading_style),
            Spacer(1, 0.16 * inch),
            table,
        ]
    )
    print(f"PDF report written to {PDF_PATH}")


if __name__ == "__main__":
    main()