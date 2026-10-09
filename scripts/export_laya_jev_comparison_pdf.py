"""Generate a landscape PDF comparison with TypeSafe/Jev presented first."""

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

REPORT_PATH = Path("reports/laya_jev_complex_200.json")
PDF_PATH = Path("reports/laya_jev_complex_200.pdf")


def match_label(matched: bool) -> str:
    """Render an expected-agent comparison as a concise label."""
    return "Yes" if matched else "No"


def main() -> None:
    """Create the Jev-prioritized side-by-side routing comparison report."""
    report: dict[str, Any] = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    summary = report["summary"]
    jev = summary["jev"]
    laya = summary["laya"]
    total = summary["total_questions"]

    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.fontName = "Helvetica"
    body.fontSize = 6.25
    body.leading = 7.5
    header = ParagraphStyle(
        "Header",
        parent=body,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9.5,
        textColor=colors.white,
    )
    title = styles["Title"]
    title.fontName = "Helvetica-Bold"
    title.fontSize = 16
    section = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12
    )
    summary_text = ParagraphStyle("Summary", parent=body, fontSize=9, leading=12, spaceAfter=8)

    overview = (
        f"This report compares both models on the same {total} labeled customer questions. "
        f"TypeSafe/Jev matched {jev['matched_expected_agent']} / {total} "
        f"({jev['matched_expected_agent'] / total * 100:.1f}%) with an average classification "
        f"time of {jev['average_classification_time_ms']:.2f} ms. Laya matched "
        f"{laya['matched_expected_agent']} / {total} "
        f"({laya['matched_expected_agent'] / total * 100:.1f}%) with an average classification "
        f"time of {laya['average_classification_time_ms']:.2f} ms."
    )
    high_confidence_text = (
        f"High-confidence error review (score > 0.90): Jev had "
        f"<b>{jev['high_confidence_incorrect']} incorrect result(s) out of "
        f"{jev['score_above_0_9']} high-confidence results</b>; Laya had "
        f"{laya['high_confidence_incorrect']} incorrect result(s) out of "
        f"{laya['score_above_0_9']} high-confidence results. The two models selected the same "
        f"agent on {summary['models_agree']} / {total} questions."
    )
    metrics_rows = [
        [
            Paragraph("Model", header),
            Paragraph("Matched", header),
            Paragraph("Average time", header),
            Paragraph("Score &gt; 0.90", header),
            Paragraph("Incorrect at &gt; 0.90", header),
        ],
        [
            Paragraph("Jev", body),
            Paragraph(f"{jev['matched_expected_agent']} / {total}", body),
            Paragraph(f"{jev['average_classification_time_ms']:.2f} ms", body),
            Paragraph(str(jev["score_above_0_9"]), body),
            Paragraph(str(jev["high_confidence_incorrect"]), body),
        ],
        [
            Paragraph("Laya", body),
            Paragraph(f"{laya['matched_expected_agent']} / {total}", body),
            Paragraph(f"{laya['average_classification_time_ms']:.2f} ms", body),
            Paragraph(str(laya["score_above_0_9"]), body),
            Paragraph(str(laya["high_confidence_incorrect"]), body),
        ],
    ]
    metrics_table = LongTable(
        metrics_rows,
        colWidths=[0.85 * inch, 1.05 * inch, 1.45 * inch, 1.35 * inch, 1.65 * inch],
    )
    metrics_table.setStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#E7F6E7")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B7C9D6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )

    rows = [
        [
            Paragraph("expected agent", header),
            Paragraph("message", header),
            Paragraph("Jev matched", header),
            Paragraph("Jev agent", header),
            Paragraph("Jev score", header),
            Paragraph("Jev time (ms)", header),
            Paragraph("Laya matched", header),
            Paragraph("Laya agent", header),
            Paragraph("Laya score", header),
            Paragraph("Laya time (ms)", header),
        ]
    ]
    for record in report["responses"]:
        rows.append(
            [
                Paragraph(record["expected_agent"], body),
                Paragraph(record["message"], body),
                Paragraph(match_label(record["jev_matched"]), body),
                Paragraph(record["jev"]["agent"], body),
                Paragraph(f"{record['jev']['score']:.4f}", body),
                Paragraph(f"{record['jev']['classification_time_ms']:.2f}", body),
                Paragraph(match_label(record["laya_matched"]), body),
                Paragraph(record["laya"]["agent"], body),
                Paragraph(f"{record['laya']['score']:.4f}", body),
                Paragraph(f"{record['laya']['classification_time_ms']:.2f}", body),
            ]
        )

    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(letter),
        leftMargin=0.275 * inch,
        rightMargin=0.275 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
        title="Jev and Laya Routing Comparison",
    )
    table = LongTable(
        rows,
        colWidths=[
            1.02 * inch,
            2.05 * inch,
            0.56 * inch,
            0.92 * inch,
            0.56 * inch,
            0.67 * inch,
            0.58 * inch,
            0.92 * inch,
            0.56 * inch,
            0.67 * inch,
        ],
        repeatRows=1,
    )
    table.setStyle(
        [
            ("BACKGROUND", (0, 0), (5, 0), colors.HexColor("#1F4E78")),
            ("BACKGROUND", (6, 0), (-1, 0), colors.HexColor("#606060")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B7C9D6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF5F9")]),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (4, 1), (5, -1), "RIGHT"),
            ("ALIGN", (6, 1), (6, -1), "CENTER"),
            ("ALIGN", (8, 1), (9, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    for row_number, record in enumerate(report["responses"], start=1):
        if not record["jev_matched"]:
            table.setStyle(
                [("BACKGROUND", (0, row_number), (5, row_number), colors.HexColor("#FDECEC"))]
            )
        elif record["jev"]["score"] > 0.9:
            table.setStyle(
                [("BACKGROUND", (0, row_number), (5, row_number), colors.HexColor("#E7F6E7"))]
            )
        if not record["laya_matched"]:
            table.setStyle(
                [("BACKGROUND", (6, row_number), (-1, row_number), colors.HexColor("#FDECEC"))]
            )

    document.build(
        [
            Paragraph("TypeSafe/Jev and Laya Routing Comparison", title),
            Spacer(1, 0.16 * inch),
            Paragraph("Executive Summary", section),
            Paragraph(overview, summary_text),
            Paragraph("High-Confidence Error Review", section),
            Paragraph(high_confidence_text, summary_text),
            metrics_table,
            PageBreak(),
            Paragraph("Question-by-Question Results", title),
            Spacer(1, 0.16 * inch),
            table,
        ]
    )
    print(f"Comparison PDF written to {PDF_PATH}")


if __name__ == "__main__":
    main()
