from fastapi import APIRouter

from app.schemas.dossier import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut()
