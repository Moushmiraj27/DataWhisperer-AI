from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from backend.app.application.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.application.schemas.visualization import VisualizationRequest, VisualizationResponse


class VerificationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    RETRIED = "retried"
    SKIPPED = "skipped"


class VerificationCheck(BaseModel):
    name: str
    status: VerificationStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class VerificationRequest(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)
    expected_columns: list[str] = Field(default_factory=list)
    required_columns: list[str] = Field(default_factory=list)
    analysis_request: AnalysisRequest | None = None
    analysis_output: AnalysisResponse | None = None
    visualization_request: VisualizationRequest | None = None
    visualization_output: VisualizationResponse | None = None
    retry_failed_operations: bool = True


class VerificationResponse(BaseModel):
    verified: bool
    checks: list[VerificationCheck]
    verified_analysis_output: AnalysisResponse | None = None
    verified_visualization_output: VisualizationResponse | None = None
    missing_values: list[dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    warnings: list[str] = Field(default_factory=list)
