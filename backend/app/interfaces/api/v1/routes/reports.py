from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.report_agent import ReportAgent, ReportAgentError
from backend.app.application.schemas.report import ReportRequest, ReportResponse
from backend.app.core.exceptions import ApplicationError

router = APIRouter(prefix="/reports")


@router.post("/generate", response_model=ReportResponse, summary="Generate professional AI report PDF")
async def generate_report(request: ReportRequest) -> ReportResponse:
    try:
        return ReportAgent().generate(request)
    except ReportAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
