from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.workflow_agent import WorkflowAgent, WorkflowAgentError
from backend.app.application.schemas.workflow import WorkflowRequest, WorkflowResponse
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiService,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/workflow")


@router.post("/run", response_model=WorkflowResponse, summary="Run full agent workflow")
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        return WorkflowAgent(insight_service=GeminiService(get_settings())).run(request)
    except WorkflowAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiConfigurationError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
    except GeminiTimeoutError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.GATEWAY_TIMEOUT) from error
    except GeminiResponseError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
    except GeminiServiceError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_GATEWAY) from error
