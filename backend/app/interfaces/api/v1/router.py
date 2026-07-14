from fastapi import APIRouter

from backend.app.interfaces.api.v1.routes.analysis import router as analysis_router
from backend.app.interfaces.api.v1.routes.chat import router as chat_router
from backend.app.interfaces.api.v1.routes.health import router as health_router
from backend.app.interfaces.api.v1.routes.insights import router as insights_router
from backend.app.interfaces.api.v1.routes.planner import router as planner_router
from backend.app.interfaces.api.v1.routes.verification import router as verification_router
from backend.app.interfaces.api.v1.routes.visualization import router as visualization_router

api_router = APIRouter()
api_router.include_router(analysis_router, tags=["analysis"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(insights_router, tags=["insights"])
api_router.include_router(planner_router, tags=["planner"])
api_router.include_router(verification_router, tags=["verification"])
api_router.include_router(visualization_router, tags=["visualization"])
