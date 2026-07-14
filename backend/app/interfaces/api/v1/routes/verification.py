from http import HTTPStatus

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from backend.app.application.agents.verification_agent import VerificationAgentError
from backend.app.application.schemas.verification import VerificationRequest, VerificationResponse
from backend.app.core.exceptions import ApplicationError
from backend.app.interfaces.api.dependencies import get_verification_agent

router = APIRouter(prefix="/verification")


@router.post("/verify", response_model=VerificationResponse, summary="Verify analysis and visualization output")
async def verify_output(request: VerificationRequest) -> VerificationResponse:
    try:
        return await run_in_threadpool(get_verification_agent().verify, request)
    except VerificationAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
