from backend.app.application.agents.workflow_agent import WorkflowAgent, build_default_analysis_request, find_numeric_columns
from backend.app.application.schemas.insight import InsightResponse
from backend.app.application.schemas.workflow import WorkflowRequest


class FakeInsightService:
    def generate_structured_response(self, system_instruction, prompt, response_model):
        return InsightResponse(
            executive_summary="Sales performance is stable with clear regional differences.",
            business_insights=[],
            key_trends=[],
            anomalies=[],
            recommendations=[],
            limitations=[],
        )


RECORDS = [
    {"region": "West", "sales": 100, "profit": 20},
    {"region": "East", "sales": 150, "profit": 30},
    {"region": "West", "sales": 200, "profit": 40},
]


def test_find_numeric_columns_ignores_booleans_and_text() -> None:
    records = [{"name": "A", "active": True, "sales": 10}]

    assert find_numeric_columns(records) == ["sales"]


def test_build_default_analysis_request_adds_numeric_kpis() -> None:
    request = build_default_analysis_request(RECORDS)

    assert [kpi.column for kpi in request.kpis] == ["sales", "profit"]
    assert request.statistics_columns == ["sales", "profit"]


def test_workflow_agent_runs_all_agents_and_returns_final_response() -> None:
    response = WorkflowAgent(insight_service=FakeInsightService()).run(
        WorkflowRequest(
            user_request="Analyze sales and create a visualization",
            records=RECORDS,
            expected_columns=["region", "sales", "profit"],
            required_columns=["sales"],
        )
    )

    assert response.final_summary.startswith("Sales performance")
    assert response.planner.primary_intent
    assert response.analysis.row_count == 3
    assert response.visualization.figure["data"]
    assert response.insights.executive_summary
    assert response.verification.verified is True
    assert response.verified is True
