from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.visualization_agent import VisualizationAgent, VisualizationAgentError
from backend.app.application.schemas.visualization import VisualizationRequest, VisualizationResponse
from backend.app.core.exceptions import ApplicationError

router = APIRouter(prefix="/visualization")


@router.post("/figure", response_model=VisualizationResponse, summary="Create Plotly visualization")
async def create_visualization(request: VisualizationRequest) -> VisualizationResponse:
    try:
        return VisualizationAgent().execute(request)
    except VisualizationAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
