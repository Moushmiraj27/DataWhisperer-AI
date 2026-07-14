from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from backend.app.application.prompts.gemini import DATA_CHAT_SYSTEM_PROMPT, build_data_chat_prompt
from backend.app.application.schemas.gemini import GeminiStructuredResponse
from backend.app.core.config import Settings

logger = logging.getLogger(__name__)


class GeminiServiceError(RuntimeError):
    """Base exception for Gemini service failures."""


class GeminiConfigurationError(GeminiServiceError):
    """Raised when Gemini is not configured."""


class GeminiTimeoutError(GeminiServiceError):
    """Raised when Gemini does not respond in time."""


class GeminiResponseError(GeminiServiceError):
    """Raised when Gemini returns an invalid structured response."""


class GeminiService:
    def __init__(
        self,
        settings: Settings,
        client: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._client = client
        self._sleep = sleep

    def generate_data_chat_response(
        self,
        question: str,
        dataset_context: str | None = None,
    ) -> GeminiStructuredResponse:
        prompt = build_data_chat_prompt(question=question, dataset_context=dataset_context)
        response_schema = GeminiStructuredResponse.model_json_schema()
        last_error: Exception | None = None

        for attempt in range(1, self._settings.gemini_max_retries + 1):
            try:
                interaction = self._get_client().interactions.create(
                    model=self._settings.gemini_model,
                    system_instruction=DATA_CHAT_SYSTEM_PROMPT,
                    input=prompt,
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": response_schema,
                    },
                    generation_config={
                        "temperature": self._settings.gemini_temperature,
                    },
                )
                return self._parse_structured_response(interaction)
            except GeminiResponseError:
                raise
            except TimeoutError as error:
                last_error = error
                logger.warning("Gemini request timed out on attempt %s.", attempt)
            except Exception as error:
                last_error = error
                logger.warning("Gemini request failed on attempt %s: %s", attempt, error)

            if attempt < self._settings.gemini_max_retries:
                self._sleep(min(2 ** (attempt - 1), 8))

        if isinstance(last_error, TimeoutError):
            raise GeminiTimeoutError("Gemini request timed out.") from last_error

        raise GeminiServiceError("Gemini request failed after retries.") from last_error

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        if not self._settings.gemini_api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is not configured.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise GeminiConfigurationError("google-genai is not installed.") from error

        timeout_ms = int(self._settings.gemini_timeout_seconds * 1000)
        retry_options = types.HttpRetryOptions(
            attempts=self._settings.gemini_max_retries,
            initial_delay=1,
            max_delay=8,
            exp_base=2,
            jitter=0.2,
            http_status_codes=[429, 500, 502, 503, 504],
        )

        return genai.Client(
            api_key=self._settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=timeout_ms, retry_options=retry_options),
        )

    @staticmethod
    def _parse_structured_response(interaction: Any) -> GeminiStructuredResponse:
        output_text = getattr(interaction, "output_text", None)
        if not output_text:
            raise GeminiResponseError("Gemini returned an empty response.")

        try:
            return GeminiStructuredResponse.model_validate_json(output_text)
        except ValidationError as error:
            raise GeminiResponseError("Gemini returned an invalid structured response.") from error
