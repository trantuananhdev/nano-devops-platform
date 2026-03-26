from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Parent
from ..schemas import ParentCreate, ParentOut

router = APIRouter(tags=["parents"])


@router.post("/parents", response_model=ParentOut)
def create_parent(payload: ParentCreate, db: Session = Depends(get_db)) -> Parent:
    p = Parent(name=payload.name, phone=payload.phone, email=str(payload.email) if payload.email else None)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/parents", response_model=list[ParentOut])
def list_parents(db: Session = Depends(get_db)) -> list[Parent]:
    return db.query(Parent).order_by(Parent.id.asc()).all()


@router.get("/parents/{id}", response_model=ParentOut)
def get_parent(id: int, db: Session = Depends(get_db)) -> Parent:
    p = db.get(Parent, id)
    if not p:
        raise HTTPException(status_code=404, detail="Parent not found")
    return p

