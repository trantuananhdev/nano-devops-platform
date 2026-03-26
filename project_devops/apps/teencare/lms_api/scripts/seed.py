from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Class, Parent, Student, Subscription


def seed(db: Session) -> None:
    if db.query(Parent).count() > 0:
        return

    p1 = Parent(name="Nguyễn Thị Lan", phone="0900000001", email="lan.parent@example.com")
    p2 = Parent(name="Trần Văn Minh", phone="0900000002", email="minh.parent@example.com")
    db.add_all([p1, p2])
    db.flush()

    s1 = Student(name="An", dob=date(2010, 5, 12), gender="male", current_grade="10", parent_id=p1.id)
    s2 = Student(name="Bình", dob=date(2011, 8, 20), gender="female", current_grade="9", parent_id=p1.id)
    s3 = Student(name="Chi", dob=date(2012, 2, 3), gender="female", current_grade="8", parent_id=p2.id)
    db.add_all([s1, s2, s3])
    db.flush()

    c1 = Class(
        name="Toán nâng cao",
        subject="Math",
        day_of_week=0,
        time_slot="18:00-19:30",
        teacher_name="Cô Hương",
        max_students=2,
    )
    c2 = Class(
        name="Tiếng Anh giao tiếp",
        subject="English",
        day_of_week=2,
        time_slot="18:00-19:00",
        teacher_name="Thầy John",
        max_students=3,
    )
    c3 = Class(
        name="Kỹ năng học tập",
        subject="Study Skills",
        day_of_week=4,
        time_slot="17:30-18:30",
        teacher_name="Cô Mai",
        max_students=2,
    )
    db.add_all([c1, c2, c3])
    db.flush()

    today = date.today()
    sub1 = Subscription(
        student_id=s1.id,
        package_name="Gói 8 buổi",
        start_date=today - timedelta(days=7),
        end_date=today + timedelta(days=30),
        total_sessions=8,
        used_sessions=0,
    )
    sub2 = Subscription(
        student_id=s2.id,
        package_name="Gói 4 buổi",
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=14),
        total_sessions=4,
        used_sessions=1,
    )
    sub3 = Subscription(
        student_id=s3.id,
        package_name="Gói 12 buổi",
        start_date=today - timedelta(days=3),
        end_date=today + timedelta(days=45),
        total_sessions=12,
        used_sessions=2,
    )
    db.add_all([sub1, sub2, sub3])


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
        db.commit()
    finally:
        db.close()
    print("Seeded OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

