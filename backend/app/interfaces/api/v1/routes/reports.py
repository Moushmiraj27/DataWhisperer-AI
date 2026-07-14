from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.report_agent import ReportAgentError
from backend.app.application.schemas.report import ReportRequest, ReportResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_report_agent

router = APIRouter(prefix="/reports")


@router.post("/generate", response_model=ReportResponse, summary="Generate professional AI report PDF")
async def generate_report(request: ReportRequest) -> ReportResponse:
    try:
        return await run_in_threadpool(get_report_agent().generate, request)
    except ReportAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
