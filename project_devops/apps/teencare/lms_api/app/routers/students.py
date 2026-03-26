from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Parent, Student
from ..schemas import StudentCreate, StudentOut

router = APIRouter(tags=["students"])


@router.post("/students", response_model=StudentOut)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> Student:
    parent = db.get(Parent, payload.parent_id)
    if not parent:
        raise HTTPException(status_code=400, detail="parent_id not found")

    s = Student(
        name=payload.name,
        dob=payload.dob,
        gender=payload.gender,
        current_grade=payload.current_grade,
        parent_id=payload.parent_id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    s = (
        db.query(Student)
        .options(joinedload(Student.parent))
        .filter(Student.id == s.id)
        .one()
    )
    return s


@router.get("/students", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)) -> list[Student]:
    return (
        db.query(Student)
        .options(joinedload(Student.parent))
        .order_by(Student.id.asc())
        .all()
    )


@router.get("/students/{id}", response_model=StudentOut)
def get_student(id: int, db: Session = Depends(get_db)) -> Student:
    s = (
        db.query(Student)
        .options(joinedload(Student.parent))
        .filter(Student.id == id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s

