from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.schemas.gemini import GeminiChatRequest, GeminiStructuredResponse
from backend.app.application.schemas.memory import ChatHistoryResponse, ResetConversationResponse
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_conversation_memory, get_gemini_service
from backend.app.infrastructure.persistence.conversation_memory import (
    ConversationMemoryError,
    build_context_with_memory,
)
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/chat")


@router.post("/gemini", response_model=GeminiStructuredResponse, summary="Chat with Gemini")
async def chat_with_gemini(request: GeminiChatRequest) -> GeminiStructuredResponse:
    settings = get_settings()
    service = get_gemini_service(settings)
    memory = get_conversation_memory(settings)

    try:
        conversation_context = await run_in_threadpool(memory.get_recent_context, request.session_id)
        response = await run_in_threadpool(
            service.generate_data_chat_response,
            request.question,
            build_context_with_memory(request.dataset_context, conversation_context),
        )
        await run_in_threadpool(memory.append_exchange, request.session_id, request.question, response.answer)
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
    memory = get_conversation_memory(settings)

    try:
        messages = await run_in_threadpool(memory.get_messages, session_id)
        return ChatHistoryResponse(session_id=session_id, messages=messages)
    except ConversationMemoryError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from error


@router.delete("/history/{session_id}", response_model=ResetConversationResponse, summary="Reset conversation")
async def reset_chat_history(session_id: str) -> ResetConversationResponse:
    settings = get_settings()
    memory = get_conversation_memory(settings)

    try:
        await run_in_threadpool(memory.reset, session_id)
        return ResetConversationResponse(session_id=session_id, reset=True)
    except ConversationMemoryError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR) from error
