from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Class
from ..schemas import ClassCreate, ClassOut
from ..services import parse_time_slot

router = APIRouter(tags=["classes"])


@router.post("/classes", response_model=ClassOut)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)) -> Class:
    try:
        parse_time_slot(payload.time_slot)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    c = Class(
        name=payload.name,
        subject=payload.subject,
        day_of_week=payload.day_of_week,
        time_slot=payload.time_slot,
        teacher_name=payload.teacher_name,
        max_students=payload.max_students,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/classes", response_model=list[ClassOut])
def list_classes(
    day: int | None = Query(default=None, ge=0, le=6),
    db: Session = Depends(get_db),
) -> list[Class]:
    q = db.query(Class)
    if day is not None:
        q = q.filter(Class.day_of_week == int(day))
    return q.order_by(Class.day_of_week.asc(), Class.time_slot.asc()).all()

