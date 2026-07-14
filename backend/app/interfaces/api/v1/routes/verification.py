from http import HTTPStatus

from fastapi import APIRouter

from backend.app.application.agents.verification_agent import VerificationAgent, VerificationAgentError
from backend.app.application.schemas.verification import VerificationRequest, VerificationResponse
from backend.app.core.exceptions import ApplicationError

router = APIRouter(prefix="/verification")


@router.post("/verify", response_model=VerificationResponse, summary="Verify analysis and visualization output")
async def verify_output(request: VerificationRequest) -> VerificationResponse:
    try:
        return VerificationAgent().verify(request)
    except VerificationAgentError as error:
        raise ApplicationError(str(error), status_code=HTTPStatus.BAD_REQUEST) from error
