from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InsightConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BusinessInsight(BaseModel):
    title: str
    explanation: str
    evidence: list[str] = Field(default_factory=list)
    business_impact: str
    confidence: InsightConfidence


class KeyTrend(BaseModel):
    metric: str
    direction: str = Field(description="Increasing, decreasing, stable, mixed, or unknown.")
    explanation: str
    supporting_values: list[str] = Field(default_factory=list)


class Anomaly(BaseModel):
    title: str
    explanation: str
    affected_columns: list[str] = Field(default_factory=list)
    severity: str = Field(description="low, medium, or high")


class Recommendation(BaseModel):
    action: str
    rationale: str
    priority: str = Field(description="low, medium, or high")
    expected_outcome: str


class InsightRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    dataset_context: str | None = Field(default=None, max_length=12000)
    analysis_results: dict[str, Any] | list[dict[str, Any]] | str | None = None


class InsightResponse(BaseModel):
    executive_summary: str
    business_insights: list[BusinessInsight] = Field(default_factory=list)
    key_trends: list[KeyTrend] = Field(default_factory=list)
    anomalies: list[Anomaly] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
