from __future__ import annotations

from typing import NotRequired, TypedDict

from backend.app.application.schemas.planner import ExecutionStep, PlannerIntent, PlannerResponse


class PlannerAgentError(RuntimeError):
    """Raised when the planner agent cannot run."""


class PlannerState(TypedDict):
    request: str
    dataset_context: str | None
    scores: NotRequired[dict[PlannerIntent, int]]
    intents: NotRequired[list[PlannerIntent]]
    confidence: NotRequired[float]
    reasoning: NotRequired[str]
    execution_plan: NotRequired[list[ExecutionStep]]
    requires_dataset: NotRequired[bool]
    clarification_questions: NotRequired[list[str]]
    response: NotRequired[PlannerResponse]


INTENT_KEYWORDS: dict[PlannerIntent, tuple[str, ...]] = {
    PlannerIntent.STATISTICS: (
        "average",
        "correlation",
        "count",
        "describe",
        "distribution",
        "mean",
        "median",
        "mode",
        "percentile",
        "standard deviation",
        "statistics",
        "summary",
        "variance",
    ),
    PlannerIntent.VISUALIZATION: (
        "bar chart",
        "boxplot",
        "chart",
        "graph",
        "heatmap",
        "histogram",
        "line chart",
        "plot",
        "scatter",
        "visual",
        "visualize",
    ),
    PlannerIntent.FILTERING: (
        "between",
        "exclude",
        "filter",
        "greater than",
        "less than",
        "only",
        "remove rows",
        "select",
        "subset",
        "where",
    ),
    PlannerIntent.AGGREGATION: (
        "aggregate",
        "by",
        "group",
        "group by",
        "max",
        "min",
        "per",
        "pivot",
        "roll up",
        "sum",
        "total",
    ),
    PlannerIntent.DATA_CLEANING: (
        "clean",
        "deduplicate",
        "duplicate",
        "fill",
        "impute",
        "missing",
        "null",
        "outlier",
        "standardize",
        "type conversion",
    ),
    PlannerIntent.RECOMMENDATION: (
        "best",
        "next",
        "recommend",
        "should",
        "suggest",
        "what should",
        "which",
    ),
    PlannerIntent.REPORT_GENERATION: (
        "dashboard",
        "export",
        "generate report",
        "pdf",
        "presentation",
        "report",
        "summarize findings",
        "write",
    ),
}


PLAN_TEMPLATES: dict[PlannerIntent, tuple[str, str, list[str], str]] = {
    PlannerIntent.STATISTICS: (
        "Compute summary statistics",
        "Calculate descriptive statistics and relevant numeric relationships.",
        ["loaded dataset", "selected columns or all columns"],
        "Statistics table and concise interpretation",
    ),
    PlannerIntent.VISUALIZATION: (
        "Create visualizations",
        "Select chart types and produce visual encodings for the requested analysis.",
        ["loaded dataset", "chart columns", "chart type"],
        "Visualization specification and rendered chart",
    ),
    PlannerIntent.FILTERING: (
        "Apply filters",
        "Identify filter conditions and create the matching row subset.",
        ["loaded dataset", "filter criteria"],
        "Filtered dataset preview and row count",
    ),
    PlannerIntent.AGGREGATION: (
        "Aggregate data",
        "Group records and compute aggregate measures.",
        ["loaded dataset", "grouping columns", "aggregate measures"],
        "Aggregated table",
    ),
    PlannerIntent.DATA_CLEANING: (
        "Assess and clean data",
        "Detect missing values, duplicates, invalid types, and outliers before proposing cleaning actions.",
        ["loaded dataset", "cleaning policy"],
        "Data quality findings and cleaning recommendations",
    ),
    PlannerIntent.RECOMMENDATION: (
        "Generate recommendations",
        "Use analysis outputs to recommend next actions or questions.",
        ["analysis results", "business goal"],
        "Ranked recommendations with rationale",
    ),
    PlannerIntent.REPORT_GENERATION: (
        "Generate report",
        "Assemble findings, visuals, and recommendations into a report-ready structure.",
        ["analysis outputs", "target audience", "report format"],
        "Structured report outline",
    ),
}


DATASET_REQUIRED_INTENTS = {
    PlannerIntent.STATISTICS,
    PlannerIntent.VISUALIZATION,
    PlannerIntent.FILTERING,
    PlannerIntent.AGGREGATION,
    PlannerIntent.DATA_CLEANING,
}


class PlannerAgent:
    def __init__(self) -> None:
        self._graph = self._build_graph()

    def plan(self, user_request: str, dataset_context: str | None = None) -> PlannerResponse:
        initial_state: PlannerState = {
            "request": user_request.strip(),
            "dataset_context": dataset_context,
        }
        final_state = self._graph.invoke(initial_state)
        return final_state["response"]

    def _build_graph(self):
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as error:
            raise PlannerAgentError("LangGraph is not installed. Install dependencies from requirements.txt.") from error

        graph = StateGraph(PlannerState)
        graph.add_node("classify_request", classify_request)
        graph.add_node("build_execution_plan", build_execution_plan)
        graph.add_node("finalize_response", finalize_response)

        graph.add_edge(START, "classify_request")
        graph.add_edge("classify_request", "build_execution_plan")
        graph.add_edge("build_execution_plan", "finalize_response")
        graph.add_edge("finalize_response", END)

        return graph.compile()


def classify_request(state: PlannerState) -> PlannerState:
    request = state["request"].lower()
    scores = score_intents(request)
    ranked_intents = [intent for intent, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score > 0]

    if not ranked_intents:
        ranked_intents = [PlannerIntent.STATISTICS]

    primary_score = max(scores.values()) if scores else 0
    total_score = sum(scores.values()) or 1
    confidence = min(0.95, max(0.35, primary_score / total_score))

    return {
        **state,
        "scores": scores,
        "intents": ranked_intents,
        "confidence": round(confidence, 2),
        "reasoning": build_reasoning(ranked_intents, scores),
    }


def score_intents(request: str) -> dict[PlannerIntent, int]:
    scores: dict[PlannerIntent, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for keyword in keywords if keyword in request)
    return scores


def build_reasoning(intents: list[PlannerIntent], scores: dict[PlannerIntent, int]) -> str:
    primary_intent = intents[0]
    matched = scores.get(primary_intent, 0)

    if matched == 0:
        return "No explicit intent keywords were found, so the request defaults to a statistics-oriented plan."

    secondary = [intent.value for intent in intents[1:3]]
    if secondary:
        return f"Matched {matched} signal(s) for {primary_intent.value}; also detected {', '.join(secondary)}."
    return f"Matched {matched} signal(s) for {primary_intent.value}."


def build_execution_plan(state: PlannerState) -> PlannerState:
    intents = state["intents"]
    execution_plan = [
        build_step(order=index + 1, intent=intent)
        for index, intent in enumerate(intents)
    ]
    requires_dataset = any(intent in DATASET_REQUIRED_INTENTS for intent in intents)
    clarification_questions = build_clarification_questions(
        request=state["request"],
        dataset_context=state.get("dataset_context"),
        requires_dataset=requires_dataset,
    )

    return {
        **state,
        "execution_plan": execution_plan,
        "requires_dataset": requires_dataset,
        "clarification_questions": clarification_questions,
    }


def build_step(order: int, intent: PlannerIntent) -> ExecutionStep:
    action, description, inputs_required, expected_output = PLAN_TEMPLATES[intent]
    return ExecutionStep(
        order=order,
        action=action,
        intent=intent,
        description=description,
        inputs_required=inputs_required,
        expected_output=expected_output,
    )


def build_clarification_questions(
    request: str,
    dataset_context: str | None,
    requires_dataset: bool,
) -> list[str]:
    questions: list[str] = []
    if requires_dataset and not dataset_context:
        questions.append("Which uploaded dataset should this plan use?")

    lowered_request = request.lower()
    if "report" in lowered_request and "format" not in lowered_request:
        questions.append("What report format should be generated?")

    return questions


def finalize_response(state: PlannerState) -> PlannerState:
    intents = state["intents"]
    response = PlannerResponse(
        primary_intent=intents[0],
        intents=intents,
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        execution_plan=state["execution_plan"],
        requires_dataset=state["requires_dataset"],
        clarification_questions=state["clarification_questions"],
    )
    return {**state, "response": response}
