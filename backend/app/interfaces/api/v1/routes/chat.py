from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.schemas.gemini import GeminiChatRequest, GeminiStructuredResponse
from backend.app.application.schemas.memory import ChatHistoryResponse, ResetConversationResponse
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.infrastructure.persistence.conversation_memory import (
    ConversationMemory,
    ConversationMemoryError,
    build_context_with_memory,
)
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
    settings = get_settings()
    service = GeminiService(settings)
    memory = ConversationMemory(settings.chat_history_path, settings.chat_memory_limit)

    try:
        conversation_context = memory.get_recent_context(request.session_id)
        response = service.generate_data_chat_response(
            question=request.question,
            dataset_context=build_context_with_memory(request.dataset_context, conversation_context),
        )
        memory.append_exchange(request.session_id, request.question, response.answer)
        return response
    except ConversationMemoryError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from error
    except GeminiConfigurationError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiTimeoutError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.GATEWAY_TIMEOUT) from error
    except GeminiResponseError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
    except GeminiServiceError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error


@router.get("/history/{session_id}", response_model=ChatHistoryResponse, summary="Get persistent chat history")
async def get_chat_history(session_id: str) -> ChatHistoryResponse:
    settings = get_settings()
    memory = ConversationMemory(settings.chat_history_path, settings.chat_memory_limit)

    try:
        return ChatHistoryResponse(session_id=session_id, messages=memory.get_messages(session_id))
    except ConversationMemoryError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from error


@router.delete("/history/{session_id}", response_model=ResetConversationResponse, summary="Reset conversation")
async def reset_chat_history(session_id: str) -> ResetConversationResponse:
    settings = get_settings()
    memory = ConversationMemory(settings.chat_history_path, settings.chat_memory_limit)

    try:
        memory.reset(session_id)
        return ResetConversationResponse(session_id=session_id, reset=True)
    except ConversationMemoryError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from error
