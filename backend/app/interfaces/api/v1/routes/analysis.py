from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.analysis_agent import AnalysisAgentError
from backend.app.application.schemas.analysis import AnalysisRequest, AnalysisResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_analysis_agent

router = APIRouter(prefix="/analysis")


@router.post("/execute", response_model=AnalysisResponse, summary="Execute Pandas analysis")
async def execute_analysis(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return await run_in_threadpool(get_analysis_agent().execute, request)
    except AnalysisAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
