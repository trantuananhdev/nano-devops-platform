"""Seed risk rules — 6 quy tắc theo Nghị định 24/2024/NĐ-CP và quy chế EVN.

Idempotent: skip nếu đã có bất kỳ rule nào.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import RiskLevel, RiskRule

logger = logging.getLogger(__name__)

RISK_RULES_DATA = [
    {
        "name": "Vượt ngưỡng ngân sách phê duyệt",
        "description": "Tổng giá trị gói thầu vượt quá 110% dự toán được duyệt",
        "condition_expression": "any(c.get('tool') == 'ErpBudgetCheck' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 10,
    },
    {
        "name": "Thiếu hồ sơ năng lực nhà thầu",
        "description": "Hồ sơ không có đủ giấy phép kinh doanh, chứng chỉ hành nghề theo Nghị định 24/2024/NĐ-CP",
        "condition_expression": "any(c.get('tool') == 'LegalGraphRAG' and c.get('missing_docs') for c in checks)",
        "risk_level": RiskLevel.high,
        "priority": 9,
    },
    {
        "name": "Thiếu chứng nhận tiêu chuẩn kỹ thuật",
        "description": "Thiết bị điện không có chứng nhận TCVN/IEC bắt buộc",
        "condition_expression": "any('technical_cert' in c.get('missing_docs', []) for c in checks if isinstance(c.get('missing_docs'), list))",
        "risk_level": RiskLevel.high,
        "priority": 8,
    },
    {
        "name": "Giá đơn vị cao bất thường",
        "description": "Đơn giá vật tư cao hơn 130% so với khung giá EVN hiện hành",
        "condition_expression": "any(c.get('tool') == 'ErpInventoryCheck' and c.get('price_anomaly') for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 7,
    },
    {
        "name": "Tiến độ cung cấp không khả thi",
        "description": "Tiến độ giao hàng/thi công không phù hợp yêu cầu vận hành lưới điện",
        "condition_expression": "any(c.get('tool') == 'ScheduleValidator' and c.get('status') == 'fail' for c in checks)",
        "risk_level": RiskLevel.medium,
        "priority": 6,
    },
    {
        "name": "Đủ điều kiện thẩm định bình thường",
        "description": "Tất cả kiểm tra đều pass, hồ sơ đủ điều kiện thẩm định",
        "condition_expression": "all(c.get('status') == 'pass' for c in checks) and len(checks) >= 2",
        "risk_level": RiskLevel.low,
        "priority": 1,
    },
]


async def seed_risk_rules(session: AsyncSession) -> None:
    """Seed risk rules — skip nếu đã có."""
    existing = (await session.execute(select(RiskRule))).scalars().all()
    if existing:
        logger.info("Risk rules already seeded (%d rules), skipping", len(existing))
        return

    for r in RISK_RULES_DATA:
        session.add(RiskRule(**r))

    await session.commit()
    logger.info("Seeded %d risk rules", len(RISK_RULES_DATA))
