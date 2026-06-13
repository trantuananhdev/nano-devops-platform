# Seed Data thực tế — EVN Context

## Script seed hoàn chỉnh: seeds/seed_all.py

```python
"""
Seed toàn bộ dữ liệu mẫu thực tế EVN.
Chạy: python -m seeds.seed_all
Idempotent: có thể chạy lại không bị duplicate.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.entities import (
    Alert, AlertStatus, AppraisalResult, Dossier, DossierStatus,
    Notification, NotificationType, RiskLevel, RiskRule, User, UserRole,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. USERS — Nhân viên EVN
# ---------------------------------------------------------------------------
USERS = [
    # Admin hệ thống
    {"name": "Nguyễn Văn Hải", "email": "hai.nv@evn.com.vn", "role": UserRole.admin},

    # Lãnh đạo HDTV
    {"name": "Trần Thị Minh Châu", "email": "chau.ttm@evn.com.vn", "role": UserRole.hdtv_leader},
    {"name": "Lê Quang Tuấn", "email": "tuan.lq@evn.com.vn", "role": UserRole.hdtv_leader},

    # Trưởng phòng các ban
    {"name": "Phạm Đức Long", "email": "long.pd@evn.com.vn", "role": UserRole.dept_head},  # Ban QLDA
    {"name": "Hoàng Thị Thu", "email": "thu.ht@evn.com.vn", "role": UserRole.dept_head},   # Ban TCKT
    {"name": "Vũ Minh Khoa", "email": "khoa.vm@evn.com.vn", "role": UserRole.dept_head},   # Ban VT

    # Chuyên viên thẩm định
    {"name": "Đỗ Thành Nam", "email": "nam.dt@evn.com.vn", "role": UserRole.specialist},
    {"name": "Nguyễn Thị Lan", "email": "lan.nt@evn.com.vn", "role": UserRole.specialist},
    {"name": "Bùi Văn Hùng", "email": "hung.bv@evn.com.vn", "role": UserRole.specialist},
    {"name": "Lý Thị Hoa", "email": "hoa.lt@evn.com.vn", "role": UserRole.specialist},
]


# ---------------------------------------------------------------------------
# 2. DOSSIERS — Hồ sơ mua sắm/đấu thầu EVN
# ---------------------------------------------------------------------------
DOSSIERS = [
    {
        "doc_no": "EVNCPC-MS-2026-001",
        "title": "Mua sắm cáp điện lực 24kV cho dự án lưới điện tỉnh Bình Dương",
        "unit": "Tổng công ty Điện lực miền Nam (EVNSPC)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.appraising,
    },
    {
        "doc_no": "EVNNPC-XL-2026-015",
        "title": "Thi công lắp đặt trạm biến áp 110kV Thái Nguyên 2",
        "unit": "Tổng công ty Điện lực miền Bắc (EVNNPC)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.submitted_to_dept,
    },
    {
        "doc_no": "EVNHANO-IT-2026-007",
        "title": "Mua sắm thiết bị CNTT phục vụ hệ thống SCADA vận hành lưới điện",
        "unit": "Tổng công ty Điện lực TP Hà Nội (EVNHANOI)",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.approved,
    },
    {
        "doc_no": "EVNCPC-VT-2026-023",
        "title": "Cung cấp máy biến áp phân phối 3 pha 22/0.4kV - 250kVA (50 bộ)",
        "unit": "Tổng công ty Điện lực miền Trung (EVNCPC)",
        "risk_level": RiskLevel.medium,
        "status": DossierStatus.dept_approved,
    },
    {
        "doc_no": "EVNHCMC-MS-2026-031",
        "title": "Mua sắm dây dẫn điện ABC bọc cách điện cho lưới trung thế TP.HCM",
        "unit": "Tổng công ty Điện lực TP.HCM (EVNHCMC)",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.draft,
    },
    {
        "doc_no": "EVNNLDC-IT-2026-004",
        "title": "Nâng cấp hệ thống EMS/SCADA Trung tâm Điều độ Hệ thống điện Quốc gia",
        "unit": "Trung tâm Điều độ HTĐ Quốc gia (NLDC)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.board_reviewed,
    },
    {
        "doc_no": "EVNSPC-XL-2026-044",
        "title": "Tư vấn giám sát xây dựng đường dây 220kV Vĩnh Long - Trà Vinh",
        "unit": "Tổng công ty Điện lực miền Nam (EVNSPC)",
        "risk_level": RiskLevel.high,
        "status": DossierStatus.needs_revision,
    },
    {
        "doc_no": "EVNCPC-TB-2026-012",
        "title": "Bảo trì định kỳ hệ thống chống sét và nối đất trạm 500kV Đà Nẵng",
        "unit": "Tổng công ty Điện lực miền Trung (EVNCPC)",
        "risk_level": RiskLevel.low,
        "status": DossierStatus.pending,
    },
]


# ---------------------------------------------------------------------------
# 3. RISK RULES — Theo Nghị định 24/2024/NĐ-CP và quy chế EVN
# ---------------------------------------------------------------------------
RISK_RULES = [
    {
        "name": "Vượt ngưỡng ngân sách phê duyệt",
        "description": "Tổng giá trị gói thầu vượt quá 110% dự toán được duyệt",
        "condition_expression": "any(c['tool'] == 'ErpBudgetCheck' and c['status'] == 'fail' for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 10,
    },
    {
        "name": "Thiếu hồ sơ năng lực nhà thầu",
        "description": "Hồ sơ không có đủ giấy phép kinh doanh, chứng chỉ hành nghề theo ND24",
        "condition_expression": "any(c['tool'] == 'LegalGraphRAG' and c.get('missing_docs', False) for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 9,
    },
    {
        "name": "Giá đơn vị cao bất thường",
        "description": "Đơn giá vật tư cao hơn 130% so với khung giá EVN hiện hành",
        "condition_expression": "any(c['tool'] == 'ErpInventoryCheck' and c.get('price_anomaly', False) for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 7,
    },
    {
        "name": "Thời gian cung cấp không khả thi",
        "description": "Tiến độ giao hàng/thi công không phù hợp với yêu cầu vận hành lưới",
        "condition_expression": "any(c['tool'] == 'ScheduleValidator' and c['status'] == 'fail' for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 6,
    },
    {
        "name": "Thiếu chứng nhận tiêu chuẩn kỹ thuật",
        "description": "Thiết bị điện không có chứng nhận TCVN/IEC bắt buộc",
        "condition_expression": "len(failed) >= 1 and any('technical_cert' in c.get('missing_docs', []) for c in failed)",
        "risk_level": RiskLevel.high,
        "priority": 8,
    },
    {
        "name": "Rủi ro thấp — đủ điều kiện",
        "description": "Tất cả checks đều pass, hồ sơ đủ điều kiện thẩm định bình thường",
        "condition_expression": "len(failed) == 0 and len(passed) >= 3",
        "risk_level": RiskLevel.low,
        "priority": 1,
    },
]


# ---------------------------------------------------------------------------
# 4. ALERTS — Cảnh báo hệ thống
# ---------------------------------------------------------------------------
ALERTS_DATA = [
    {
        "title": "Ngân sách gói thầu cáp điện Bình Dương vượt 15%",
        "severity": "high",
        "source": "ErpBudgetCheck",
        "description": "Hồ sơ EVNCPC-MS-2026-001: Tổng giá trị 8.750.000.000 VND vượt dự toán phê duyệt 7.580.000.000 VND (115.4%). Cần xem xét lại đơn giá cáp XLPE 24kV.",
        "status": AlertStatus.open,
        "dossier_doc_no": "EVNCPC-MS-2026-001",
    },
    {
        "title": "Thiếu chứng chỉ ISO 9001 nhà thầu thi công trạm Thái Nguyên",
        "severity": "high",
        "source": "LegalGraphRAG",
        "description": "Hồ sơ EVNNPC-XL-2026-015: Nhà thầu chưa cung cấp chứng chỉ ISO 9001:2015 cho hạng mục xây lắp điện. Yêu cầu bổ sung theo Điều 12 Nghị định 24/2024.",
        "status": AlertStatus.open,
        "dossier_doc_no": "EVNNPC-XL-2026-015",
    },
    {
        "title": "Giá máy biến áp EVNCPC-VT-2026-023 cao hơn khung giá 28%",
        "severity": "medium",
        "source": "ErpInventoryCheck",
        "description": "Đơn giá MBA 250kVA đề xuất: 185.000.000 VND/bộ, khung giá EVN 2026: 144.500.000 VND/bộ. Chênh lệch 40.500.000 VND/bộ × 50 bộ = 2.025.000.000 VND.",
        "status": AlertStatus.open,
        "dossier_doc_no": "EVNCPC-VT-2026-023",
    },
    {
        "title": "Hệ thống SCADA đã kết nối Meilisearch index",
        "severity": "low",
        "source": "system",
        "description": "Search index khởi tạo thành công với 8 hồ sơ. Thời gian index: 0.34s.",
        "status": AlertStatus.resolved,
        "dossier_doc_no": None,
    },
]


# ---------------------------------------------------------------------------
# SEED RUNNER
# ---------------------------------------------------------------------------

async def seed_users(session) -> dict[str, int]:
    """Seed users, return email→id map."""
    id_map = {}
    for u in USERS:
        existing = (await session.execute(
            select(User).where(User.email == u["email"])
        )).scalar_one_or_none()
        if existing:
            id_map[u["email"]] = existing.id
            continue
        user = User(**u)
        session.add(user)
        await session.flush()  # để lấy id ngay
        id_map[u["email"]] = user.id
        logger.info("Seeded user: %s (%s)", u["name"], u["role"])
    await session.commit()
    return id_map


async def seed_dossiers(session) -> dict[str, int]:
    """Seed dossiers, return doc_no→id map."""
    id_map = {}
    for d in DOSSIERS:
        existing = (await session.execute(
            select(Dossier).where(Dossier.doc_no == d["doc_no"])
        )).scalar_one_or_none()
        if existing:
            id_map[d["doc_no"]] = existing.id
            continue
        dossier = Dossier(**d)
        session.add(dossier)
        await session.flush()
        id_map[d["doc_no"]] = dossier.id
        logger.info("Seeded dossier: %s", d["doc_no"])
    await session.commit()
    return id_map


async def seed_risk_rules(session) -> None:
    """Seed risk rules."""
    existing_count = (await session.execute(
        select(RiskRule)
    )).scalars().all()
    if existing_count:
        logger.info("Risk rules already seeded (%d rules), skipping", len(existing_count))
        return
    for r in RISK_RULES:
        session.add(RiskRule(**r))
    await session.commit()
    logger.info("Seeded %d risk rules", len(RISK_RULES))


async def seed_alerts(session, dossier_id_map: dict[str, int]) -> None:
    """Seed alerts với dossier FK."""
    for a in ALERTS_DATA:
        doc_no = a.pop("dossier_doc_no", None)
        dossier_id = dossier_id_map.get(doc_no) if doc_no else None

        # Idempotency: skip nếu alert cùng source + description đã tồn tại
        existing = (await session.execute(
            select(Alert).where(Alert.description == a["description"])
        )).scalar_one_or_none()
        if existing:
            a["dossier_doc_no"] = doc_no  # restore cho lần chạy sau
            continue

        alert = Alert(dossier_id=dossier_id, **a)
        session.add(alert)
        logger.info("Seeded alert: %s", a.get("title", a["source"]))
    await session.commit()


async def seed_appraisal_sample(session, dossier_id_map: dict[str, int]) -> None:
    """Seed 1 appraisal result mẫu cho hồ sơ đã approved."""
    approved_doc_no = "EVNHANO-IT-2026-007"
    dossier_id = dossier_id_map.get(approved_doc_no)
    if not dossier_id:
        return

    existing = (await session.execute(
        select(AppraisalResult).where(AppraisalResult.dossier_id == dossier_id)
    )).scalar_one_or_none()
    if existing:
        return

    result = AppraisalResult(
        dossier_id=dossier_id,
        overall_risk=RiskLevel.low,
        report_md="""## Kết quả thẩm định

**Hồ sơ:** EVNHANO-IT-2026-007 — Mua sắm thiết bị CNTT SCADA  
**Kết luận:** ✅ Đủ điều kiện phê duyệt

### Kiểm tra pháp lý
- Hợp đồng nguyên tắc với nhà cung cấp Siemens Việt Nam: **ĐẠT**
- Giấy phép nhập khẩu thiết bị điện tử: **ĐẠT**
- Chứng nhận CE/IEC 61850: **ĐẠT**

### Kiểm tra tài chính
- Dự toán: 4.250.000.000 VND — trong ngưỡng phê duyệt: **ĐẠT**
- Giá thiết bị SCADA RTU: phù hợp khung giá tham chiếu 2026: **ĐẠT**
""",
        resolution_md="Đề nghị phê duyệt. Yêu cầu cam kết bảo hành 3 năm từ nhà cung cấp.",
        checks=[
            {"tool": "LegalGraphRAG", "status": "pass", "score": 0.94},
            {"tool": "ErpBudgetCheck", "status": "pass", "score": 0.91},
            {"tool": "ErpInventoryCheck", "status": "pass", "score": 0.88},
        ],
        critic_verdict={"approved": True, "confidence": 0.92, "comments": "Hồ sơ đầy đủ, không có điểm cần làm rõ."},
    )
    session.add(result)
    await session.commit()
    logger.info("Seeded sample appraisal for %s", approved_doc_no)


async def seed_all():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    async with async_session_factory() as session:
        logger.info("=== Starting EVN seed ===")
        user_map = await seed_users(session)
        dossier_map = await seed_dossiers(session)
        await seed_risk_rules(session)
        await seed_alerts(session, dossier_map)
        await seed_appraisal_sample(session, dossier_map)
        logger.info("=== Seed hoàn tất: %d users, %d dossiers ===", len(user_map), len(dossier_map))


if __name__ == "__main__":
    asyncio.run(seed_all())
```

## Cách chạy

```bash
# Từ thư mục hdtv-ai-platform/
python -m seeds.seed_all

# Hoặc trong docker
docker exec -it hdtv-platform python -m seeds.seed_all
```

## Mở rộng seed

Khi thêm module mới, tạo `seeds/seed_<tên>.py` riêng và thêm call vào `seed_all()`.
Pattern idempotency: luôn check `scalar_one_or_none()` trước khi insert theo unique field.