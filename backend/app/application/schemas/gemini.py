from pydantic import BaseModel, Field


class GeminiInsight(BaseModel):
    title: str = Field(description="Short insight title.")
    detail: str = Field(description="Brief explanation of the insight.")
    confidence: str = Field(description="One of: low, medium, high.")


class GeminiChartRecommendation(BaseModel):
    chart_type: str = Field(description="Recommended chart type.")
    columns: list[str] = Field(default_factory=list, description="Columns to use for the chart.")
    rationale: str = Field(description="Why this chart is useful.")


class GeminiStructuredResponse(BaseModel):
    answer: str = Field(description="Direct answer to the user question.")
    summary: str = Field(description="Brief summary of the analysis.")
    insights: list[GeminiInsight] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    chart_recommendations: list[GeminiChartRecommendation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GeminiChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    dataset_context: str | None = Field(default=None, max_length=12000)
