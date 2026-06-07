"""
API v1 Router — EcoIT App
"""

from fastapi import APIRouter
from api.v1.endpoints import hello

router = APIRouter(tags=["v1"])


@router.get("/ping")
async def ping():
    """Sanity check."""
    return {"pong": True}


# Register endpoints
router.include_router(hello.router, prefix="/hello-world", tags=["hello"])
