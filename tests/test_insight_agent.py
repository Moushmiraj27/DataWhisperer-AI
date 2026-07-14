import pytest

from backend.app.application.agents.insight_agent import InsightAgent, serialize_analysis_results
from backend.app.application.schemas.insight import (
    Anomaly,
    BusinessInsight,
    InsightConfidence,
    InsightRequest,
    InsightResponse,
    KeyTrend,
    Recommendation,
)


class FakeGeminiService:
    def __init__(self) -> None:
        self.prompt = ""
        self.system_instruction = ""

    def generate_structured_response(self, system_instruction, prompt, response_model):
        self.system_instruction = system_instruction
        self.prompt = prompt
        return response_model(
            executive_summary="Revenue is growing, but returns require attention.",
            business_insights=[
                BusinessInsight(
                    title="Revenue growth",
                    explanation="Sales increased across the latest period.",
                    evidence=["sales: 1200"],
                    business_impact="Improves short-term revenue outlook.",
                    confidence=InsightConfidence.HIGH,
                )
            ],
            key_trends=[
                KeyTrend(
                    metric="sales",
                    direction="increasing",
                    explanation="Sales moved upward across periods.",
                    supporting_values=["Jan: 100", "Feb: 150"],
                )
            ],
            anomalies=[
                Anomaly(
                    title="High return rate",
                    explanation="Returns rose faster than sales.",
                    affected_columns=["returns"],
                    severity="medium",
                )
            ],
            recommendations=[
                Recommendation(
                    action="Audit returned orders",
                    rationale="Returns are affecting net revenue.",
                    priority="high",
                    expected_outcome="Reduce avoidable returns.",
                )
            ],
            limitations=[],
        )


class FailingGeminiService:
    def generate_structured_response(self, system_instruction, prompt, response_model):
        raise RuntimeError("Gemini unavailable")


def test_insight_agent_generates_structured_response() -> None:
    gemini_service = FakeGeminiService()
    request = InsightRequest(
        objective="Explain business performance",
        dataset_context="Rows: 10, Columns: sales, returns",
        analysis_results={"kpis": [{"label": "sales", "value": 1200}]},
    )

    response = InsightAgent(gemini_service=gemini_service).generate(request)

    assert response.executive_summary.startswith("Revenue is growing")
    assert response.business_insights[0].confidence == InsightConfidence.HIGH
    assert response.key_trends[0].metric == "sales"
    assert response.anomalies[0].affected_columns == ["returns"]
    assert response.recommendations[0].priority == "high"
    assert "Explain business performance" in gemini_service.prompt
    assert '"kpis"' in gemini_service.prompt


def test_serialize_analysis_results_handles_strings_and_json() -> None:
    assert serialize_analysis_results("already summarized") == "already summarized"
    assert '"value": 42' in serialize_analysis_results({"value": 42})


def test_serialize_analysis_results_returns_none_for_missing_results() -> None:
    assert serialize_analysis_results(None) is None


def test_insight_agent_surfaces_gemini_failures() -> None:
    request = InsightRequest(objective="Explain performance")

    with pytest.raises(RuntimeError, match="Gemini unavailable"):
        InsightAgent(gemini_service=FailingGeminiService()).generate(request)
