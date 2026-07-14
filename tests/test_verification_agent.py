from backend.app.application.agents.analysis_agent import AnalysisAgent
from backend.app.application.agents.verification_agent import VerificationAgent
from backend.app.application.agents.visualization_agent import VisualizationAgent
from backend.app.application.schemas.analysis import (
    AggregationFunction,
    AnalysisRequest,
    FilterCondition,
    FilterOperator,
    KpiSpec,
)
from backend.app.application.schemas.verification import VerificationRequest, VerificationStatus
from backend.app.application.schemas.visualization import ChartType, VisualizationRequest, VisualizationResponse


RECORDS = [
    {"region": "West", "sales": 100, "profit": 20},
    {"region": "East", "sales": 150, "profit": None},
    {"region": "West", "sales": 200, "profit": 40},
]


def test_verification_agent_verifies_columns_and_missing_values() -> None:
    response = VerificationAgent().verify(
        VerificationRequest(
            records=RECORDS,
            expected_columns=["region", "sales", "profit"],
            required_columns=["sales"],
        )
    )

    assert response.verified is True
    assert response.missing_values == [{"column": "profit", "missing_values": 1, "missing_percent": 33.33}]
    assert any(check.name == "column_names" and check.status == VerificationStatus.PASSED for check in response.checks)


def test_verification_agent_retries_incorrect_analysis_output() -> None:
    analysis_request = AnalysisRequest(
        records=RECORDS,
        filters=[FilterCondition(column="sales", operator=FilterOperator.GTE, value=100)],
        kpis=[KpiSpec(column="sales", function=AggregationFunction.SUM, label="Total Sales")],
    )
    wrong_output = AnalysisAgent().execute(analysis_request).model_copy(update={"filtered_row_count": 999})

    response = VerificationAgent().verify(
        VerificationRequest(
            analysis_request=analysis_request,
            analysis_output=wrong_output,
            retry_failed_operations=True,
        )
    )

    assert response.retry_count == 1
    assert response.verified is True
    assert response.verified_analysis_output is not None
    assert response.verified_analysis_output.filtered_row_count == 3
    assert any(check.name == "calculation_correctness" and check.status == VerificationStatus.RETRIED for check in response.checks)


def test_verification_agent_validates_chart_output() -> None:
    visualization_request = VisualizationRequest(records=RECORDS, chart_type=ChartType.BAR, x="region", y="sales")
    visualization_output = VisualizationAgent().execute(visualization_request)

    response = VerificationAgent().verify(
        VerificationRequest(
            visualization_request=visualization_request,
            visualization_output=visualization_output,
        )
    )

    assert any(check.name == "chart_validity" and check.status == VerificationStatus.PASSED for check in response.checks)


def test_verification_agent_retries_invalid_chart_output() -> None:
    visualization_request = VisualizationRequest(records=RECORDS, chart_type=ChartType.BAR, x="region", y="sales")
    invalid_output = VisualizationResponse(chart_type=ChartType.BAR, figure={"data": []}, reasoning="bad")

    response = VerificationAgent().verify(
        VerificationRequest(
            visualization_request=visualization_request,
            visualization_output=invalid_output,
            retry_failed_operations=True,
        )
    )

    assert response.retry_count == 1
    assert response.verified is True
    assert response.verified_visualization_output is not None
    assert response.verified_visualization_output.figure["data"]


def test_verification_agent_fails_when_required_columns_are_missing() -> None:
    response = VerificationAgent().verify(
        VerificationRequest(
            records=RECORDS,
            expected_columns=["region", "sales", "profit", "margin"],
            required_columns=["margin"],
        )
    )

    assert response.verified is False
    assert any(check.name == "column_names" and check.status == VerificationStatus.FAILED for check in response.checks)
    assert any(check.name == "required_columns" and check.status == VerificationStatus.FAILED for check in response.checks)


def test_verification_agent_fails_invalid_chart_without_retry() -> None:
    invalid_output = VisualizationResponse(chart_type=ChartType.BAR, figure={"data": []}, reasoning="bad")

    response = VerificationAgent().verify(
        VerificationRequest(
            records=RECORDS,
            visualization_output=invalid_output,
            retry_failed_operations=False,
        )
    )

    assert response.verified is False
    assert any(check.name == "chart_validity" and check.status == VerificationStatus.FAILED for check in response.checks)
