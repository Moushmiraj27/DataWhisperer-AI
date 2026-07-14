from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.planner_agent import PlannerAgent, PlannerAgentError
from backend.app.application.schemas.planner import PlannerRequest, PlannerResponse
from backend.app.core.exceptions import ApplicationError

router = APIRouter(prefix="/planner")


@router.post("/plan", response_model=PlannerResponse, summary="Create an execution plan")
async def create_execution_plan(request: PlannerRequest) -> PlannerResponse:
    try:
        return PlannerAgent().plan(
            user_request=request.request,
            dataset_context=request.dataset_context,
        )
    except PlannerAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.SERVICE_UNAVAILABLE) from error
