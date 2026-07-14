from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.application.schemas.analysis import (
    AggregationFunction,
    AnalysisRequest,
    AnalysisResponse,
    FilterCondition,
    FilterOperator,
    KpiResult,
    SortDirection,
)


class AnalysisAgentError(ValueError):
    """Raised when an analysis request cannot be executed."""


class AnalysisAgent:
    def execute(self, request: AnalysisRequest) -> AnalysisResponse:
        dataframe = pd.DataFrame(request.records)
        if dataframe.empty:
            raise AnalysisAgentError("Analysis requires at least one data row.")

        warnings: list[str] = []
        filtered_dataframe = self._apply_filters(dataframe, request.filters)
        sorted_dataframe = self._apply_sort(filtered_dataframe, request.sort)
        kpis = self._calculate_kpis(sorted_dataframe, request.kpis)
        aggregation = self._aggregate(sorted_dataframe, request.aggregation) if request.aggregation else []
        statistics = self._calculate_statistics(sorted_dataframe, request.statistics_columns, warnings)

        return AnalysisResponse(
            row_count=len(dataframe),
            filtered_row_count=len(sorted_dataframe),
            column_count=len(dataframe.columns),
            columns=[str(column) for column in dataframe.columns],
            preview=to_json_records(sorted_dataframe.head(request.preview_rows)),
            kpis=kpis,
            aggregation=aggregation,
            statistics=statistics,
            warnings=warnings,
        )

    def _apply_filters(self, dataframe: pd.DataFrame, filters: list[FilterCondition]) -> pd.DataFrame:
        filtered = dataframe.copy()
        for condition in filters:
            self._require_columns(filtered, [condition.column])
            mask = build_filter_mask(filtered, condition)
            filtered = filtered.loc[mask]
        return filtered

    def _apply_sort(self, dataframe: pd.DataFrame, sort_specs) -> pd.DataFrame:
        if not sort_specs:
            return dataframe

        columns = [sort.column for sort in sort_specs]
        self._require_columns(dataframe, columns)
        ascending = [sort.direction == SortDirection.ASC for sort in sort_specs]
        return dataframe.sort_values(by=columns, ascending=ascending, kind="mergesort")

    def _calculate_kpis(self, dataframe: pd.DataFrame, kpis) -> list[KpiResult]:
        results: list[KpiResult] = []
        for kpi in kpis:
            self._require_columns(dataframe, [kpi.column])
            value = apply_aggregation(dataframe[kpi.column], kpi.function)
            results.append(
                KpiResult(
                    label=kpi.label or f"{kpi.function.value}_{kpi.column}",
                    column=kpi.column,
                    function=kpi.function,
                    value=to_json_value(value),
                )
            )
        return results

    def _aggregate(self, dataframe: pd.DataFrame, aggregation) -> list[dict[str, Any]]:
        if not aggregation.metrics:
            raise AnalysisAgentError("Aggregation requires at least one metric.")

        group_by = aggregation.group_by
        metric_columns = [metric.column for metric in aggregation.metrics]
        self._require_columns(dataframe, [*group_by, *metric_columns])

        if group_by:
            grouped = dataframe.groupby(group_by, dropna=False)
            result_parts = []
            for metric in aggregation.metrics:
                alias = metric.alias or f"{metric.function.value}_{metric.column}"
                series = apply_grouped_aggregation(grouped[metric.column], metric.function)
                result_parts.append(series.rename(alias))
            result = pd.concat(result_parts, axis=1).reset_index()
        else:
            result = pd.DataFrame(
                [
                    {
                        metric.alias or f"{metric.function.value}_{metric.column}": to_json_value(
                            apply_aggregation(dataframe[metric.column], metric.function)
                        )
                        for metric in aggregation.metrics
                    }
                ]
            )

        return to_json_records(result)

    def _calculate_statistics(
        self,
        dataframe: pd.DataFrame,
        requested_columns: list[str],
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        numeric_dataframe = dataframe.select_dtypes(include="number")
        if requested_columns:
            self._require_columns(dataframe, requested_columns)
            numeric_columns = [column for column in requested_columns if column in numeric_dataframe.columns]
            skipped = sorted(set(requested_columns) - set(numeric_columns))
            if skipped:
                warnings.append(f"Skipped non-numeric statistics columns: {', '.join(skipped)}")
            numeric_dataframe = numeric_dataframe[numeric_columns]

        if numeric_dataframe.empty:
            warnings.append("No numeric columns available for statistical analysis.")
            return []

        statistics = numeric_dataframe.describe().transpose().reset_index(names="column")
        return to_json_records(statistics)

    @staticmethod
    def _require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
        missing = [column for column in columns if column not in dataframe.columns]
        if missing:
            raise AnalysisAgentError(f"Unknown column(s): {', '.join(missing)}")


def build_filter_mask(dataframe: pd.DataFrame, condition: FilterCondition) -> pd.Series:
    series = dataframe[condition.column]
    operator = condition.operator

    if operator == FilterOperator.EQ:
        return series == condition.value
    if operator == FilterOperator.NE:
        return series != condition.value
    if operator == FilterOperator.GT:
        return series > condition.value
    if operator == FilterOperator.GTE:
        return series >= condition.value
    if operator == FilterOperator.LT:
        return series < condition.value
    if operator == FilterOperator.LTE:
        return series <= condition.value
    if operator == FilterOperator.CONTAINS:
        return series.astype(str).str.contains(str(condition.value), case=False, na=False)
    if operator == FilterOperator.IN:
        return series.isin(as_list(condition.value))
    if operator == FilterOperator.NOT_IN:
        return ~series.isin(as_list(condition.value))
    if operator == FilterOperator.IS_NULL:
        return series.isna()
    if operator == FilterOperator.NOT_NULL:
        return series.notna()

    raise AnalysisAgentError(f"Unsupported filter operator: {operator}")


def apply_aggregation(series: pd.Series, function: AggregationFunction) -> Any:
    if function == AggregationFunction.COUNT:
        return int(series.count())
    if function == AggregationFunction.SUM:
        return series.sum()
    if function == AggregationFunction.MEAN:
        return series.mean()
    if function == AggregationFunction.MEDIAN:
        return series.median()
    if function == AggregationFunction.MIN:
        return series.min()
    if function == AggregationFunction.MAX:
        return series.max()
    if function == AggregationFunction.STD:
        return series.std()
    raise AnalysisAgentError(f"Unsupported aggregation function: {function}")


def apply_grouped_aggregation(grouped_series, function: AggregationFunction) -> pd.Series:
    if function == AggregationFunction.COUNT:
        return grouped_series.count()
    if function == AggregationFunction.SUM:
        return grouped_series.sum()
    if function == AggregationFunction.MEAN:
        return grouped_series.mean()
    if function == AggregationFunction.MEDIAN:
        return grouped_series.median()
    if function == AggregationFunction.MIN:
        return grouped_series.min()
    if function == AggregationFunction.MAX:
        return grouped_series.max()
    if function == AggregationFunction.STD:
        return grouped_series.std()
    raise AnalysisAgentError(f"Unsupported aggregation function: {function}")


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def to_json_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    clean_dataframe = dataframe.astype(object).where(pd.notna(dataframe), None)
    return [
        {str(key): to_json_value(value) for key, value in row.items()}
        for row in clean_dataframe.to_dict(orient="records")
    ]


def to_json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
