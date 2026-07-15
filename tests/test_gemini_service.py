from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.application.prompts.gemini import build_data_chat_prompt
from backend.app.application.schemas.gemini import GeminiStructuredResponse
from backend.app.core.config import Settings
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiService,
    GeminiServiceError,
    GeminiTimeoutError,
)


class FakeInteractions:
    def __init__(self, output_text: str | None = None, failures: int = 0) -> None:
        self.output_text = output_text
        self.failures = failures
        self.calls = 0

    def create(self, **_: object) -> SimpleNamespace:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("temporary failure")
        return SimpleNamespace(output_text=self.output_text)


def make_settings(**overrides: object) -> Settings:
    values = {
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "gemini-flash-lite-latest",
        "GEMINI_TIMEOUT_SECONDS": 1,
        "GEMINI_MAX_RETRIES": 2,
        "GEMINI_TEMPERATURE": 0.2,
    }
    values.update(overrides)
    return Settings(**values)


def test_gemini_service_returns_structured_response() -> None:
    payload = GeminiStructuredResponse(
        answer="The dataset has missing values.",
        summary="One column needs attention.",
        insights=[{"title": "Missing values", "detail": "Score has nulls.", "confidence": "high"}],
        suggested_questions=["Which rows are incomplete?"],
        chart_recommendations=[],
        warnings=[],
    ).model_dump()
    interactions = FakeInteractions(output_text=json.dumps(payload))
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    response = service.generate_data_chat_response("What is wrong?", "score has 2 missing values")

    assert response.answer == "The dataset has missing values."
    assert interactions.calls == 1


def test_gemini_service_retries_transient_failures() -> None:
    payload = GeminiStructuredResponse(answer="ok", summary="ok").model_dump_json()
    interactions = FakeInteractions(output_text=payload, failures=1)
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    response = service.generate_data_chat_response("Question")

    assert response.answer == "ok"
    assert interactions.calls == 2


def test_gemini_service_raises_for_invalid_structured_response() -> None:
    interactions = FakeInteractions(output_text='{"answer": 12}')
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    with pytest.raises(GeminiResponseError):
        service.generate_data_chat_response("Question")


def test_gemini_service_raises_for_empty_response() -> None:
    interactions = FakeInteractions(output_text="")
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    with pytest.raises(GeminiResponseError):
        service.generate_data_chat_response("Question")


def test_gemini_service_raises_configuration_error_without_key() -> None:
    service = GeminiService(settings=make_settings(GEMINI_API_KEY=None))

    with pytest.raises(GeminiConfigurationError):
        service.generate_data_chat_response("Question")


def test_gemini_service_raises_after_retry_exhaustion() -> None:
    interactions = FakeInteractions(output_text=None, failures=2)
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    with pytest.raises(GeminiServiceError):
        service.generate_data_chat_response("Question")


def test_gemini_service_raises_timeout_after_retries() -> None:
    class TimeoutInteractions:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **_: object) -> SimpleNamespace:
            self.calls += 1
            raise TimeoutError("slow request")

    interactions = TimeoutInteractions()
    service = GeminiService(settings=make_settings(), client=SimpleNamespace(interactions=interactions), sleep=lambda _: None)

    with pytest.raises(GeminiTimeoutError):
        service.generate_data_chat_response("Question")

    assert interactions.calls == 2


def test_prompt_template_includes_question_and_context() -> None:
    prompt = build_data_chat_prompt("What changed?", "3 rows, 2 columns")

    assert "What changed?" in prompt
    assert "3 rows, 2 columns" in prompt
