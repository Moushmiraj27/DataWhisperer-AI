from fastapi import APIRouter

from backend.app.interfaces.api.v1.routes.chat import router as chat_router
from backend.app.interfaces.api.v1.routes.health import router as health_router
from backend.app.interfaces.api.v1.routes.planner import router as planner_router

api_router = APIRouter()
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(planner_router, tags=["planner"])
