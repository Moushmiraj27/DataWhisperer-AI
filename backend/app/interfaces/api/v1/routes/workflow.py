from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.workflow_agent import WorkflowAgent, WorkflowAgentError
from backend.app.application.schemas.workflow import WorkflowRequest, WorkflowResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_gemini_service
from backend.app.infrastructure.providers.gemini_service import (
    GeminiConfigurationError,
    GeminiResponseError,
    GeminiServiceError,
    GeminiTimeoutError,
)

router = APIRouter(prefix="/workflow")


@router.post("/run", response_model=WorkflowResponse, summary="Run full agent workflow")
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        return await run_in_threadpool(WorkflowAgent(insight_service=get_gemini_service()).run, request)
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
