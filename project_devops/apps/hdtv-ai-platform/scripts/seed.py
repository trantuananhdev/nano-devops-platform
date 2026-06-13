"""Seed dossiers, users, and Chroma legal docs."""
import asyncio
import os
import sys

import httpx
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_factory
from app.core.config import get_settings
settings = get_settings()
from app.models.entities import (
    Dossier,
    DossierStatus,
    RiskLevel,
    RiskRule,
    ToolConfig,
    User,
    UserPreference,
    UserRole,
    ReferenceDocument,
)
from app.services import minio_service
from app.services.rag.pdf_extractor import extract_text_from_pdf, chunk_text
from app.services.memory import vector_store

DOSSIERS = [
    {
        "doc_no": "124/TTr-B02",
        "title": "Tờ trình phê duyệt Kế hoạch đấu thầu Dự án Cáp ngầm Ba Đình",
        "unit": "Ban Kế hoạch (B02)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.submitted_to_dept,
    },
    {
        "doc_no": "89/TTr-B08",
        "title": "Phê duyệt Quyết toán Dự án Trạm biến áp 110kV",
        "unit": "Ban QLĐT (B08)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.draft,
    },
    {
        "doc_no": "45/TTr-B12",
        "title": "Kế hoạch mua sắm vật tư thiết bị An toàn PCTT 2026",
        "unit": "Ban An toàn (B12)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.dept_approved,
    },
    {
        "doc_no": "210/TTr-B09",
        "title": "Giao chỉ tiêu Sản xuất kinh doanh Quý 3/2026",
        "unit": "Ban Kinh doanh (B09)",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.approved,
    },
    {
        "doc_no": "198/TTr-EVNHANOI",
        "title": "Phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) phục vụ kiểm tra đường dây 220/110kV",
        "unit": "Ban Kỹ thuật (KT)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.board_reviewed,
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
            
            # Check if there are already docs in the collection
            resp = await client.get(f"{base}/api/v1/collections/{coll_id}/count")
            resp.raise_for_status()
            count = resp.json()
            if count > 0:
                print("Legal docs already in Chroma, skipping seed_chroma()")
                return
                
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
    from app.core.config import get_settings
    import httpx
    
    print("Seeding demo agent memories into Chroma...")
    
    # Check if we already have agent memories
    s = get_settings()
    base = f"http://{s.chroma_host}:{s.chroma_port}"
    coll_id = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Replicate _get_or_create_collection logic
            resp = await client.post(
                f"{base}/api/v1/collections",
                json={"name": s.chroma_collection_memories, "get_or_create": True},
            )
            resp.raise_for_status()
            coll_id = resp.json().get("id") or s.chroma_collection_memories
            
            resp = await client.get(f"{base}/api/v1/collections/{coll_id}/count")
            resp.raise_for_status()
            count = resp.json()
            if count > 0:
                print("Agent memories already seeded into Chroma, skipping")
                return
    except Exception as exc:
        print(f"Checking existing agent memories skipped: {exc}")
    
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


async def seed_dossier_198_pdfs() -> None:
    """T-39: Upload dossier 198 real PDFs/files to MinIO and create ReferenceDocuments."""
    import os
    from pathlib import Path
    import mimetypes
    from app.services import minio_service
    from app.services.reference_document_service import create_reference_document
    from app.schemas.dossier import ReferenceDocumentCreate

    # Get dossier 198 from DB
    dossier_id = None
    async with async_session_factory() as session:
        result = await session.execute(select(Dossier).where(Dossier.doc_no == "198/TTr-EVNHANOI"))
        dossier = result.scalar_one_or_none()
        if not dossier:
            print("Dossier 198 not found, skipping PDF upload")
            return
        dossier_id = dossier.id
        
        # Check if we already have reference documents for this dossier
        existing_refs = await session.execute(select(ReferenceDocument).where(ReferenceDocument.dossier_id == dossier_id))
        if existing_refs.scalars().first():
            print(f"Reference documents for dossier {dossier_id} already exist, skipping")
            return

    # Data folder path
    data_root = Path(__file__).parent.parent / "data" / "seed" / "dossier_198_uav"
    if not data_root.exists():
        print(f"Data folder not found: {data_root}")
        return

    try:
        main_pdf_found = False
        # Recursively find all files in data_root
        all_files = list(data_root.rglob("*"))
        for file_path in all_files:
            if file_path.is_dir():
                continue
                
            # Skip hidden files
            if file_path.name.startswith("."):
                continue
                
            # Get relative path to show folder structure
            rel_path = file_path.relative_to(data_root)
            print(f"Processing file: {rel_path}")
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Default to binary stream if we can't guess
                mime_type = "application/octet-stream"
                
            # Upload file to MinIO
            with open(file_path, "rb") as f:
                data_bytes = f.read()
                file_size = len(data_bytes)
                
                # Create a unique key that preserves folder structure
                minio_key = f"dossier-198/{rel_path.as_posix()}"
                result = await minio_service.upload_pdf(data_bytes, file_path.name, minio_key)
                
                if result["ok"]:
                    print(f"Uploaded: {rel_path} (key={result['key']}, size={file_size} bytes)")
                    
                    # Create ReferenceDocument in DB
                    ref_doc_data = ReferenceDocumentCreate(
                        file_name=file_path.name,
                        file_key=result["key"],
                        file_size=file_size,
                        content_type=mime_type,
                    )
                    
                    async with async_session_factory() as session:
                        await create_reference_document(
                            session=session,
                            dossier_id=dossier_id,
                            data=ref_doc_data,
                            uploaded_by=1,  # Admin user
                        )
                        
                    # Set as main dossier PDF if it's one of the main files
                    if not main_pdf_found and ("tờ trình" in file_path.name.lower() or "ttr" in file_path.name.lower()):
                        async with async_session_factory() as session:
                            dossier = (await session.execute(select(Dossier).where(Dossier.id == dossier_id))).scalar_one()
                            dossier.pdf_url = result["key"]
                            await session.commit()
                        main_pdf_found = True
                        print(f"Set as main dossier PDF: {file_path.name}")
                else:
                    print(f"Failed to upload {rel_path}: {result.get('error')}")

    except Exception as exc:
        print(f"MinIO upload skipped: {exc}")
        import traceback
        traceback.print_exc()


async def seed_real_legal_docs() -> None:
    """T-40: Extract and ingest real legal PDFs into Chroma legal_docs collection."""
    import os
    from pathlib import Path

    data_root = Path(__file__).parent.parent / "data" / "seed" / "dossier_198_uav" / "Tài liệu căn cứ tham khảo" / "8594_QĐ-EVNHANOI"
    if not data_root.exists():
        print(f"Reference folder not found: {data_root}")
        return

    legal_pdfs = list(data_root.glob("*.pdf"))
    if not legal_pdfs:
        print("No legal PDFs found to ingest")
        return

    # Check if we already have legal docs in Chroma
    from app.core.config import get_settings
    import httpx
    s = get_settings()
    base = f"http://{s.chroma_host}:{s.chroma_port}"
    already_seeded = False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First get or create the collection
            resp = await client.post(
                f"{base}/api/v1/collections",
                json={"name": s.rag_legal_collection, "get_or_create": True},
            )
            resp.raise_for_status()
            coll_id = resp.json().get("id") or s.rag_legal_collection
            
            # Check if there are any documents in the collection
            resp = await client.get(
                f"{base}/api/v1/collections/{coll_id}/count",
            )
            resp.raise_for_status()
            count = resp.json()
            if count > 0:
                print("Legal docs already seeded into Chroma, skipping")
                return
    except Exception as exc:
        print(f"Checking existing legal docs skipped: {exc}")

    print(f"Ingesting {len(legal_pdfs)} real legal docs into Chroma...")
    
    for pdf_path in legal_pdfs:
        try:
            print(f"  Extracting: {pdf_path.name}")
            text, page_count = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(text)
            
            # Upsert to Chroma legal_docs collection
            doc_id = pdf_path.stem
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}-chunk-{i}"
                await vector_store.upsert_legal_doc(
                    doc_id=chunk_id,
                    text=chunk,
                    metadata={
                        "source": pdf_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "page_count": page_count,
                    },
                )
            print(f"    → {len(chunks)} chunks ingested")
            
        except Exception as exc:
            print(f"    Failed: {exc}")


async def seed_alerts() -> None:
    """Seed demo alerts, especially alert AL-1043 for Dossier 198 (ID=5)."""
    from app.models.entities import Alert, AlertStatus
    print("Seeding alerts...")
    async with async_session_factory() as session:
        # Find dossier 198
        result = await session.execute(select(Dossier).where(Dossier.doc_no == "198/TTr-EVNHANOI"))
        dossier = result.scalar_one_or_none()
        if not dossier:
            print("  Dossier 198 not found, skipping alert seeding")
            return
        dossier_id = dossier.id
        
        # Check if alert AL-1043 (which has id=1043 in DB) already exists
        existing = await session.execute(
            select(Alert).where(Alert.dossier_id == dossier_id, Alert.source == "AI Spec Cross-Check")
        )
        if existing.scalar_one_or_none():
            print("  Alert for dossier 198 already exists, skipping")
            return

        # Seed alert
        alert = Alert(
            id=1043,  # Set ID to 1043 explicitly to match AL-1043!
            dossier_id=dossier_id,
            title="Độ phân giải camera UAV chưa đạt chuẩn tối thiểu",
            severity="medium",
            source="AI Spec Cross-Check",
            description="Độ phân giải camera hồng ngoại đề xuất là 640x512, thấp hơn tiêu chuẩn tối thiểu quy định tại Quyết định 8594/QĐ-EVNHANOI (yêu cầu tối thiểu 800x600).",
            status=AlertStatus.open,
        )
        session.add(alert)
        await session.commit()
        print("  Seeded alert AL-1043 successfully")


async def seed_mcp_logs() -> None:
    """Seed demo MCP call logs for the admin panel."""
    from app.models.entities import McpCallLog
    print("Seeding MCP call logs...")
    async with async_session_factory() as session:
        # Check if logs already exist
        result = await session.execute(select(McpCallLog).limit(1))
        if result.scalar_one_or_none():
            print("  MCP logs already exist, skipping")
            return

        # Insert 2 logs
        log1 = McpCallLog(
            api_key_prefix="gemini-p",
            tool_name="legal_doc_lookup",
            inputs={"doc_no": "8594/QĐ-EVNHANOI"},
            outputs={"doc_no": "8594/QĐ-EVNHANOI", "title": "Quyết định 8594/QĐ-EVNHANOI", "still_effective": True},
            is_error=False,
            is_streaming=False,
            execution_ms=250,
        )
        log2 = McpCallLog(
            api_key_prefix="gemini-p",
            tool_name="supplier_feedback_lookup",
            inputs={"spec_item": "dung lượng bộ nhớ"},
            outputs={"spec_item": "dung lượng bộ nhớ", "suppliers": ["Apex Tech"], "risk_detected": True},
            is_error=False,
            is_streaming=False,
            execution_ms=380,
        )
        session.add_all([log1, log2])
        await session.commit()
        print("  Seeded 2 MCP call logs successfully")


async def seed_notifications() -> None:
    """Seed demo notifications for user_id=1."""
    from app.models.entities import Notification, NotificationType
    print("Seeding notifications...")
    async with async_session_factory() as session:
        # Check if notifications already exist for user 1
        result = await session.execute(
            select(Notification).where(Notification.user_id == 1).limit(1)
        )
        if result.scalar_one_or_none():
            print("  Notifications for user 1 already exist, skipping")
            return

        # Seed 3 notifications:
        # 1 unread appraisal_complete, 1 unread status_change, 1 read version_created
        n1 = Notification(
            user_id=1,
            type=NotificationType.appraisal_complete,
            title="Thẩm định hoàn tất",
            message="Yêu cầu phê duyệt Tiêu chuẩn kỹ thuật thiết bị bay không người lái (UAV) đã được thẩm định tự động bởi AI.",
            dossier_id=5,
            is_read=False,
            extra_data={"risk_level": "medium"},
        )
        n2 = Notification(
            user_id=1,
            type=NotificationType.status_change,
            title="Cập nhật trạng thái tờ trình",
            message="Tờ trình 198/TTr-EVNHANOI thay đổi trạng thái từ nháp sang đã trình duyệt bộ phận.",
            dossier_id=5,
            is_read=False,
            extra_data={"old_status": "draft", "new_status": "submitted_to_dept"},
        )
        n3 = Notification(
            user_id=1,
            type=NotificationType.version_created,
            title="Phiên bản tài liệu mới",
            message="Phiên bản V2 của tài liệu Phụ lục kỹ thuật đã được khởi tạo bởi chuyên viên.",
            dossier_id=5,
            is_read=True,
            extra_data={"version": 2},
        )
        session.add_all([n1, n2, n3])
        await session.commit()
        print("  Seeded 3 notifications for user 1 successfully")


async def main() -> None:
    await seed_db()
    await seed_tool_chains()
    await seed_alerts()
    await seed_mcp_logs()
    await seed_notifications()
    await seed_chroma()
    await seed_meilisearch()
    await seed_agent_memories()
    await seed_user_preferences()
    await seed_dossier_198_pdfs()
    await seed_real_legal_docs()


if __name__ == "__main__":
    asyncio.run(main())
