import pytest

from backend.app.application.agents.analysis_agent import AnalysisAgent, AnalysisAgentError
from backend.app.application.schemas.analysis import (
    AggregationFunction,
    AggregationMetric,
    AggregationSpec,
    AnalysisRequest,
    FilterCondition,
    FilterOperator,
    KpiSpec,
    SortDirection,
    SortSpec,
)


RECORDS = [
    {"region": "West", "category": "A", "sales": 100, "profit": 20},
    {"region": "West", "category": "B", "sales": 200, "profit": 30},
    {"region": "East", "category": "A", "sales": 150, "profit": 25},
    {"region": "East", "category": "B", "sales": 80, "profit": None},
]


def test_analysis_agent_filters_sorts_and_returns_preview() -> None:
    request = AnalysisRequest(
        records=RECORDS,
        filters=[FilterCondition(column="sales", operator=FilterOperator.GTE, value=100)],
        sort=[SortSpec(column="profit", direction=SortDirection.DESC)],
        preview_rows=2,
    )

    response = AnalysisAgent().execute(request)

    assert response.row_count == 4
    assert response.filtered_row_count == 3
    assert response.preview[0]["sales"] == 200
    assert response.preview[1]["sales"] == 150


def test_analysis_agent_calculates_kpis_and_aggregation() -> None:
    request = AnalysisRequest(
        records=RECORDS,
        aggregation=AggregationSpec(
            group_by=["region"],
            metrics=[
                AggregationMetric(column="sales", function=AggregationFunction.SUM, alias="total_sales"),
                AggregationMetric(column="profit", function=AggregationFunction.MEAN, alias="avg_profit"),
            ],
        ),
        kpis=[KpiSpec(column="sales", function=AggregationFunction.SUM, label="Total Sales")],
    )

    response = AnalysisAgent().execute(request)

    assert response.kpis[0].label == "Total Sales"
    assert response.kpis[0].value == 530
    assert {row["region"] for row in response.aggregation} == {"East", "West"}
    assert next(row for row in response.aggregation if row["region"] == "West")["total_sales"] == 300


def test_analysis_agent_returns_statistics() -> None:
    request = AnalysisRequest(records=RECORDS, statistics_columns=["sales", "profit"])

    response = AnalysisAgent().execute(request)

    statistic_columns = {row["column"] for row in response.statistics}
    assert statistic_columns == {"sales", "profit"}
    assert response.warnings == []


def test_analysis_agent_rejects_unknown_columns() -> None:
    request = AnalysisRequest(
        records=RECORDS,
        filters=[FilterCondition(column="unknown", operator=FilterOperator.EQ, value="x")],
    )

    with pytest.raises(AnalysisAgentError, match="Unknown column"):
        AnalysisAgent().execute(request)
