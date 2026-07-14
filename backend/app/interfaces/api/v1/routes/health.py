from fastapi import APIRouter

from backend.app.core.config import get_settings

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }
