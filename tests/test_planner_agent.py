from backend.app.application.agents.planner_agent import PlannerAgent, build_step, score_intents
from backend.app.application.schemas.planner import PlannerIntent


def test_score_intents_detects_requested_categories() -> None:
    scores = score_intents("filter rows, group by city, and plot a chart")

    assert scores[PlannerIntent.FILTERING] > 0
    assert scores[PlannerIntent.AGGREGATION] > 0
    assert scores[PlannerIntent.VISUALIZATION] > 0


def test_planner_agent_returns_execution_plan() -> None:
    response = PlannerAgent().plan(
        user_request="Clean missing values and generate a report",
        dataset_context="Rows: 100, Columns: age, score",
    )

    assert response.primary_intent == PlannerIntent.DATA_CLEANING
    assert PlannerIntent.REPORT_GENERATION in response.intents
    assert response.execution_plan[0].order == 1
    assert response.requires_dataset is True


def test_planner_agent_defaults_to_statistics_for_ambiguous_request() -> None:
    response = PlannerAgent().plan("Tell me about this file")

    assert response.primary_intent == PlannerIntent.STATISTICS
    assert response.clarification_questions == ["Which uploaded dataset should this plan use?"]


def test_planner_agent_classifies_all_supported_categories() -> None:
    request = (
        "Show statistics, visualize a chart, filter rows, group by category, "
        "clean missing values, recommend next actions, and generate a PDF report."
    )

    response = PlannerAgent().plan(request, dataset_context="Rows: 10, Columns: category, sales")

    assert set(response.intents) == set(PlannerIntent)
    assert response.requires_dataset is True
    assert [step.order for step in response.execution_plan] == list(range(1, len(response.execution_plan) + 1))


def test_build_step_uses_template_metadata() -> None:
    step = build_step(order=1, intent=PlannerIntent.AGGREGATION)

    assert step.action == "Aggregate data"
    assert step.intent == PlannerIntent.AGGREGATION
    assert "grouping columns" in step.inputs_required
