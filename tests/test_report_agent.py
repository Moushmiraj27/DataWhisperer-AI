from pathlib import Path

from pypdf import PdfReader

from backend.app.application.agents.report_agent import ReportAgent
from backend.app.application.schemas.insight import Recommendation
from backend.app.application.schemas.report import ReportChart, ReportKpi, ReportRequest, ReportRisk


def test_report_agent_generates_pdf_with_required_sections(tmp_path) -> None:
    request = ReportRequest(
        title="Quarterly Sales Report",
        executive_summary="Sales improved while operational risks remain manageable.",
        kpis=[
            ReportKpi(label="Revenue", value="120000", description="Total revenue"),
            ReportKpi(label="Profit", value="32000", description="Net profit"),
        ],
        charts=[
            ReportChart(
                title="Revenue by Region",
                chart_type="bar",
                figure={"data": [{"type": "bar", "x": ["West", "East"], "y": [100, 150]}]},
                description="Regional revenue comparison.",
            )
        ],
        recommendations=[
            Recommendation(
                action="Invest in East region",
                rationale="East has the strongest growth.",
                priority="high",
                expected_outcome="Increase revenue.",
            )
        ],
        risks=[
            ReportRisk(
                title="Margin pressure",
                severity="medium",
                description="Costs are rising.",
                mitigation="Monitor supplier pricing.",
            )
        ],
        output_filename="quarterly_sales_report.pdf",
    )

    response = ReportAgent(output_dir=tmp_path).generate(request)

    pdf_path = Path(response.pdf_path)
    assert pdf_path.exists()
    assert response.page_count >= 1
    assert response.sections == ["Executive Summary", "KPIs", "Charts", "Recommendations", "Risks"]

    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Executive Summary" in text
    assert "KPIs" in text
    assert "Charts" in text
    assert "Recommendations" in text
    assert "Risks" in text
    assert "Revenue" in text


def test_report_agent_sanitizes_output_filename(tmp_path) -> None:
    response = ReportAgent(output_dir=tmp_path).generate(
        ReportRequest(title="AI Report", output_filename="../bad name")
    )

    assert Path(response.pdf_path).name == "bad_name.pdf"
