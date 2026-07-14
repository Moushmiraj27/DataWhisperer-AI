from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.schemas.gemini import GeminiChatRequest, GeminiStructuredResponse
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiService,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/chat")


@router.post("/gemini", response_model=GeminiStructuredResponse, summary="Chat with Gemini")
async def chat_with_gemini(request: GeminiChatRequest) -> GeminiStructuredResponse:
    service = GeminiService(get_settings())

    try:
        return service.generate_data_chat_response(
            question=request.question,
            dataset_context=request.dataset_context,
        )
    except GeminiConfigurationError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiTimeoutError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.GATEWAY_TIMEOUT) from error
    except GeminiResponseError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
    except GeminiServiceError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
