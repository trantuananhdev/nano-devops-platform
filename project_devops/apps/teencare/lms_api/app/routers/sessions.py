from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import SessionRecord
from ..schemas import SessionCreate, SessionOut

router = APIRouter(tags=["sessions"])


def _ensure_teencare_ai_importable() -> None:
    """
    In monorepo layout, `teencare_ai` lives in `apps/teencare/src`.
    For local (non-docker) runs of `lms_api`, add that path if missing.
    """
    app_root = Path(__file__).resolve().parents[3]  # .../lms_api/app/routers -> .../teencare
    src_path = app_root / "src"
    if src_path.is_dir() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _run_pipeline(raw_transcript: str, teen_id: str = "teen_demo_001", family_goals: list[str] | None = None) -> dict[str, Any]:
    _ensure_teencare_ai_importable()
    try:
        from teencare_ai.core.pipeline import run_pipeline  # type: ignore
        from teencare_ai.core.types import PipelineConfig  # type: ignore
        from teencare_ai.storage.profiles import JsonProfileStore  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"teencare_ai not available: {e}")

    # Senior Fix: Use absolute path for profiles to avoid 500 in container
    app_root = Path(__file__).resolve().parents[3]  # .../teencare
    profile_path = app_root / "samples" / "profiles" / "teens.json"
    
    # If path doesn't exist (e.g. running outside of docker or different layout), fallback to relative
    if not profile_path.exists():
        profile_path = Path("samples/profiles/teens.json")

    session_input = {
        "session_id": "lms_session",
        "teen_id": teen_id,
        "raw_transcript": raw_transcript,
        "session_date": datetime.now().strftime("%Y-%m-%d"),
        "family_goals": family_goals or [],
    }
    cfg = PipelineConfig()
    
    try:
        p_store = JsonProfileStore(str(profile_path))
        return run_pipeline(session_input, config=cfg, profile_store=p_store)
    except Exception as e:
        # Fallback if profile store fails
        return run_pipeline(session_input, config=cfg)


@router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionRecord:
    try:
        out = _run_pipeline(payload.raw_transcript)
    except Exception as e:
        # Catch internal pipeline errors and provide helpful feedback
        raise HTTPException(
            status_code=500, 
            detail=f"AI Pipeline failed: {str(e)}. Check your API keys and environment variables."
        )

    rec = SessionRecord(
        student_id=payload.student_id,
        class_id=payload.class_id,
        raw_transcript=payload.raw_transcript,
        insight_json=json.dumps(out, ensure_ascii=False),
        flag=(out.get("flag") or None),
        confidence=(out.get("confidence") or None),
        risk_level=(out.get("risk_level") or None),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/sessions/{id}", response_model=SessionOut)
def get_session(id: int, db: Session = Depends(get_db)) -> SessionRecord:
    rec = db.get(SessionRecord, id)
    if not rec:
        raise HTTPException(status_code=404, detail="Session not found")
    return rec


@router.post("/sessions/import", response_model=SessionOut)
async def import_session_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> SessionRecord:
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    raw = (await file.read()).decode("utf-8", errors="replace").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    out = _run_pipeline(raw)
    rec = SessionRecord(
        raw_transcript=raw,
        insight_json=json.dumps(out, ensure_ascii=False),
        flag=(out.get("flag") or None),
        confidence=(out.get("confidence") or None),
        risk_level=(out.get("risk_level") or None),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

