"""Seed agent plans + AI audit logs cho hồ sơ UAV 198/TTr-EVNHANOI.

Phản ánh một lần chạy thẩm định AI thực tế đã hoàn thành:
  Plan 3 bước song song → đã executed → completed
  AiAuditLog: 3 tool calls với kết quả thật dựa trên pdf_text
Idempotent.
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AgentPlan, AgentPlanStatus, AiAuditLog

logger = logging.getLogger(__name__)

_TASK_ID = "seed-task-uav-198-001"

_PLAN_JSON = {
    "goal": "Thẩm định hồ sơ 198/TTr-EVNHANOI — Phê duyệt TCKT UAV phục vụ kiểm tra đường dây 220/110kV",
    "max_revisions": 2,
    "steps": [
        {
            "id": "step-1",
            "tool": "LegalGraphRAG",
            "parallel_group": None,
            "depends_on": [],
            "tool_input": {
                "query": "căn cứ pháp lý thẩm quyền phê duyệt 198/TTr-EVNHANOI UAV kiểm tra lưới điện",
                "dossier_id": 1,
                "doc_no": "198/TTr-EVNHANOI",
            },
        },
        {
            "id": "step-2",
            "tool": "TechnicalStandardCheck",
            "parallel_group": "technical",
            "depends_on": ["step-1"],
            "tool_input": {
                "query": "tiêu chuẩn kỹ thuật thiết bị bay không người lái UAV 220/110kV",
                "dossier_id": 1,
                "doc_no": "198/TTr-EVNHANOI",
            },
        },
        {
            "id": "step-3",
            "tool": "ProcurementCheck",
            "parallel_group": "technical",
            "depends_on": ["step-1"],
            "tool_input": {
                "query": "quy trình mua sắm đấu thầu UAV 4 bộ Công ty Lưới điện Cao thế",
                "dossier_id": 1,
                "doc_no": "198/TTr-EVNHANOI",
            },
        },
    ],
}

_AUDIT_LOGS = [
    {
        "task_id": _TASK_ID,
        "tool_name": "LegalGraphRAG",
        "plan_step_id": "step-1",
        "execution_time_ms": 1840,
        "inputs": {
            "query": "căn cứ pháp lý thẩm quyền phê duyệt 198/TTr-EVNHANOI",
            "dossier_id": 1,
        },
        "outputs": {
            "status": "pass",
            "score": 0.96,
            "detail": (
                "Hồ sơ đúng thẩm quyền HĐTV. Căn cứ: QĐ 8594/QĐ-EVNHANOI, NQ 180/NQ-HĐTV, "
                "Điều lệ EVNHANOI. Trình tự Ban KT → PTGĐ KT → TGĐ → HĐTV đúng quy trình."
            ),
            "references": ["QĐ 8594/QĐ-EVNHANOI", "NQ 180/NQ-HĐTV", "Điều lệ EVNHANOI 2023"],
        },
        "offset_seconds": 0,
    },
    {
        "task_id": _TASK_ID,
        "tool_name": "TechnicalStandardCheck",
        "plan_step_id": "step-2",
        "execution_time_ms": 2310,
        "inputs": {
            "query": "tiêu chuẩn kỹ thuật UAV kiểm tra đường dây 220/110kV",
            "dossier_id": 1,
        },
        "outputs": {
            "status": "warning",
            "score": 0.71,
            "detail": (
                "Yêu cầu kỹ thuật đáp ứng vận hành (bay ≥40 phút, RTK ≤1cm, LIDAR ≥480k điểm/giây). "
                "Cảnh báo: Phụ lục I dùng cả 'máy bay không người lái' và 'thiết bị bay không người lái' "
                "cho cùng đối tượng — cần thống nhất thuật ngữ."
            ),
            "warnings": ["Không nhất quán thuật ngữ trong Phụ lục I"],
        },
        "offset_seconds": 2,
    },
    {
        "task_id": _TASK_ID,
        "tool_name": "ProcurementCheck",
        "plan_step_id": "step-3",
        "execution_time_ms": 1950,
        "inputs": {
            "query": "quy trình mua sắm UAV 4 bộ đấu thầu",
            "dossier_id": 1,
        },
        "outputs": {
            "status": "warning",
            "score": 0.68,
            "detail": (
                "Khảo sát giá 4 nhà phân phối, 2 phúc đáp (Apex Tech VN + MAJ) — đạt ngưỡng tối thiểu. "
                "Cảnh báo: Phụ lục I còn dùng 'Nhà thầu', 'Hồ sơ dự thầu' — đây là TCKT, không phải "
                "hồ sơ mời thầu, cần loại bỏ để tránh nhầm lẫn pháp lý."
            ),
            "warnings": ["Ngôn ngữ đấu thầu trong văn bản tiêu chuẩn kỹ thuật"],
        },
        "offset_seconds": 2,
    },
]


async def seed_agent_plans(
    session: AsyncSession,
    dossier_id_map: dict[str, int],
) -> None:
    uav_id = dossier_id_map.get("198/TTr-EVNHANOI")
    if not uav_id:
        return

    # AgentPlan
    existing_plan = (
        await session.execute(
            select(AgentPlan).where(AgentPlan.dossier_id == uav_id)
        )
    ).scalar_one_or_none()

    if not existing_plan:
        plan = AgentPlan(
            dossier_id=uav_id,
            plan_json=_PLAN_JSON,
            revision=0,
            status=AgentPlanStatus.completed,
        )
        session.add(plan)
        logger.info("Seeded AgentPlan cho UAV 198")

    # AiAuditLogs
    existing_logs = (
        await session.execute(
            select(AiAuditLog).where(AiAuditLog.task_id == _TASK_ID)
        )
    ).scalars().all()

    if not existing_logs:
        base_ts = datetime.now(tz=timezone.utc) - timedelta(days=2, hours=3)
        for entry in _AUDIT_LOGS:
            ts = base_ts + timedelta(seconds=entry["offset_seconds"])
            log = AiAuditLog(
                task_id=_TASK_ID,
                tool_name=entry["tool_name"],
                plan_step_id=entry["plan_step_id"],
                execution_time_ms=entry["execution_time_ms"],
                inputs=entry["inputs"],
                outputs=entry["outputs"],
                error_type=None,
            )
            session.add(log)
        logger.info("Seeded %d AiAuditLogs cho UAV 198", len(_AUDIT_LOGS))

    await session.commit()
