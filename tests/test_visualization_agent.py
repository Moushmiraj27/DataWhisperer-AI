import pytest

from backend.app.application.agents.visualization_agent import VisualizationAgent, VisualizationAgentError
from backend.app.application.schemas.visualization import ChartType, VisualizationRequest


RECORDS = [
    {"month": "Jan", "sales": 100, "profit": 20, "region": "West"},
    {"month": "Feb", "sales": 140, "profit": 35, "region": "West"},
    {"month": "Mar", "sales": 90, "profit": 18, "region": "East"},
]


def test_visualization_agent_returns_requested_bar_chart() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.BAR, x="month", y="sales")
    )

    assert response.chart_type == ChartType.BAR
    assert response.figure["data"][0]["type"] == "bar"


def test_visualization_agent_auto_selects_scatter_for_numeric_columns() -> None:
    response = VisualizationAgent().execute(VisualizationRequest(records=RECORDS))

    assert response.chart_type == ChartType.SCATTER
    assert response.figure["data"][0]["type"] == "scatter"


def test_visualization_agent_returns_histogram() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.HISTOGRAM, x="sales")
    )

    assert response.figure["data"][0]["type"] == "histogram"


def test_visualization_agent_returns_line_chart() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.LINE, x="month", y="sales")
    )

    assert response.chart_type == ChartType.LINE
    assert response.figure["data"][0]["type"] == "scatter"
    assert response.figure["data"][0]["mode"] == "lines"


def test_visualization_agent_returns_pie_chart() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.PIE, x="region", y="sales")
    )

    assert response.chart_type == ChartType.PIE
    assert response.figure["data"][0]["type"] == "pie"


def test_visualization_agent_returns_heatmap() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.HEATMAP)
    )

    assert response.chart_type == ChartType.HEATMAP
    assert response.figure["data"][0]["type"] == "heatmap"


def test_visualization_agent_returns_boxplot() -> None:
    response = VisualizationAgent().execute(
        VisualizationRequest(records=RECORDS, chart_type=ChartType.BOXPLOT, y="profit")
    )

    assert response.figure["data"][0]["type"] == "box"


def test_visualization_agent_rejects_unknown_columns() -> None:
    with pytest.raises(VisualizationAgentError, match="Unknown column"):
        VisualizationAgent().execute(
            VisualizationRequest(records=RECORDS, chart_type=ChartType.LINE, x="missing", y="sales")
        )


def test_visualization_agent_rejects_heatmap_without_numeric_columns() -> None:
    with pytest.raises(VisualizationAgentError, match="Heatmap requires"):
        VisualizationAgent().execute(
            VisualizationRequest(records=[{"region": "West", "category": "A"}], chart_type=ChartType.HEATMAP)
        )
