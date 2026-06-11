"""T-23: Role-based agent profile prompts for HDTV appraisal."""

from app.services.orchestrator.prompts import admin, dept_head, hdtv_leader, specialist

ROLE_MODULES = {
    "hdtv_leader": hdtv_leader,
    "dept_head": dept_head,
    "specialist": specialist,
    "admin": admin,
}

__all__ = ["ROLE_MODULES", "admin", "dept_head", "hdtv_leader", "specialist"]
