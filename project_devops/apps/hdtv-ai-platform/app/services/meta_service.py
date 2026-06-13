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
    {
        "id": 4,
        "name": "Quét định kỳ ý kiến góp ý nhà cung cấp",
        "cron": "0 9 * * 1",
        "schedule_text": "Hàng tuần (Thứ Hai, 09:00)",
        "tools": ["supplier_feedback_lookup", "legal_doc_lookup"],
        "status": "active",
        "description": "Quét và phân tích định kỳ các ý kiến góp ý của nhà cung cấp đối với các gói thầu thiết bị công nghệ.",
    },
]

STATUS_LABELS = {
    DossierStatus.draft: "Nháp",
    DossierStatus.pending: "Chờ duyệt",
    DossierStatus.appraising: "Đang thẩm định",
    DossierStatus.submitted_to_dept: "Đã trình lên Ban",
    DossierStatus.dept_approved: "Ban đã duyệt",
    DossierStatus.dept_rejected: "Ban từ chối",
    DossierStatus.submitted_to_board: "Đã trình lên HĐTV",
    DossierStatus.board_reviewed: "HĐTV đã xem xét",
    DossierStatus.approved: "Đã phê duyệt",
    DossierStatus.rejected: "Đã từ chối",
    DossierStatus.needs_revision: "Cần chỉnh sửa",
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

    if dossier_id == 5:
        nodes = [
            GraphNodeOut(id="tt198", type="dossier", label="198/TTr-EVNHANOI", desc="Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) phục vụ kiểm tra đường dây 220/110kV", x=400, y=300),
            GraphNodeOut(id="qd8594", type="legal", label="QĐ 8594/QĐ-EVNHANOI", desc="Quy định tiêu chuẩn kỹ thuật UAV tối thiểu của Tổng công ty", x=150, y=150),
            GraphNodeOut(id="nq180", type="law", label="NQ 180-NQ/ĐU", desc="Nghị quyết đẩy mạnh chuyển đổi số trong quản lý kỹ thuật", x=280, y=120),
            GraphNodeOut(id="qd153", type="law", label="QĐ 153/QĐ-EVN", desc="Quy chế quản lý thiết bị bay không người lái trong Tập đoàn", x=410, y=100),
            GraphNodeOut(id="pl_so_sanh", type="data", label="Phụ lục So sánh", desc="Bảng so sánh chi tiết kỹ thuật các dòng UAV của các nhà thầu", x=600, y=200),
            GraphNodeOut(id="apex_feedback", type="data", label="Góp ý Apex Tech", desc="Ý kiến phản hồi từ nhà cung cấp Apex Tech về cấu hình thiết bị", x=720, y=320),
            GraphNodeOut(id="risk_spec", type="risk", label="Rủi ro cấu hình", desc="AI phát hiện Apex Tech đề xuất giảm chỉ tiêu RAM từ 64GB xuống 16GB", x=820, y=200),
        ]
        edges = [
            GraphEdgeOut(source="tt198", target="qd8594", label="Căn cứ theo"),
            GraphEdgeOut(source="tt198", target="nq180", label="Căn cứ theo"),
            GraphEdgeOut(source="tt198", target="qd153", label="Đúng thẩm quyền theo"),
            GraphEdgeOut(source="tt198", target="pl_so_sanh", label="Chứa Phụ lục"),
            GraphEdgeOut(source="pl_so_sanh", target="apex_feedback", label="Đối chiếu"),
            GraphEdgeOut(source="apex_feedback", target="risk_spec", label="Gây ra"),
        ]
        return KnowledgeGraphOut(
            dossier_id=dossier.id,
            dossier_title=dossier.title,
            nodes=nodes,
            edges=edges,
        )

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
    pending = sum(1 for d in dossiers if d.status in (DossierStatus.draft, DossierStatus.pending, DossierStatus.appraising, DossierStatus.submitted_to_dept, DossierStatus.dept_approved, DossierStatus.submitted_to_board, DossierStatus.board_reviewed, DossierStatus.needs_revision))
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
        alert_sources = []

    # Calculate dossiers by unit breakdown
    unit_counts: dict[str, int] = {}
    for d in dossiers:
        u = d.unit or "Khác"
        unit_counts[u] = unit_counts.get(u, 0) + 1
    total_dossiers = len(dossiers) or 1
    dossiers_by_unit = [
        {"unit": unit, "count": cnt, "pct": round(cnt / total_dossiers * 100)}
        for unit, cnt in sorted(unit_counts.items(), key=lambda x: -x[1])
    ]

    risk_order = {RiskLevel.high: 0, RiskLevel.medium: 1, RiskLevel.low: 2}
    sorted_dossiers = sorted(dossiers, key=lambda d: risk_order.get(d.risk_level, 3))
    notable = [
        {
            "id": d.id,
            "dossier_id": d.id,
            "doc_no": d.doc_no,
            "title": d.title,
            "dept": d.unit,
            "date": d.created_at.strftime("%d/%m/%Y") if d.created_at else "",
            "risk": RISK_LABELS.get(d.risk_level, d.risk_level),
            "status": STATUS_LABELS.get(d.status, d.status),
        }
        for d in sorted_dossiers[:10]
    ]

    # Newest dossiers - sorted by created_at descending, top 5
    newest_sorted = sorted(dossiers, key=lambda d: d.created_at if d.created_at else datetime.min, reverse=True)
    newest = [
        {
            "id": d.doc_no,
            "dossier_id": d.id,
            "doc_no": d.doc_no,
            "title": d.title,
            "dept": d.unit,
            "unit": d.unit,
            "date": d.created_at.strftime("%d/%m/%Y") if d.created_at else "",
            "risk_level": d.risk_level.value,
            "status": d.status.value,
        }
        for d in newest_sorted[:5]
    ]

    return DashboardSummaryOut(
        pending_count=pending,
        high_risk_count=high_risk,
        approved_count=approved,
        open_alerts=len(alerts),
        alert_sources=alert_sources,
        notable_dossiers=notable,
        newest_dossiers=newest,
        dossiers_by_unit=dossiers_by_unit,
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
        SkillTemplateOut(
            id=3,
            name="Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị (đối chiếu góp ý NCC)",
            description="Đánh giá tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) và đối chiếu ý kiến góp ý của nhà cung cấp.",
            type="api_crosscheck",
            is_active=True,
            markdown_content=(
                "# Kỹ năng: Thẩm định Tiêu chuẩn kỹ thuật Vật tư/Thiết bị\n\n"
                "## API Hooks\n- legal_doc_lookup\n- supplier_feedback_lookup\n\n"
                "## Risk Rules\n- HIGH: Thiết bị không đáp ứng tiêu chuẩn kỹ thuật tối thiểu tại QĐ 8594/QĐ-EVNHANOI hoặc quy chế tập đoàn.\n"
                "- MEDIUM: Nhà cung cấp đề xuất hạ cấu hình kỹ thuật thiết bị so với dự thảo (ví dụ: giảm RAM từ 64GB xuống 16GB, giảm tầm bay...)."
            ),
        ),
    ]


def default_checklist(dossier_type_id: int | None = None) -> list[ChecklistItemOut]:
    if dossier_type_id == 6:
        return [
            ChecklistItemOut(id=101, text="Kiểm tra hiệu lực văn bản pháp lý căn cứ (QĐ 8594)", type="auto", is_required=True),
            ChecklistItemOut(id=102, text="Đánh giá thẩm quyền phê duyệt theo quy chế EVN (QĐ 153)", type="auto", is_required=True),
            ChecklistItemOut(id=103, text="Đối chiếu cấu hình đề xuất với góp ý của nhà cung cấp", type="auto", is_required=True),
            ChecklistItemOut(id=104, text="Kiểm tra cấu trúc và tính đầy đủ của hồ sơ", type="auto", is_required=True),
            ChecklistItemOut(id=105, text="Xác minh năng lực nhà cung cấp trên thị trường", type="auto", is_required=False),
        ]
    return DEFAULT_CHECKLIST


# ---------------------------------------------------------------------------
# Admin meta — DB-based users and roles
# ---------------------------------------------------------------------------

_ROLE_LABELS = {
    UserRole.admin: "Quản trị viên",
    UserRole.hdtv_leader: "Lãnh đạo HĐTV",
    UserRole.dept_head: "Trưởng ban chuyên môn",
    UserRole.specialist: "Chuyên viên",
}

_ROLE_DESCS = {
    UserRole.admin: "Toàn quyền cấu hình hệ thống, AI, người dùng.",
    UserRole.hdtv_leader: "Quyền chốt duyệt Tờ trình, xem toàn bộ báo cáo AI, ra Nghị quyết.",
    UserRole.dept_head: "Trình duyệt Tờ trình, trả lời giải trình, xem cảnh báo thuộc Ban quản lý.",
    UserRole.specialist: "Tạo nháp Tờ trình, upload hồ sơ, xem đồ thị tri thức cơ bản.",
}

_SYSTEM_LOGS: list[dict] = [
    {"id": 1, "time": "25/05/2026 10:45:12", "user": "Hệ thống AI", "action": "Tự động quét", "details": "Quét 5 Tờ trình mới, sinh 2 cảnh báo rủi ro cao.", "type": "info"},
    {"id": 2, "time": "25/05/2026 10:20:00", "user": "Lãnh đạo HĐTV", "action": "Dự thảo Nghị quyết", "details": "Dự thảo tự động Nghị quyết cho Tờ trình 124/TTr-B02", "type": "success"},
    {"id": 3, "time": "25/05/2026 09:15:30", "user": "nva@evnhanoi.vn", "action": "Cập nhật Cấu hình", "details": "Thêm tiêu chí: \"Kiểm tra thời hạn bảo lãnh dự thầu\" vào Checklist", "type": "warning"},
    {"id": 4, "time": "25/05/2026 08:00:00", "user": "Hệ thống", "action": "Đồng bộ ERP", "details": "Lỗi kết nối phân hệ HRMS SSO. Mã lỗi 503.", "type": "danger"},
    {"id": 5, "time": "24/05/2026 15:30:00", "user": "lvc@evnhanoi.vn", "action": "Khóa tài khoản", "details": "Đã tạm khóa tài khoản ptd@evnhanoi.vn", "type": "warning"},
]

async def list_users(session: AsyncSession) -> list[UserOut]:
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [
        UserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
        )
        for user in users
    ]


async def list_roles(session: AsyncSession) -> list[RoleOut]:
    # Get user count per role
    count_result = await session.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    role_counts = {row[0]: row[1] for row in count_result.all()}
    
    # Create RoleOut for each enum value
    roles = []
    for idx, role in enumerate(UserRole, start=1):
        roles.append(
            RoleOut(
                id=f"R{idx:03d}",
                name=_ROLE_LABELS.get(role, role.value),
                desc=_ROLE_DESCS.get(role, ""),
                users_count=role_counts.get(role, 0),
            )
        )
    return roles


def list_system_logs() -> list[SystemLogOut]:
    return [SystemLogOut(**log) for log in _SYSTEM_LOGS]
