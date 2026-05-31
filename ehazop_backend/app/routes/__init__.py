"""API routes."""

from ehazop_backend.app.routes.auth import router as auth_router
from ehazop_backend.app.routes.users import router as users_router
from ehazop_backend.app.routes.studies import router as studies_router
from ehazop_backend.app.routes.hazards import router as hazards_router
from ehazop_backend.app.routes.analysis import router as analysis_router
from ehazop_backend.app.routes.risk import router as risk_router
from ehazop_backend.app.routes.llm import router as llm_router
from ehazop_backend.app.routes.knowledge import router as knowledge_router
from ehazop_backend.app.routes.actions import router as actions_router
from ehazop_backend.app.routes.reports import router as reports_router
from ehazop_backend.app.routes.guidewords import router as guidewords_router
from ehazop_backend.app.routes.ws import router as ws_router

__all__ = [
    "auth_router",
    "users_router",
    "studies_router",
    "hazards_router",
    "analysis_router",
    "risk_router",
    "llm_router",
    "knowledge_router",
    "actions_router",
    "reports_router",
    "guidewords_router",
    "ws_router",
]