"""Executive PDF health report generator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from flowsentinel.config import OUTPUTS_DIR, PDF_COMPANY_NAME, PDF_MAX_EXCEPTIONS, PDF_REPORT_TITLE


logger = logging.getLogger(__name__)

NAVY = colors.HexColor("#0D1B2A")
TEAL = colors.HexColor("#1B998B")
AMBER = colors.HexColor("#FFBF00")
RED = colors.HexColor("#E84855")
WHITE = colors.white
LIGHT = colors.HexColor("#F4F6F8")
MID = colors.HexColor("#CDD5DF")


def _grade_color(score: float):
    if score >= 90:
        return TEAL
    if score >= 75:
        return colors.HexColor("#2ECC71")
    if score >= 60:
        return AMBER
    return RED


class PDFReportGenerator:
    """Build a one-page operational summary PDF."""

    def __init__(self, output_dir: Path = OUTPUTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, score_record: dict, exceptions: list[dict], anomaly_count: int, run_date: str | None = None) -> Path:
        report_date = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = self.output_dir / f"flowsentinel_report_{report_date}.pdf"

        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        story = []

        header_style = ParagraphStyle(
            "Header",
            parent=styles["Normal"],
            fontSize=22,
            textColor=NAVY,
            fontName="Helvetica-Bold",
            spaceAfter=2 * mm,
        )
        sub_style = ParagraphStyle(
            "Sub",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#6B7280"),
        )

        story.append(Paragraph(PDF_REPORT_TITLE, header_style))
        story.append(
            Paragraph(
                f"{PDF_COMPANY_NAME} · Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                sub_style,
            )
        )
        story.append(HRFlowable(width="100%", thickness=1, color=MID, spaceAfter=6 * mm))

        composite = float(score_record.get("composite_score", 0))
        score_table = Table(
            [
                ["METRIC", "VALUE", "WEIGHT"],
                ["Composite Health Score", f"{composite:.1f} / 100", "Weighted composite"],
                ["Completeness", f"{score_record.get('completeness', 0):.1f}%", "30%"],
                ["Error-Free Rate", f"{score_record.get('error_rate', 0):.1f}%", "25%"],
                ["Throughput", f"{score_record.get('throughput', 0):.1f}%", "25%"],
                ["Anomaly-Free Rate", f"{score_record.get('anomaly_rate', 0):.1f}%", "20%"],
            ],
            colWidths=[75 * mm, 45 * mm, 45 * mm],
        )
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, 1), _grade_color(composite)),
                    ("TEXTCOLOR", (0, 1), (-1, 1), WHITE),
                    ("ROWBACKGROUNDS", (0, 2), (-1, -1), [LIGHT, WHITE]),
                    ("GRID", (0, 0), (-1, -1), 0.5, MID),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(score_table)
        story.append(Spacer(1, 6 * mm))

        volume_table = Table(
            [
                ["Records Processed", "Rule Violations", "Anomalies Flagged"],
                [f"{int(score_record.get('total_records', 0)):,}", f"{len(exceptions):,}", f"{anomaly_count:,}"],
            ],
            colWidths=[55 * mm, 55 * mm, 55 * mm],
        )
        volume_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 1), (-1, 1), 16),
                    ("TEXTCOLOR", (0, 1), (0, 1), TEAL),
                    ("TEXTCOLOR", (1, 1), (1, 1), RED if len(exceptions) > 500 else TEAL),
                    ("TEXTCOLOR", (2, 1), (2, 1), AMBER if anomaly_count > 100 else TEAL),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, MID),
                ]
            )
        )
        story.append(volume_table)
        story.append(Spacer(1, 6 * mm))

        if exceptions:
            story.append(
                Paragraph(
                    f"Top exceptions (showing {min(len(exceptions), PDF_MAX_EXCEPTIONS)} of {len(exceptions):,})",
                    ParagraphStyle("Section", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=NAVY),
                )
            )
            exception_rows = [["Record ID", "Rule", "Field", "Severity", "Team"]]
            for exception in exceptions[:PDF_MAX_EXCEPTIONS]:
                exception_rows.append(
                    [
                        str(exception.get("record_id", ""))[:20],
                        exception.get("rule_id", ""),
                        exception.get("field", ""),
                        exception.get("severity", ""),
                        str(exception.get("team", "")).upper(),
                    ]
                )
            exception_table = Table(exception_rows, colWidths=[55 * mm, 22 * mm, 28 * mm, 22 * mm, 28 * mm])
            exception_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, WHITE]),
                        ("GRID", (0, 0), (-1, -1), 0.3, MID),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.append(exception_table)

        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID))
        story.append(
            Paragraph(
                f"FlowSentinel · Automated Process Health Report · {report_date} · Confidential",
                ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#9CA3AF"), alignment=1),
            )
        )

        document.build(story)
        logger.info("PDF report saved to %s", output_path)
        return output_path

