from typing import Any

from pydantic import BaseModel, Field

from backend.app.application.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.application.schemas.insight import InsightResponse
from backend.app.application.schemas.planner import PlannerResponse
from backend.app.application.schemas.verification import VerificationResponse
from backend.app.application.schemas.visualization import VisualizationRequest, VisualizationResponse


class WorkflowRequest(BaseModel):
    user_request: str = Field(min_length=1, max_length=4000)
    records: list[dict[str, Any]] = Field(min_length=1)
    dataset_context: str | None = Field(default=None, max_length=12000)
    analysis_request: AnalysisRequest | None = None
    visualization_request: VisualizationRequest | None = None
    expected_columns: list[str] = Field(default_factory=list)
    required_columns: list[str] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    final_summary: str
    planner: PlannerResponse
    analysis: AnalysisResponse
    visualization: VisualizationResponse
    insights: InsightResponse
    verification: VerificationResponse
    verified: bool
    warnings: list[str] = Field(default_factory=list)
