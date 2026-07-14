from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.insight_agent import InsightAgent
from backend.app.application.schemas.insight import InsightRequest, InsightResponse
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiService,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/insights")


@router.post("/generate", response_model=InsightResponse, summary="Generate business insights")
async def generate_insights(request: InsightRequest) -> InsightResponse:
    agent = InsightAgent(gemini_service=GeminiService(get_settings()))

    try:
        return agent.generate(request)
    except GeminiConfigurationError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiTimeoutError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.GATEWAY_TIMEOUT) from error
    except GeminiResponseError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
    except GeminiServiceError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
