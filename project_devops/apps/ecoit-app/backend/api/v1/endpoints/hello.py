"""Hello endpoint — EcoIT Hello World test."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
async def hello():
    """Simple hello world — verifies full stack is working."""
    return {
        "message": "Hello from EcoIT Backend! 🚀",
        "stack": "FastAPI + PostgreSQL + Redis",
        "status": "running",
        "platform": "Nano DevOps — Acer Ubuntu",
    }


@router.get("/hello/{name}")
async def hello_name(name: str):
    return {"message": f"Xin chào, {name}! EcoIT stack đang chạy tốt ✅"}
