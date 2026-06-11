"""Seed dossiers, users, and Chroma legal docs."""
import asyncio
import os
import sys

import httpx
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_factory
from app.models.entities import (
    Dossier,
    DossierStatus,
    RiskLevel,
    RiskRule,
    ToolConfig,
    User,
    UserPreference,
    UserRole,
)

DOSSIERS = [
    {
        "doc_no": "124/TTr-B02",
        "title": "Tờ trình phê duyệt Kế hoạch đấu thầu Dự án Cáp ngầm Ba Đình",
        "unit": "Ban Kế hoạch (B02)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.pending,
    },
    {
        "doc_no": "89/TTr-B08",
        "title": "Phê duyệt Quyết toán Dự án Trạm biến áp 110kV",
        "unit": "Ban QLĐT (B08)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.needs_revision,
    },
    {
        "doc_no": "45/TTr-B12",
        "title": "Kế hoạch mua sắm vật tư thiết bị An toàn PCTT 2026",
        "unit": "Ban An toàn (B12)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.pending,
    },
    {
        "doc_no": "210/TTr-B09",
        "title": "Giao chỉ tiêu Sản xuất kinh doanh Quý 3/2026",
        "unit": "Ban Kinh doanh (B09)",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.approved,
    },
]

LEGAL_DOCS = [
    ("Nghị định 15/2021/NĐ-CP", "Quy định về đấu thầu lựa chọn nhà thầu", "valid"),
    ("Quyết định 143/QĐ-HĐTV", "Phê duyệt chủ trương đầu tư dự án cáp ngầm Ba Đình", "valid"),
    ("Thông tư 10/2025/TT-BXD", "Hướng dẫn đấu thầu xây dựng", "valid"),
]

TOOL_CONFIGS = [
    {
        "name": "LegalGraphRAG",
        "description": "Kiểm tra căn cứ pháp lý và văn bản liên quan",
        "category": "legal",
        "priority": 10,
        "is_active": True,
        "fallback_response": {"results": ["Nghị định 15/2021/NĐ-CP", "Quyết định 143/QĐ-HĐTV"]},
    },
    {
        "name": "ErpBudgetCheck",
        "description": "Đối chiếu Tổng mức đầu tư với hệ thống ERP",
        "category": "financial",
        "priority": 9,
        "is_active": True,
        "fallback_response": {"approved_budget_vnd": 50000000000, "proposed_budget_vnd": 52000000000, "variance_vnd": 2000000000, "exceeded": True},
    },
    {
        "name": "ErpInventoryCheck",
        "description": "Kiểm tra tình hình vật tư tồn kho",
        "category": "financial",
        "priority": 8,
        "is_active": True,
        "fallback_response": {"material_code": "CVP-240", "stock_meters": 5000, "waste_warning": True},
    },
    {
        "name": "DOfficeLookup",
        "description": "Tra cứu thông tin hồ sơ trên hệ thống DOffice",
        "category": "admin",
        "priority": 7,
        "is_active": True,
        "fallback_response": {"doc_status": "registered", "signed": True, "attachments": 3},
    },
    {
        "name": "PmisProjectCheck",
        "description": "Kiểm tra tiến độ dự án trên PMIS",
        "category": "project",
        "priority": 6,
        "is_active": True,
        "fallback_response": {"project_code": "DA-2026-BD", "phase": "implementation", "on_schedule": True},
    },
    {
        "name": "EcoOcrExtract",
        "description": "Trích xuất nội dung từ file PDF",
        "category": "document",
        "priority": 5,
        "is_active": True,
        "fallback_response": {"pages": 12, "extracted_text": "Tờ trình phê duyệt Kế hoạch đấu thầu Dự án Cáp ngầm Ba Đình"},
        "output_mapping": {"extracted_text": "query"},
        "chains_to": ["LegalGraphRAG"],
    },
]

# T-21: Tool chain configs (idempotent upsert for existing DBs)
TOOL_CHAIN_CONFIGS: dict[str, dict] = {
    "EcoOcrExtract": {
        "output_mapping": {"extracted_text": "query"},
        "chains_to": ["LegalGraphRAG"],
    },
}

RISK_RULES = [
    {
        "name": "Budget Exceeded",
        "description": "Vượt quá ngân sách đã phê duyệt",
        "condition_expression": "any(c.get('tool') == 'ErpBudgetCheck' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 10,
        "is_active": True,
    },
    {
        "name": "Inventory Waste",
        "description": "Phát hiện vật tư tồn kho lãng phí",
        "condition_expression": "any(c.get('tool') == 'ErpInventoryCheck' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 9,
        "is_active": True,
    },
    {
        "name": "Missing Legal Docs",
        "description": "Thiếu căn cứ pháp lý",
        "condition_expression": "any(c.get('tool') == 'LegalGraphRAG' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 8,
        "is_active": True,
    },
    {
        "name": "Unsigned Docs",
        "description": "Hồ sơ chưa đủ chữ ký",
        "condition_expression": "any(c.get('tool') == 'DOfficeLookup' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 7,
        "is_active": True,
    },
    {
        "name": "All Checks Pass",
        "description": "Tất cả các kiểm tra đều hợp lệ",
        "condition_expression": "all(c.get('status') == 'pass' for c in checks)",
        "risk_level": RiskLevel.low,
        "priority": 1,
        "is_active": True,
    },
]


async def seed_db() -> None:
    async with async_session_factory() as session:
        # Check if already seeded
        existing = await session.execute(select(Dossier).limit(1))
        if existing.scalar_one_or_none():
            print("Dossiers already seeded, skipping DB")
            return

        # Seed users (T-23: four role profiles — ids 1–4)
        session.add_all([
            User(
                name="Lãnh đạo HĐTV",
                email="hdtv@evnhanoi.vn",
                role=UserRole.hdtv_leader,
                is_active=True,
            ),
            User(
                name="Trưởng ban Kế hoạch",
                email="depthead@evnhanoi.vn",
                role=UserRole.dept_head,
                is_active=True,
            ),
            User(
                name="Quản trị viên",
                email="admin@evnhanoi.vn",
                role=UserRole.admin,
                is_active=True,
            ),
            User(
                name="Chuyên viên thẩm định",
                email="specialist@evnhanoi.vn",
                role=UserRole.specialist,
                is_active=True,
            ),
        ])

        # Seed dossiers
        for item in DOSSIERS:
            session.add(Dossier(**item))
        
        # Seed tool configs
        for item in TOOL_CONFIGS:
            session.add(ToolConfig(**item))
        
        # Seed risk rules
        for item in RISK_RULES:
            session.add(RiskRule(**item))
            
        await session.commit()
        print(f"Seeded {len(DOSSIERS)} dossiers, {len(TOOL_CONFIGS)} tools, {len(RISK_RULES)} risk rules")


async def seed_chroma() -> None:
    host = os.getenv("CHROMA_HOST", "chroma")
    port = os.getenv("CHROMA_PORT", "8000")
    base = f"http://{host}:{port}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base}/api/v1/collections",
                json={"name": "legal_docs", "get_or_create": True},
            )
            resp.raise_for_status()
            coll_id = resp.json().get("id", "legal_docs")
            docs = [d[1] for d in LEGAL_DOCS]
            metadatas = [{"title": d[0], "status": d[2]} for d in LEGAL_DOCS]
            ids = [f"legal-{i}" for i in range(len(LEGAL_DOCS))]
            await client.post(
                f"{base}/api/v1/collections/{coll_id}/add",
                json={"ids": ids, "documents": docs, "metadatas": metadatas},
            )
            print(f"Seeded {len(LEGAL_DOCS)} legal docs into Chroma")
    except Exception as exc:
        print(f"Chroma seed skipped: {exc}")


async def seed_meilisearch() -> None:
    """T-11: Bulk-index seeded dossiers into Meilisearch after DB seed."""
    from app.services import search_service  # local import to avoid circular at module level

    print("Indexing dossiers into Meilisearch...")
    await search_service.ensure_index()

    async with async_session_factory() as session:
        rows = (await session.execute(select(Dossier).order_by(Dossier.id))).scalars().all()
        docs = [search_service.dossier_to_doc(d) for d in rows]
    await search_service.index_all_dossiers(docs)
    print(f"Meilisearch: indexed {len(docs)} dossiers")


async def seed_agent_memories() -> None:
    """T-15: Seed a handful of demo agent memories into Chroma for demo retrieval."""
    from app.services.memory import vector_store as mem_store  # local import

    print("Seeding demo agent memories into Chroma...")
    demo_memories = [
        {
            "dossier_id": 1,
            "step": 1,
            "thought": "Kiểm tra căn cứ pháp lý Tờ trình cáp ngầm Ba Đình",
            "observation": "Nghị định 15/2021/NĐ-CP còn hiệu lực. Quyết định 143/QĐ-HĐTV đã phê duyệt.",
            "tool_name": "LegalGraphRAG",
        },
        {
            "dossier_id": 1,
            "step": 2,
            "thought": "Kiểm tra ngân sách ERP — dự án cáp ngầm Ba Đình",
            "observation": "Tổng mức đề xuất 52 tỷ VNĐ, vượt hạn mức 50 tỷ VNĐ (exceeded=True).",
            "tool_name": "ErpBudgetCheck",
        },
        {
            "dossier_id": 2,
            "step": 1,
            "thought": "Đối chiếu quyết toán Trạm biến áp 110kV với hệ thống ERP INV",
            "observation": "Phát hiện tồn kho CVP-240 5000m — cảnh báo lãng phí.",
            "tool_name": "ErpInventoryCheck",
        },
    ]
    for mem in demo_memories:
        emb_id = await mem_store.upsert_memory(
            dossier_id=mem["dossier_id"],
            step=mem["step"],
            thought=mem["thought"],
            observation=mem["observation"],
            tool_name=mem["tool_name"],
        )
        status = f"embedding_id={emb_id}" if emb_id else "Chroma unreachable (skipped)"
        print(f"  dossier={mem['dossier_id']} step={mem['step']} → {status}")


async def seed_tool_chains() -> None:
    """T-21: Upsert EcoOcrExtract → LegalGraphRAG chain on tool_configs."""
    print("Seeding tool chain configs...")
    async with async_session_factory() as session:
        for tool_name, chain_cfg in TOOL_CHAIN_CONFIGS.items():
            result = await session.execute(select(ToolConfig).where(ToolConfig.name == tool_name))
            tool = result.scalar_one_or_none()
            if not tool:
                print(f"  {tool_name}: not found, skipping")
                continue
            tool.output_mapping = chain_cfg["output_mapping"]
            tool.chains_to = chain_cfg["chains_to"]
            print(f"  {tool_name} → {chain_cfg['chains_to']} mapping={chain_cfg['output_mapping']}")
        await session.commit()


async def seed_user_preferences() -> None:
    """T-16: Seed per-role user preferences for demo personalization."""
    from app.services.memory import preference_service  # local import

    DEMO_PREFS = [
        # user_id=1 → hdtv_leader: concise report, financial risk focus
        (1, {"report_style": "concise", "risk_focus": "financial", "language": "vi"}),
        # user_id=2 → dept_head: checklist-oriented supplements
        (2, {"report_style": "detailed", "risk_focus": "legal", "language": "vi"}),
        # user_id=4 → specialist: detailed report, full risk coverage
        (4, {"report_style": "detailed", "risk_focus": "all", "language": "vi"}),
    ]

    print("Seeding user preferences...")
    async with async_session_factory() as session:
        for user_id, prefs in DEMO_PREFS:
            await preference_service.set_preferences_bulk(session, user_id, prefs)
            print(f"  user_id={user_id} prefs={list(prefs.keys())}")


async def main() -> None:
    await seed_db()
    await seed_tool_chains()
    await seed_chroma()
    await seed_meilisearch()
    await seed_agent_memories()
    await seed_user_preferences()


if __name__ == "__main__":
    asyncio.run(main())
