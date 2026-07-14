from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ChartType(StrEnum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    PIE = "pie"
    HEATMAP = "heatmap"
    BOXPLOT = "boxplot"


class VisualizationRequest(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1)
    chart_type: ChartType | None = None
    x: str | None = None
    y: str | None = None
    color: str | None = None
    title: str | None = None


class VisualizationResponse(BaseModel):
    chart_type: ChartType
    figure: dict[str, Any]
    reasoning: str
    warnings: list[str] = Field(default_factory=list)
