from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.visualization_agent import VisualizationAgentError
from backend.app.application.schemas.visualization import VisualizationRequest, VisualizationResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_visualization_agent

router = APIRouter(prefix="/visualization")


@router.post("/figure", response_model=VisualizationResponse, summary="Create Plotly visualization")
async def create_visualization(request: VisualizationRequest) -> VisualizationResponse:
    try:
        return await run_in_threadpool(get_visualization_agent().execute, request)
    except VisualizationAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
