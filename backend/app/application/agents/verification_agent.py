from __future__ import annotations

import math
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from pydantic import ValidationError

from backend.app.application.agents.analysis_agent import AnalysisAgent, AnalysisAgentError
from backend.app.application.agents.visualization_agent import VisualizationAgent, VisualizationAgentError
from backend.app.application.schemas.analysis import AnalysisResponse
from backend.app.application.schemas.verification import (
    VerificationCheck,
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
)
from backend.app.application.schemas.visualization import VisualizationResponse


class VerificationAgentError(ValueError):
    """Raised when verification cannot be performed."""


class VerificationAgent:
    def __init__(
        self,
        analysis_agent: AnalysisAgent | None = None,
        visualization_agent: VisualizationAgent | None = None,
    ) -> None:
        self._analysis_agent = analysis_agent or AnalysisAgent()
        self._visualization_agent = visualization_agent or VisualizationAgent()

    def verify(self, request: VerificationRequest) -> VerificationResponse:
        dataframe = pd.DataFrame(request.records or get_records_from_requests(request))
        checks: list[VerificationCheck] = []
        warnings: list[str] = []
        retry_count = 0

        checks.extend(verify_columns(dataframe, request.expected_columns, request.required_columns))
        missing_values = summarize_missing_values(dataframe)
        checks.append(verify_missing_values(missing_values))

        verified_analysis_output = request.analysis_output
        analysis_check, retried_analysis, analysis_retry_count = self._verify_or_retry_analysis(request)
        checks.append(analysis_check)
        if retried_analysis is not None:
            verified_analysis_output = retried_analysis
        retry_count += analysis_retry_count

        verified_visualization_output = request.visualization_output
        chart_check, retried_chart, chart_retry_count = self._verify_or_retry_chart(request)
        checks.append(chart_check)
        if retried_chart is not None:
            verified_visualization_output = retried_chart
        retry_count += chart_retry_count

        if dataframe.empty and not request.analysis_request and not request.visualization_request:
            warnings.append("No records or operation requests were provided; only structural checks could run.")

        return VerificationResponse(
            verified=all(
                check.status in {VerificationStatus.PASSED, VerificationStatus.RETRIED, VerificationStatus.SKIPPED}
                for check in checks
            ),
            checks=checks,
            verified_analysis_output=verified_analysis_output,
            verified_visualization_output=verified_visualization_output,
            missing_values=missing_values,
            retry_count=retry_count,
            warnings=warnings,
        )

    def _verify_or_retry_analysis(
        self,
        request: VerificationRequest,
    ) -> tuple[VerificationCheck, AnalysisResponse | None, int]:
        if not request.analysis_request and not request.analysis_output:
            return skipped_check("calculation_correctness", "No analysis output was provided."), None, 0

        if not request.analysis_request:
            return skipped_check(
                "calculation_correctness",
                "Analysis output was provided without the original request, so correctness could not be recomputed.",
            ), None, 0

        try:
            expected_output = self._analysis_agent.execute(request.analysis_request)
        except AnalysisAgentError as error:
            return failed_check("calculation_correctness", str(error)), None, 0

        if request.analysis_output is None:
            if request.retry_failed_operations:
                return (
                    VerificationCheck(
                        name="calculation_correctness",
                        status=VerificationStatus.RETRIED,
                        message="Analysis output was missing and has been regenerated.",
                    ),
                    expected_output,
                    1,
                )
            return failed_check("calculation_correctness", "Analysis output is missing."), None, 0

        differences = compare_analysis_outputs(expected_output, request.analysis_output)
        if not differences:
            return passed_check("calculation_correctness", "Analysis output matches recomputed Pandas results."), None, 0

        if request.retry_failed_operations:
            return (
                VerificationCheck(
                    name="calculation_correctness",
                    status=VerificationStatus.RETRIED,
                    message="Analysis output did not match recomputed results and has been regenerated.",
                    details={"differences": differences},
                ),
                expected_output,
                1,
            )

        return failed_check("calculation_correctness", "Analysis output does not match recomputed results.", {"differences": differences}), None, 0

    def _verify_or_retry_chart(
        self,
        request: VerificationRequest,
    ) -> tuple[VerificationCheck, VisualizationResponse | None, int]:
        if not request.visualization_request and not request.visualization_output:
            return skipped_check("chart_validity", "No visualization output was provided."), None, 0

        chart_error = None
        if request.visualization_output is not None:
            chart_error = validate_plotly_figure(request.visualization_output.figure)
            if chart_error is None:
                return passed_check("chart_validity", "Plotly figure JSON is valid."), None, 0

            if not request.retry_failed_operations or request.visualization_request is None:
                return failed_check("chart_validity", chart_error), None, 0

        if request.visualization_request is None:
            return failed_check("chart_validity", "Visualization request is required to retry chart generation."), None, 0

        try:
            retried_output = self._visualization_agent.execute(request.visualization_request)
        except VisualizationAgentError as error:
            return failed_check("chart_validity", str(error)), None, 0

        return (
            VerificationCheck(
                name="chart_validity",
                status=VerificationStatus.RETRIED,
                message="Chart output was missing or invalid and has been regenerated.",
                details={"previous_error": chart_error} if chart_error else {},
            ),
            retried_output,
            1,
        )


def get_records_from_requests(request: VerificationRequest) -> list[dict[str, Any]]:
    if request.analysis_request:
        return request.analysis_request.records
    if request.visualization_request:
        return request.visualization_request.records
    return []


def verify_columns(
    dataframe: pd.DataFrame,
    expected_columns: list[str],
    required_columns: list[str],
) -> list[VerificationCheck]:
    if dataframe.empty and not expected_columns and not required_columns:
        return [skipped_check("column_names", "No records or column requirements were provided.")]

    actual_columns = [str(column) for column in dataframe.columns]
    checks: list[VerificationCheck] = []

    if expected_columns:
        missing_expected = [column for column in expected_columns if column not in actual_columns]
        unexpected = [column for column in actual_columns if column not in expected_columns]
        status = VerificationStatus.PASSED if not missing_expected and not unexpected else VerificationStatus.FAILED
        checks.append(
            VerificationCheck(
                name="column_names",
                status=status,
                message="Column names match expected columns." if status == VerificationStatus.PASSED else "Column names do not match expected columns.",
                details={
                    "expected": expected_columns,
                    "actual": actual_columns,
                    "missing_expected": missing_expected,
                    "unexpected": unexpected,
                },
            )
        )
    else:
        checks.append(passed_check("column_names", "Column names are available.", {"actual": actual_columns}))

    if required_columns:
        missing_required = [column for column in required_columns if column not in actual_columns]
        status = VerificationStatus.PASSED if not missing_required else VerificationStatus.FAILED
        checks.append(
            VerificationCheck(
                name="required_columns",
                status=status,
                message="Required columns are present." if status == VerificationStatus.PASSED else "Required columns are missing.",
                details={"required": required_columns, "missing_required": missing_required},
            )
        )

    return checks


def summarize_missing_values(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    if dataframe.empty:
        return []

    missing_counts = dataframe.isna().sum()
    return [
        {
            "column": str(column),
            "missing_values": int(count),
            "missing_percent": round(float(count) / len(dataframe) * 100, 2),
        }
        for column, count in missing_counts.items()
        if int(count) > 0
    ]


def verify_missing_values(missing_values: list[dict[str, Any]]) -> VerificationCheck:
    if not missing_values:
        return passed_check("missing_values", "No missing values detected.")
    return VerificationCheck(
        name="missing_values",
        status=VerificationStatus.PASSED,
        message="Missing values were detected and reported.",
        details={"columns_with_missing_values": missing_values},
    )


def compare_analysis_outputs(expected: AnalysisResponse, actual: AnalysisResponse) -> list[str]:
    differences: list[str] = []
    expected_dict = expected.model_dump(mode="json")
    actual_dict = actual.model_dump(mode="json")

    for key in ["row_count", "filtered_row_count", "column_count", "columns", "preview", "kpis", "aggregation", "statistics"]:
        if not values_equal(expected_dict.get(key), actual_dict.get(key)):
            differences.append(key)

    return differences


def validate_plotly_figure(figure: dict[str, Any]) -> str | None:
    try:
        go.Figure(figure)
    except (ValueError, TypeError, ValidationError) as error:
        return f"Invalid Plotly figure: {error}"

    if not figure.get("data"):
        return "Invalid Plotly figure: figure contains no traces."
    return None


def values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, float) and isinstance(right, float):
        return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(values_equal(l_item, r_item) for l_item, r_item in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(values_equal(left[key], right[key]) for key in left)
    return left == right


def passed_check(name: str, message: str, details: dict[str, Any] | None = None) -> VerificationCheck:
    return VerificationCheck(
        name=name,
        status=VerificationStatus.PASSED,
        message=message,
        details=details or {},
    )


def failed_check(name: str, message: str, details: dict[str, Any] | None = None) -> VerificationCheck:
    return VerificationCheck(
        name=name,
        status=VerificationStatus.FAILED,
        message=message,
        details=details or {},
    )


def skipped_check(name: str, message: str) -> VerificationCheck:
    return VerificationCheck(name=name, status=VerificationStatus.SKIPPED, message=message)
