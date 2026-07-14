from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.app.application.schemas.report import ReportChart, ReportKpi, ReportRequest, ReportResponse, ReportRisk


OUTPUT_DIR = Path("output/pdf")


class ReportAgentError(ValueError):
    """Raised when a report cannot be generated."""


class ReportAgent:
    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        self._output_dir = output_dir

    def generate(self, request: ReportRequest) -> ReportResponse:
        normalized = normalize_report_request(request)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = self._output_dir / build_report_filename(normalized)

        story = build_report_story(normalized)
        document = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=42,
            leftMargin=42,
            topMargin=48,
            bottomMargin=42,
            title=normalized.title,
        )
        document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

        page_count = len(PdfReader(str(pdf_path)).pages)
        return ReportResponse(
            title=normalized.title,
            pdf_path=str(pdf_path),
            page_count=page_count,
            sections=["Executive Summary", "KPIs", "Charts", "Recommendations", "Risks"],
            warnings=[],
        )


def normalize_report_request(request: ReportRequest) -> ReportRequest:
    if request.workflow is None:
        return request

    workflow = request.workflow
    kpis = [
        ReportKpi(label=kpi.label, value=kpi.value, description=f"{kpi.function.value} of {kpi.column}")
        for kpi in workflow.analysis.kpis
    ]
    charts = [
        ReportChart(
            title=f"{workflow.visualization.chart_type.value.title()} Chart",
            chart_type=workflow.visualization.chart_type.value,
            figure=workflow.visualization.figure,
            description=workflow.visualization.reasoning,
        )
    ]
    risks = [
        ReportRisk(
            title=anomaly.title,
            severity=anomaly.severity,
            description=anomaly.explanation,
            mitigation="Review affected columns and validate source data.",
        )
        for anomaly in workflow.insights.anomalies
    ]

    return request.model_copy(
        update={
            "executive_summary": request.executive_summary or workflow.insights.executive_summary,
            "kpis": request.kpis or kpis,
            "charts": request.charts or charts,
            "recommendations": request.recommendations or workflow.insights.recommendations,
            "risks": request.risks or risks,
        }
    )


def build_report_story(request: ReportRequest) -> list[Any]:
    styles = build_styles()
    story: list[Any] = []

    story.append(Paragraph(request.title, styles["Title"]))
    story.append(Paragraph(f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", styles["Meta"]))
    story.append(Spacer(1, 0.24 * inch))

    add_section(story, "Executive Summary", styles)
    story.append(Paragraph(request.executive_summary or "No executive summary was provided.", styles["Body"]))

    add_section(story, "KPIs", styles)
    story.append(build_kpi_table(request.kpis, styles))

    add_section(story, "Charts", styles)
    if request.charts:
        for chart in request.charts:
            story.extend(build_chart_section(chart, styles))
    else:
        story.append(Paragraph("No charts were provided.", styles["Body"]))

    story.append(PageBreak())
    add_section(story, "Recommendations", styles)
    story.append(build_recommendation_table(request.recommendations, styles))

    add_section(story, "Risks", styles)
    story.append(build_risk_table(request.risks, styles))

    return story


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=12,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_CENTER,
        ),
    }


def add_section(story: list[Any], title: str, styles: dict[str, ParagraphStyle]) -> None:
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(title, styles["Section"]))


def build_kpi_table(kpis: list[ReportKpi], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [["KPI", "Value", "Description"]]
    if kpis:
        rows.extend([[kpi.label, str(kpi.value), kpi.description or ""] for kpi in kpis])
    else:
        rows.append(["No KPIs provided", "-", "-"])
    return styled_table(rows, [1.5 * inch, 1.2 * inch, 3.8 * inch], styles)


def build_recommendation_table(recommendations, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [["Priority", "Action", "Rationale", "Expected Outcome"]]
    if recommendations:
        rows.extend(
            [
                [recommendation.priority, recommendation.action, recommendation.rationale, recommendation.expected_outcome]
                for recommendation in recommendations
            ]
        )
    else:
        rows.append(["-", "No recommendations provided", "-", "-"])
    return styled_table(rows, [0.75 * inch, 1.8 * inch, 2.2 * inch, 1.75 * inch], styles)


def build_risk_table(risks: list[ReportRisk], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [["Severity", "Risk", "Description", "Mitigation"]]
    if risks:
        rows.extend([[risk.severity, risk.title, risk.description, risk.mitigation or ""] for risk in risks])
    else:
        rows.append(["-", "No risks provided", "-", "-"])
    return styled_table(rows, [0.75 * inch, 1.5 * inch, 2.4 * inch, 1.85 * inch], styles)


def styled_table(rows: list[list[Any]], column_widths: list[float], styles: dict[str, ParagraphStyle]) -> Table:
    paragraph_rows = [
        [Paragraph(str(value), styles["Body"]) for value in row]
        for row in rows
    ]
    table = Table(paragraph_rows, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_chart_section(chart: ReportChart, styles: dict[str, ParagraphStyle]) -> list[Any]:
    flowables: list[Any] = [
        Paragraph(chart.title, styles["Body"]),
        Paragraph(chart.description or f"{chart.chart_type.title()} chart", styles["Body"]),
        Spacer(1, 0.08 * inch),
    ]
    drawing = build_chart_drawing(chart)
    if drawing is not None:
        flowables.append(drawing)
    flowables.append(build_chart_metadata_table(chart, styles))
    flowables.append(Spacer(1, 0.14 * inch))
    return flowables


def build_chart_drawing(chart: ReportChart) -> Drawing | None:
    traces = chart.figure.get("data", [])
    if not traces:
        return None

    first_trace = traces[0]
    trace_type = first_trace.get("type", chart.chart_type)
    y_values = coerce_numeric_list(first_trace.get("y", []))
    x_values = [str(value) for value in first_trace.get("x", [])]

    if trace_type == "bar" and y_values:
        drawing = Drawing(460, 150)
        bar_chart = VerticalBarChart()
        bar_chart.x = 35
        bar_chart.y = 25
        bar_chart.height = 100
        bar_chart.width = 380
        bar_chart.data = [y_values[:12]]
        bar_chart.categoryAxis.categoryNames = x_values[:12] if x_values else [str(index + 1) for index in range(len(y_values[:12]))]
        bar_chart.valueAxis.valueMin = 0
        bar_chart.bars[0].fillColor = colors.HexColor("#2563eb")
        drawing.add(bar_chart)
        return drawing

    if trace_type in {"line", "scatter"} and y_values:
        drawing = Drawing(460, 150)
        line_plot = LinePlot()
        line_plot.x = 35
        line_plot.y = 25
        line_plot.height = 100
        line_plot.width = 380
        line_plot.data = [[(index, value) for index, value in enumerate(y_values[:50])]]
        line_plot.lines[0].strokeColor = colors.HexColor("#2563eb")
        drawing.add(line_plot)
        return drawing

    return None


def build_chart_metadata_table(chart: ReportChart, styles: dict[str, ParagraphStyle]) -> Table:
    traces = chart.figure.get("data", [])
    trace_count = len(traces)
    trace_types = ", ".join(sorted({str(trace.get("type", "unknown")) for trace in traces})) if traces else "none"
    return styled_table(
        [["Chart Type", "Trace Count", "Trace Types"], [chart.chart_type, trace_count, trace_types]],
        [1.6 * inch, 1.2 * inch, 3.7 * inch],
        styles,
    )


def coerce_numeric_list(values: Any) -> list[float]:
    numeric_values: list[float] = []
    for value in values or []:
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError):
            continue
    return numeric_values


def build_report_filename(request: ReportRequest) -> str:
    if request.output_filename:
        return sanitize_filename(request.output_filename)
    slug = sanitize_filename(request.title.lower().replace(" ", "_"))
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{slug}_{timestamp}.pdf"


def sanitize_filename(filename: str) -> str:
    stem = re.sub(r"[^a-zA-Z0-9_.-]+", "_", filename).strip("._")
    if not stem:
        raise ReportAgentError("Output filename cannot be empty.")
    return stem if stem.lower().endswith(".pdf") else f"{stem}.pdf"


def draw_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(42, 24, "DataWhisperer AI")
    canvas.drawRightString(A4[0] - 42, 24, f"Page {document.page}")
    canvas.restoreState()
