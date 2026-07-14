from enum import StrEnum

from pydantic import BaseModel, Field


class PlannerIntent(StrEnum):
    STATISTICS = "Statistics"
    VISUALIZATION = "Visualization"
    FILTERING = "Filtering"
    AGGREGATION = "Aggregation"
    DATA_CLEANING = "Data Cleaning"
    RECOMMENDATION = "Recommendation"
    REPORT_GENERATION = "Report Generation"


class PlannerRequest(BaseModel):
    request: str = Field(min_length=1, max_length=4000)
    dataset_context: str | None = Field(default=None, max_length=12000)


class ExecutionStep(BaseModel):
    order: int
    action: str
    intent: PlannerIntent
    description: str
    inputs_required: list[str] = Field(default_factory=list)
    expected_output: str


class PlannerResponse(BaseModel):
    primary_intent: PlannerIntent
    intents: list[PlannerIntent]
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    execution_plan: list[ExecutionStep]
    requires_dataset: bool
    clarification_questions: list[str] = Field(default_factory=list)
