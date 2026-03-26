from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class ParentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None


class ParentOut(BaseModel):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dob: date | None = None
    gender: str | None = Field(default=None, max_length=20)
    current_grade: str | None = Field(default=None, max_length=50)
    parent_id: int


class StudentOut(BaseModel):
    id: int
    name: str
    dob: date | None = None
    gender: str | None = None
    current_grade: str | None = None
    parent_id: int
    parent: ParentOut

    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=100)
    day_of_week: int = Field(ge=0, le=6)
    time_slot: str = Field(min_length=3, max_length=50)
    teacher_name: str = Field(min_length=1, max_length=200)
    max_students: int = Field(ge=1, le=500)


class ClassOut(BaseModel):
    id: int
    name: str
    subject: str
    day_of_week: int
    time_slot: str
    teacher_name: str
    max_students: int

    model_config = {"from_attributes": True}


class RegistrationCreate(BaseModel):
    student_id: int
    scheduled_at: datetime | None = None


class RegistrationOut(BaseModel):
    id: int
    class_id: int
    student_id: int
    created_at: datetime
    scheduled_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionCreate(BaseModel):
    student_id: int
    package_name: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date
    total_sessions: int = Field(ge=1, le=10000)


class SubscriptionOut(BaseModel):
    id: int
    student_id: int
    package_name: str
    start_date: date
    end_date: date
    total_sessions: int
    used_sessions: int

    model_config = {"from_attributes": True}


class SubscriptionUseOut(BaseModel):
    id: int
    used_sessions: int
    total_sessions: int


class SessionCreate(BaseModel):
    student_id: int | None = None
    class_id: int | None = None
    raw_transcript: str = Field(min_length=1)


class SessionOut(BaseModel):
    id: int
    student_id: int | None = None
    class_id: int | None = None
    raw_transcript: str
    created_at: datetime
    insight_json: str | None = None
    flag: str | None = None
    confidence: str | None = None
    risk_level: str | None = None

    model_config = {"from_attributes": True}

