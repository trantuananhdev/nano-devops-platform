from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Student, Subscription
from ..schemas import SubscriptionCreate, SubscriptionOut, SubscriptionUseOut

router = APIRouter(tags=["subscriptions"])


@router.post("/subscriptions", response_model=SubscriptionOut)
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)) -> Subscription:
    s = db.get(Student, payload.student_id)
    if not s:
        raise HTTPException(status_code=400, detail="student_id not found")
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    sub = Subscription(
        student_id=payload.student_id,
        package_name=payload.package_name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_sessions=payload.total_sessions,
        used_sessions=0,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(db: Session = Depends(get_db)) -> list[Subscription]:
    return db.query(Subscription).order_by(Subscription.id.asc()).all()


@router.get("/subscriptions/{id}", response_model=SubscriptionOut)
def get_subscription(id: int, db: Session = Depends(get_db)) -> Subscription:
    sub = db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.patch("/subscriptions/{id}/use", response_model=SubscriptionUseOut)
def use_one_session(id: int, db: Session = Depends(get_db)) -> SubscriptionUseOut:
    sub = db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub.used_sessions >= sub.total_sessions:
        raise HTTPException(status_code=400, detail="No remaining sessions")
    sub.used_sessions += 1
    db.commit()
    return SubscriptionUseOut(id=sub.id, used_sessions=sub.used_sessions, total_sessions=sub.total_sessions)

