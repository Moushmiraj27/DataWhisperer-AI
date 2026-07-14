from __future__ import annotations

from typing import NotRequired, TypedDict

from backend.app.application.agents.analysis_agent import AnalysisAgent
from backend.app.application.agents.insight_agent import InsightAgent, StructuredInsightService
from backend.app.application.agents.planner_agent import PlannerAgent
from backend.app.application.agents.verification_agent import VerificationAgent
from backend.app.application.agents.visualization_agent import VisualizationAgent
from backend.app.application.schemas.analysis import AggregationFunction, AnalysisRequest, KpiSpec
from backend.app.application.schemas.insight import InsightRequest
from backend.app.application.schemas.planner import PlannerResponse
from backend.app.application.schemas.verification import VerificationRequest
from backend.app.application.schemas.visualization import VisualizationRequest
from backend.app.application.schemas.workflow import WorkflowRequest, WorkflowResponse


class WorkflowAgentError(RuntimeError):
    """Raised when the agent workflow cannot run."""


class WorkflowState(TypedDict):
    request: WorkflowRequest
    planner: NotRequired[PlannerResponse]
    analysis_request: NotRequired[AnalysisRequest]
    analysis: NotRequired[object]
    visualization_request: NotRequired[VisualizationRequest]
    visualization: NotRequired[object]
    insights: NotRequired[object]
    verification: NotRequired[object]
    response: NotRequired[WorkflowResponse]


class WorkflowAgent:
    def __init__(
        self,
        insight_service: StructuredInsightService,
        planner_agent: PlannerAgent | None = None,
        analysis_agent: AnalysisAgent | None = None,
        visualization_agent: VisualizationAgent | None = None,
        verification_agent: VerificationAgent | None = None,
    ) -> None:
        self._planner_agent = planner_agent or PlannerAgent()
        self._analysis_agent = analysis_agent or AnalysisAgent()
        self._visualization_agent = visualization_agent or VisualizationAgent()
        self._verification_agent = verification_agent or VerificationAgent(
            analysis_agent=self._analysis_agent,
            visualization_agent=self._visualization_agent,
        )
        self._insight_agent = InsightAgent(gemini_service=insight_service)
        self._graph = self._build_graph()

    def run(self, request: WorkflowRequest) -> WorkflowResponse:
        final_state = self._graph.invoke({"request": request})
        return final_state["response"]

    def _build_graph(self):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as error:
            raise WorkflowAgentError("LangGraph is not installed. Install dependencies from requirements.txt.") from error

        graph = StateGraph(WorkflowState)
        graph.add_node("planner", self._run_planner)
        graph.add_node("analysis", self._run_analysis)
        graph.add_node("visualization", self._run_visualization)
        graph.add_node("insight", self._run_insight)
        graph.add_node("verification", self._run_verification)
        graph.add_node("finalize", finalize_workflow_response)

        graph.add_edge(START, "planner")
        graph.add_edge("planner", "analysis")
        graph.add_edge("analysis", "visualization")
        graph.add_edge("visualization", "insight")
        graph.add_edge("insight", "verification")
        graph.add_edge("verification", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()

    def _run_planner(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        planner = self._planner_agent.plan(
            user_request=request.user_request,
            dataset_context=request.dataset_context or build_dataset_context(request.records),
        )
        return {**state, "planner": planner}

    def _run_analysis(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        analysis_request = request.analysis_request or build_default_analysis_request(request.records)
        analysis = self._analysis_agent.execute(analysis_request)
        return {**state, "analysis_request": analysis_request, "analysis": analysis}

    def _run_visualization(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        visualization_request = request.visualization_request or VisualizationRequest(records=request.records)
        visualization = self._visualization_agent.execute(visualization_request)
        return {**state, "visualization_request": visualization_request, "visualization": visualization}

    def _run_insight(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        analysis = state["analysis"]
        visualization = state["visualization"]
        insights = self._insight_agent.generate(
            InsightRequest(
                objective=request.user_request,
                dataset_context=request.dataset_context or build_dataset_context(request.records),
                analysis_results={
                    "analysis": analysis.model_dump(mode="json"),
                    "visualization": {
                        "chart_type": visualization.chart_type,
                        "reasoning": visualization.reasoning,
                        "warnings": visualization.warnings,
                    },
                },
            )
        )
        return {**state, "insights": insights}

    def _run_verification(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        verification = self._verification_agent.verify(
            VerificationRequest(
                records=request.records,
                expected_columns=request.expected_columns,
                required_columns=request.required_columns,
                analysis_request=state["analysis_request"],
                analysis_output=state["analysis"],
                visualization_request=state["visualization_request"],
                visualization_output=state["visualization"],
                retry_failed_operations=True,
            )
        )
        return {**state, "verification": verification}


def build_default_analysis_request(records: list[dict]) -> AnalysisRequest:
    numeric_columns = find_numeric_columns(records)
    kpis = [
        KpiSpec(column=column, function=AggregationFunction.SUM, label=f"Total {column}")
        for column in numeric_columns[:3]
    ]
    return AnalysisRequest(
        records=records,
        kpis=kpis,
        statistics_columns=numeric_columns,
        preview_rows=20,
    )


def find_numeric_columns(records: list[dict]) -> list[str]:
    if not records:
        return []

    columns = list(records[0].keys())
    numeric_columns: list[str] = []
    for column in columns:
        values = [record.get(column) for record in records if record.get(column) is not None]
        if values and all(isinstance(value, int | float) and not isinstance(value, bool) for value in values):
            numeric_columns.append(str(column))
    return numeric_columns


def build_dataset_context(records: list[dict]) -> str:
    columns = list(records[0].keys()) if records else []
    return f"Rows: {len(records)}\nColumns: {', '.join(str(column) for column in columns)}"


def finalize_workflow_response(state: WorkflowState) -> WorkflowState:
    insights = state["insights"]
    verification = state["verification"]
    warnings = [
        *state["analysis"].warnings,
        *state["visualization"].warnings,
        *verification.warnings,
    ]
    response = WorkflowResponse(
        final_summary=insights.executive_summary,
        planner=state["planner"],
        analysis=verification.verified_analysis_output or state["analysis"],
        visualization=verification.verified_visualization_output or state["visualization"],
        insights=insights,
        verification=verification,
        verified=verification.verified,
        warnings=warnings,
    )
    return {**state, "response": response}
