DATA_CHAT_SYSTEM_PROMPT = """You are DataWhisperer AI, a careful data analysis assistant.

Respond with concise, practical analysis. Use only the dataset context and user request provided.
If the available context is insufficient, say what is missing. Do not invent columns, metrics, or results.
Return output that conforms exactly to the requested JSON schema.
"""


DATA_CHAT_PROMPT_TEMPLATE = """User question:
{question}

Dataset context:
{dataset_context}

Return a structured response with:
- a direct answer
- a short summary
- actionable insights
- suggested follow-up questions
- chart recommendations when useful
- warnings for data quality or uncertainty
"""


def build_data_chat_prompt(question: str, dataset_context: str | None = None) -> str:
    context = dataset_context.strip() if dataset_context else "No dataset context was provided."
    return DATA_CHAT_PROMPT_TEMPLATE.format(question=question.strip(), dataset_context=context)
