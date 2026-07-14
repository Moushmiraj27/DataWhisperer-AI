from typing import Any

from pydantic import BaseModel, Field

from backend.app.application.schemas.insight import Recommendation
from backend.app.application.schemas.workflow import WorkflowResponse


class ReportKpi(BaseModel):
    label: str
    value: Any
    description: str | None = None


class ReportChart(BaseModel):
    title: str
    chart_type: str
    figure: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None


class ReportRisk(BaseModel):
    title: str
    severity: str = Field(description="low, medium, or high")
    description: str
    mitigation: str | None = None


class ReportRequest(BaseModel):
    title: str = Field(default="DataWhisperer AI Report", max_length=180)
    executive_summary: str | None = None
    kpis: list[ReportKpi] = Field(default_factory=list)
    charts: list[ReportChart] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    risks: list[ReportRisk] = Field(default_factory=list)
    workflow: WorkflowResponse | None = None
    output_filename: str | None = Field(default=None, max_length=120)


class ReportResponse(BaseModel):
    title: str
    pdf_path: str
    page_count: int
    sections: list[str]
    warnings: list[str] = Field(default_factory=list)
