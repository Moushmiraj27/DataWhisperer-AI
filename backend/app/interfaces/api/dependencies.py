from __future__ import annotations

from functools import lru_cache

from backend.app.application.agents.analysis_agent import AnalysisAgent
from backend.app.application.agents.planner_agent import PlannerAgent
from backend.app.application.agents.report_agent import ReportAgent
from backend.app.application.agents.verification_agent import VerificationAgent
from backend.app.application.agents.visualization_agent import VisualizationAgent
from backend.app.core.config import Settings, get_settings
from backend.app.infrastructure.persistence.conversation_memory import ConversationMemory
from backend.app.infrastructure.providers.gemini_service import GeminiService


@lru_cache
def get_planner_agent() -> PlannerAgent:
    return PlannerAgent()


@lru_cache
def get_analysis_agent() -> AnalysisAgent:
    return AnalysisAgent()


@lru_cache
def get_visualization_agent() -> VisualizationAgent:
    return VisualizationAgent()


@lru_cache
def get_verification_agent() -> VerificationAgent:
    return VerificationAgent(
        analysis_agent=get_analysis_agent(),
        visualization_agent=get_visualization_agent(),
    )


@lru_cache
def get_report_agent() -> ReportAgent:
    return ReportAgent()


def get_gemini_service(settings: Settings | None = None) -> GeminiService:
    return GeminiService(settings or get_settings())


def get_conversation_memory(settings: Settings | None = None) -> ConversationMemory:
    resolved_settings = settings or get_settings()
    return ConversationMemory(
        history_path=resolved_settings.chat_history_path,
        memory_limit=resolved_settings.chat_memory_limit,
    )
