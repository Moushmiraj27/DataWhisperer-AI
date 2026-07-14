from __future__ import annotations

import json
from typing import Protocol

from backend.app.application.prompts.insights import INSIGHT_SYSTEM_PROMPT, build_insight_prompt
from backend.app.application.schemas.insight import InsightRequest, InsightResponse


class InsightAgentError(RuntimeError):
    """Raised when insight generation fails."""


class StructuredInsightService(Protocol):
    def generate_structured_response(
        self,
        system_instruction: str,
        prompt: str,
        response_model: type[InsightResponse],
    ) -> InsightResponse:
        ...


class InsightAgent:
    def __init__(self, gemini_service: StructuredInsightService) -> None:
        self._gemini_service = gemini_service

    def generate(self, request: InsightRequest) -> InsightResponse:
        prompt = build_insight_prompt(
            objective=request.objective,
            dataset_context=request.dataset_context,
            analysis_results=serialize_analysis_results(request.analysis_results),
        )
        return self._gemini_service.generate_structured_response(
            system_instruction=INSIGHT_SYSTEM_PROMPT,
            prompt=prompt,
            response_model=InsightResponse,
        )


def serialize_analysis_results(results) -> str | None:
    if results is None:
        return None
    if isinstance(results, str):
        return results
    return json.dumps(results, indent=2, default=str)
