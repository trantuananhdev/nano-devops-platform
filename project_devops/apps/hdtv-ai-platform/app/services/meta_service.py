from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AiAuditLog, Alert, AlertStatus, Dossier, DossierStatus, RiskLevel, ToolConfig, User, UserRole
)
from app.schemas.meta import (
    ChecklistItemOut,
    DashboardSummaryOut,
    GraphEdgeOut,
    GraphNodeOut,
    KnowledgeGraphOut,
    RoleOut,
    ScheduleJobOut,
    SkillTemplateOut,
    SystemLogOut,
    ToolOut,
    UserOut,
)
from app.services.tools.base import list_tools
from app.services.tools.legal_rag import LEGAL_FALLBACK

DEFAULT_CHECKLIST: list[ChecklistItemOut] = [
    ChecklistItemOut(id=1, text="Đối chiếu Tổng mức đầu tư với hệ thống ERP", type="auto", is_required=True),
    ChecklistItemOut(id=2, text="Kiểm tra hiệu lực văn bản pháp lý căn cứ", type="auto", is_required=True),
    ChecklistItemOut(id=3, text="Xác minh chữ ký điện tử Ban Tài chính Kế toán", type="manual", is_required=True),
    ChecklistItemOut(id=4, text="Kiểm tra file Báo cáo nghiên cứu khả thi (FS)", type="auto", is_required=True),
    ChecklistItemOut(id=5, text="Đánh giá tác động chỉ tiêu vận hành (SAIDI/SAIFI)", type="auto", is_required=False),
]

SCHEDULE_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Quét tự động Hồ sơ chờ Duyệt",
        "cron": "0 * * * *",
        "schedule_text": "Hàng giờ",
        "tools": ["EcoOcrExtract", "LegalGraphRAG"],
        "status": "active",
        "description": "Quét DOffice, bóc tách nội dung và gắn nhãn tự động cho tờ trình mới.",
    },
    {
        "id": 2,
        "name": "Báo cáo Cảnh báo Tồn kho & Ngân sách",
        "cron": "0 8 * * 1",
        "schedule_text": "Hàng tuần (Thứ Hai, 08:00)",
        "tools": ["ErpInventoryCheck", "ErpBudgetCheck", "DOfficeLookup"],
        "status": "active",
        "description": "Tổng hợp cảnh báo vật tư ứ đọng và vượt ngân sách, gửi báo cáo Ban Giám đốc.",
    },
    {
        "id": 3,
        "name": "Đồng bộ Dữ liệu Đấu thầu",
        "cron": "0 2 * * *",
        "schedule_text": "Hàng ngày (02:00)",
        "tools": ["PmisProjectCheck", "LegalGraphRAG"],
        "status": "paused",
        "description": "Đối soát gói thầu và căn cứ pháp lý đấu thầu với kho tri thức nội bộ.",
    },
]

STATUS_LABELS = {
    DossierStatus.pending: "Chờ duyệt",
    DossierStatus.appraising: "Đang thẩm định",
    DossierStatus.approved: "Đã thông qua",
    DossierStatus.needs_revision: "Bổ sung hồ sơ",
}

RISK_LABELS = {
    RiskLevel.high: "Cao",
    RiskLevel.medium: "Trung bình",
    RiskLevel.low: "Thấp",
}

TOOL_META = {
    "ErpBudgetCheck": {
        "description": "Đối chiếu ngân sách ERP PS",
        "category": "erp"
    },
    "ErpInventoryCheck": {
        "description": "Kiểm tra tồn kho ERP MM",
        "category": "erp"
    },
    "DOfficeLookup": {
        "description": "Tra cứu văn bản DOffice",
        "category": "integration"
    },
    "PmisProjectCheck": {
        "description": "Kiểm tra dự án PMIS",
        "category": "integration"
    },
    "LegalGraphRAG": {
        "description": "Tra cứu pháp lý GraphRAG",
        "category": "rag"
    },
    "EcoOcrExtract": {
        "description": "Trích xuất OCR từ PDF",
        "category": "ocr"
    },
}


async def list_tool_registry(session: AsyncSession) -> list[ToolOut]:
    # Get tool usage stats
    usage_rows = await session.execute(
        select(
            AiAuditLog.tool_name,
            func.count(AiAuditLog.id),
            func.max(AiAuditLog.created_at),
        ).group_by(AiAuditLog.tool_name)
    )
    usage_map = {
        row[0]: {"count": row[1], "last": row[2]}
        for row in usage_rows.all()
    }
    
    # Get active tools from database
    tool_configs = await session.execute(
        select(ToolConfig).where(ToolConfig.is_active.is_(True)).order_by(ToolConfig.priority.desc(), ToolConfig.name)
    )
    tool_configs = tool_configs.scalars().all()
    
    tools: list[ToolOut] = []
    for tool in tool_configs:
        usage = usage_map.get(tool.name, {})
        last = usage.get("last")
        tools.append(
            ToolOut(
                name=tool.name,
                description=tool.description,
                category=tool.category,
                status="active" if usage.get("count", 0) > 0 else "ready",
                usage_count=usage.get("count", 0),
                last_used_at=last.isoformat() if isinstance(last, datetime) else None,
            )
        )
    return tools


async def build_knowledge_graph(session: AsyncSession, dossier_id: int) -> KnowledgeGraphOut | None:
    dossier = await session.get(Dossier, dossier_id)
    if not dossier:
        return None

    nodes: list[GraphNodeOut] = [
        GraphNodeOut(
            id=f"dossier-{dossier.id}",
            type="dossier",
            label=dossier.doc_no,
            desc=dossier.title[:60],
            x=400,
            y=300,
        )
    ]
    edges: list[GraphEdgeOut] = []

    for i, doc in enumerate(LEGAL_FALLBACK):
        node_id = f"legal-{i}"
        nodes.append(
            GraphNodeOut(
                id=node_id,
                type="legal",
                label=doc["title"],
                desc=doc["snippet"][:50],
                x=150 + i * 120,
                y=150,
            )
        )
        edges.append(
            GraphEdgeOut(
                source=f"dossier-{dossier.id}",
                target=node_id,
                label="Căn cứ theo",
            )
        )

    audit_rows = await session.execute(
        select(AiAuditLog.tool_name)
        .where(AiAuditLog.tool_name != "LegalGraphRAG")
        .order_by(AiAuditLog.id.desc())
        .limit(4)
    )
    tool_names = list(dict.fromkeys(audit_rows.scalars().all()))
    for i, tool_name in enumerate(tool_names):
        node_id = f"tool-{tool_name}"
        meta = TOOL_META.get(tool_name, {"description": tool_name, "category": "data"})
        nodes.append(
            GraphNodeOut(
                id=node_id,
                type="data",
                label=tool_name,
                desc=meta["description"][:50],
                x=650,
                y=120 + i * 90,
            )
        )
        edges.append(
            GraphEdgeOut(
                source=f"dossier-{dossier.id}",
                target=node_id,
                label="Đối chiếu",
            )
        )

    if dossier.risk_level in (RiskLevel.high, RiskLevel.medium):
        risk_id = "risk-flag"
        nodes.append(
            GraphNodeOut(
                id=risk_id,
                type="risk",
                label="Rủi ro AI",
                desc=f"Mức {RISK_LABELS.get(dossier.risk_level, dossier.risk_level)}",
                x=800,
                y=300,
            )
        )
        edges.append(
            GraphEdgeOut(
                source=f"dossier-{dossier.id}",
                target=risk_id,
                label="Gây ra",
            )
        )

    return KnowledgeGraphOut(
        dossier_id=dossier.id,
        dossier_title=dossier.title,
        nodes=nodes,
        edges=edges,
    )


async def dashboard_summary(session: AsyncSession) -> DashboardSummaryOut:
    dossiers = (await session.execute(select(Dossier).order_by(Dossier.id))).scalars().all()
    pending = sum(1 for d in dossiers if d.status in (DossierStatus.pending, DossierStatus.needs_revision))
    high_risk = sum(1 for d in dossiers if d.risk_level == RiskLevel.high)
    approved = sum(1 for d in dossiers if d.status == DossierStatus.approved)

    alerts = (
        await session.execute(select(Alert).where(Alert.status == AlertStatus.open))
    ).scalars().all()
    source_counts: dict[str, int] = {}
    for alert in alerts:
        source_counts[alert.source] = source_counts.get(alert.source, 0) + 1
    total_alerts = sum(source_counts.values()) or 1
    alert_sources = [
        {"source": src, "count": cnt, "pct": round(cnt / total_alerts * 100)}
        for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1])
    ]
    if not alert_sources:
        alert_sources = [
            {"source": "ERP Budget", "count": 0, "pct": 45},
            {"source": "Legal RAG", "count": 0, "pct": 30},
            {"source": "PMIS", "count": 0, "pct": 15},
            {"source": "Khác", "count": 0, "pct": 10},
        ]

    risk_order = {RiskLevel.high: 0, RiskLevel.medium: 1, RiskLevel.low: 2}
    sorted_dossiers = sorted(dossiers, key=lambda d: risk_order.get(d.risk_level, 3))
    notable = [
        {
            "id": d.doc_no,
            "dossier_id": d.id,
            "title": d.title,
            "dept": d.unit,
            "date": d.created_at.strftime("%d/%m/%Y") if d.created_at else "",
            "risk": RISK_LABELS.get(d.risk_level, d.risk_level),
            "status": STATUS_LABELS.get(d.status, d.status),
        }
        for d in sorted_dossiers[:10]
    ]

    return DashboardSummaryOut(
        pending_count=pending,
        high_risk_count=high_risk,
        approved_count=approved,
        open_alerts=len(alerts),
        alert_sources=alert_sources,
        notable_dossiers=notable,
    )


def list_schedule_jobs() -> list[ScheduleJobOut]:
    return [ScheduleJobOut(**item) for item in SCHEDULE_TEMPLATES]


def list_skill_templates() -> list[SkillTemplateOut]:
    return [
        SkillTemplateOut(
            id=1,
            name="Thẩm định Kế hoạch Đấu thầu (B02)",
            description="Đối chiếu TMĐT với ERP và checklist đấu thầu.",
            type="api_crosscheck",
            is_active=True,
            markdown_content=(
                "# Kỹ năng: Thẩm định Kế hoạch Đấu thầu\n\n"
                "## API Hooks\n- ErpBudgetCheck\n- LegalGraphRAG\n- DOfficeLookup\n\n"
                "## Risk Rules\n- HIGH: TMĐT > ERP approved_budget\n"
                "- MEDIUM: thiếu phụ lục khối lượng"
            ),
        ),
        SkillTemplateOut(
            id=2,
            name="Thẩm định Quyết toán Dự án",
            description="Kiểm tra quyết toán với PMIS và ERP.",
            type="prompt",
            is_active=True,
            markdown_content=(
                "# Kỹ năng: Quyết toán Dự án\n\n"
                "## API Hooks\n- PmisProjectCheck\n- ErpBudgetCheck"
            ),
        ),
    ]


def default_checklist() -> list[ChecklistItemOut]:
    return DEFAULT_CHECKLIST


# ---------------------------------------------------------------------------
# Admin meta — static seeds (no users table in current sprint)
# ---------------------------------------------------------------------------

_USERS: list[dict] = [
    {"id": "U001", "name": "Nguyễn Văn A", "email": "nva@evnhanoi.vn", "dept": "Ban Kế hoạch", "role": "Trưởng ban", "status": "Hoạt động"},
    {"id": "U002", "name": "Trần Thị B", "email": "ttb@evnhanoi.vn", "dept": "Hội đồng Thành viên", "role": "Lãnh đạo HĐTV", "status": "Hoạt động"},
    {"id": "U003", "name": "Lê Văn C", "email": "lvc@evnhanoi.vn", "dept": "Ban CNTT", "role": "Quản trị viên", "status": "Hoạt động"},
    {"id": "U004", "name": "Phạm Thị D", "email": "ptd@evnhanoi.vn", "dept": "Ban Tài chính", "role": "Chuyên viên", "status": "Tạm khóa"},
    {"id": "U005", "name": "Hoàng Văn E", "email": "hve@evnhanoi.vn", "dept": "Ban Quản lý Đầu tư", "role": "Chuyên viên", "status": "Hoạt động"},
]

_ROLES: list[dict] = [
    {"id": "R001", "name": "Quản trị viên", "desc": "Toàn quyền cấu hình hệ thống, AI, người dùng.", "users_count": 3},
    {"id": "R002", "name": "Lãnh đạo HĐTV", "desc": "Quyền chốt duyệt Tờ trình, xem toàn bộ báo cáo AI, ra Nghị quyết.", "users_count": 7},
    {"id": "R003", "name": "Trưởng ban chuyên môn", "desc": "Trình duyệt Tờ trình, trả lời giải trình, xem cảnh báo thuộc Ban quản lý.", "users_count": 15},
    {"id": "R004", "name": "Chuyên viên", "desc": "Tạo nháp Tờ trình, upload hồ sơ, xem đồ thị tri thức cơ bản.", "users_count": 85},
]

_SYSTEM_LOGS: list[dict] = [
    {"id": 1, "time": "25/05/2026 10:45:12", "user": "Hệ thống AI", "action": "Tự động quét", "details": "Quét 5 Tờ trình mới, sinh 2 cảnh báo rủi ro cao.", "type": "info"},
    {"id": 2, "time": "25/05/2026 10:20:00", "user": "Lãnh đạo HĐTV", "action": "Dự thảo Nghị quyết", "details": "Dự thảo tự động Nghị quyết cho Tờ trình 124/TTr-B02", "type": "success"},
    {"id": 3, "time": "25/05/2026 09:15:30", "user": "nva@evnhanoi.vn", "action": "Cập nhật Cấu hình", "details": "Thêm tiêu chí: \"Kiểm tra thời hạn bảo lãnh dự thầu\" vào Checklist", "type": "warning"},
    {"id": 4, "time": "25/05/2026 08:00:00", "user": "Hệ thống", "action": "Đồng bộ ERP", "details": "Lỗi kết nối phân hệ HRMS SSO. Mã lỗi 503.", "type": "danger"},
    {"id": 5, "time": "24/05/2026 15:30:00", "user": "lvc@evnhanoi.vn", "action": "Khóa tài khoản", "details": "Đã tạm khóa tài khoản ptd@evnhanoi.vn", "type": "warning"},
]

def list_users() -> list[UserOut]:
    return [UserOut(**u) for u in _USERS]


def list_roles() -> list[RoleOut]:
    return [RoleOut(**r) for r in _ROLES]


def list_system_logs() -> list[SystemLogOut]:
    return [SystemLogOut(**log) for log in _SYSTEM_LOGS]
