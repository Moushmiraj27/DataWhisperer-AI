from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.insight_agent import InsightAgent
from backend.app.application.schemas.insight import InsightRequest, InsightResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_gemini_service
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/insights")


@router.post("/generate", response_model=InsightResponse, summary="Generate business insights")
async def generate_insights(request: InsightRequest) -> InsightResponse:
    agent = InsightAgent(gemini_service=get_gemini_service())

    try:
        return await run_in_threadpool(agent.generate, request)
    except GeminiConfigurationError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiTimeoutError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.GATEWAY_TIMEOUT) from error
    except GeminiResponseError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
    except GeminiServiceError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
