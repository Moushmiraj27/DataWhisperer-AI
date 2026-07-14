INSIGHT_SYSTEM_PROMPT = """You are DataWhisperer AI's InsightAgent.

Explain analytical results for a business user. Ground every statement in the provided dataset profile,
analysis output, and user objective. Do not invent metrics, entities, or trends.
Return output that conforms exactly to the requested JSON schema.
"""


INSIGHT_PROMPT_TEMPLATE = """User objective:
{objective}

Dataset context:
{dataset_context}

Analysis results:
{analysis_results}

Generate:
- business insights
- key trends
- anomalies
- recommendations
- a concise executive explanation
"""


def build_insight_prompt(
    objective: str,
    dataset_context: str | None = None,
    analysis_results: str | None = None,
) -> str:
    return INSIGHT_PROMPT_TEMPLATE.format(
        objective=objective.strip(),
        dataset_context=dataset_context.strip() if dataset_context else "No dataset context was provided.",
        analysis_results=analysis_results.strip() if analysis_results else "No analysis results were provided.",
    )
