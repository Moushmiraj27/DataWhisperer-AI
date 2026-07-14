from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.analysis_agent import AnalysisAgent, AnalysisAgentError
from backend.app.application.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.core.exceptions import ApplicationError

router = APIRouter(prefix="/analysis")


@router.post("/execute", response_model=AnalysisResponse, summary="Execute Pandas analysis")
async def execute_analysis(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return AnalysisAgent().execute(request)
    except AnalysisAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
