from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FilterOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"


class AggregationFunction(StrEnum):
    COUNT = "count"
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    STD = "std"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: Any | None = None


class AggregationMetric(BaseModel):
    column: str
    function: AggregationFunction
    alias: str | None = None


class AggregationSpec(BaseModel):
    group_by: list[str] = Field(default_factory=list)
    metrics: list[AggregationMetric] = Field(default_factory=list)


class SortSpec(BaseModel):
    column: str
    direction: SortDirection = SortDirection.ASC


class KpiSpec(BaseModel):
    column: str
    function: AggregationFunction
    label: str | None = None


class AnalysisRequest(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1)
    filters: list[FilterCondition] = Field(default_factory=list)
    aggregation: AggregationSpec | None = None
    sort: list[SortSpec] = Field(default_factory=list)
    kpis: list[KpiSpec] = Field(default_factory=list)
    statistics_columns: list[str] = Field(default_factory=list)
    preview_rows: int = Field(default=20, ge=1, le=100)


class KpiResult(BaseModel):
    label: str
    column: str
    function: AggregationFunction
    value: Any


class AnalysisResponse(BaseModel):
    row_count: int
    filtered_row_count: int
    column_count: int
    columns: list[str]
    preview: list[dict[str, Any]]
    kpis: list[KpiResult] = Field(default_factory=list)
    aggregation: list[dict[str, Any]] = Field(default_factory=list)
    statistics: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
