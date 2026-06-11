from fastapi import APIRouter

from app.routers import alerts, api_keys, audit, clarifications, dossiers, feedback, health, mcp, meta, search, workflow

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dossiers.router, prefix="/dossiers", tags=["dossiers"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(search.router, tags=["search"])  # T-11
api_router.include_router(workflow.router, tags=["workflow"])  # T-12
api_router.include_router(feedback.router, tags=["feedback"])  # T-20
api_router.include_router(clarifications.router, tags=["clarifications"])  # T-22
api_router.include_router(api_keys.router, tags=["api-keys"])  # T-33
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])  # T-29, T-36
