"""
CRM Integration — tích hợp lead BĐS vào hệ thống quản lý ngoài (Odoo / HubSpot / custom).

Lớp này cung cấp interface thống nhất để đẩy lead đã phân tích ra ngoài.
Mặc định tích hợp với Odoo CRM qua XML-RPC, graceful degradation nếu không kết nối được.
"""

import logging
import xmlrpc.client
from typing import Any, Optional

from odoo_agent import generate_department_brief

logger = logging.getLogger(__name__)


class CrmIntegration:
    """
    Tích hợp lead BĐS ra hệ thống CRM ngoài.
    Hiện tại: Odoo CRM qua XML-RPC.
    Graceful degradation: log warning nếu Odoo không khả dụng — pipeline không bị block.
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self._uid: Optional[int] = None
        self._models = None

    def connect(self) -> bool:
        """Kết nối và xác thực với Odoo CRM. Trả về False nếu thất bại."""
        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
            logger.info("CRM Integration: kết nối Odoo thành công (uid=%s)", self._uid)
            return True
        except Exception as exc:
            logger.warning("CRM Integration: không kết nối được Odoo: %s", exc)
            return False

    def push_lead(self, lead_data: dict[str, Any]) -> Optional[int]:
        """
        Đẩy lead BĐS đã xử lý vào Odoo CRM.
        Trả về Odoo lead ID nếu thành công, None nếu thất bại (non-blocking).
        """
        if not self.connect():
            logger.warning("CRM push skipped — Odoo không khả dụng.")
            return None

        try:
            brief = generate_department_brief(lead_data)
            urgency = lead_data.get("urgency", "medium")
            intent = lead_data.get("intent", "other")

            # Xác định workflow CRM dựa trên BĐS context
            if urgency == "critical":
                workflow = "critical_followup"
            elif urgency == "high" and intent in ("purchase", "schedule_viewing"):
                workflow = "hot_followup"
            elif intent == "legal_inquiry":
                workflow = "legal_review"
            elif lead_data.get("transaction_type") == "invest":
                workflow = "investment_nurture"
            else:
                workflow = "standard_review"

            property_label = {
                "apartment": "Căn hộ", "house": "Nhà/Biệt thự",
                "land": "Đất nền", "commercial": "Shophouse/TMDV",
            }.get(lead_data.get("property_type", "other"), "BĐS")

            odoo_data = {
                "name": lead_data.get("customer_name") or f"Lead {lead_data.get('channel', 'CRM')}",
                "contact_name": lead_data.get("customer_name"),
                "phone": lead_data.get("phone"),
                "description": lead_data.get("raw_text", ""),
                # BĐS-specific fields
                "x_property_type": lead_data.get("property_type"),
                "x_location": lead_data.get("location"),
                "x_transaction_type": lead_data.get("transaction_type"),
                "x_budget_range": lead_data.get("budget_range"),
                "x_bedroom_count": lead_data.get("bedroom_count"),
                # AI analysis fields
                "x_ai_summary": lead_data.get("summary", ""),
                "x_ai_dept_brief": brief,
                "x_ai_urgency": urgency,
                "x_ai_intent": intent,
                "x_ai_sentiment": lead_data.get("sentiment"),
                "x_ai_workflow": workflow,
                # Source tracking
                "x_source_channel": lead_data.get("channel"),
                "tag_ids": [(4, self._get_or_create_tag(f"BĐS-{property_label}"))],
            }

            lead_id: int = self._models.execute_kw(  # type: ignore[union-attr]
                self.db, self._uid, self.password,
                "crm.lead", "create", [odoo_data],
            )
            logger.info("CRM Integration: đã tạo lead Odoo id=%s (channel=%s)", lead_id, lead_data.get("channel"))
            return lead_id
        except Exception as exc:
            logger.error("CRM Integration: tạo lead thất bại: %s", exc)
            return None

    def _get_or_create_tag(self, tag_name: str) -> int:
        """Lấy hoặc tạo tag trong Odoo (best effort)."""
        try:
            ids = self._models.execute_kw(  # type: ignore[union-attr]
                self.db, self._uid, self.password,
                "crm.tag", "search", [[["name", "=", tag_name]]],
            )
            if ids:
                return ids[0]
            return self._models.execute_kw(  # type: ignore[union-attr]
                self.db, self._uid, self.password,
                "crm.tag", "create", [{"name": tag_name}],
            )
        except Exception:
            return 0


def create_crm_integration() -> CrmIntegration:
    """Factory từ environment variables."""
    import os
    return CrmIntegration(
        url=os.getenv("ODOO_URL", "http://odoo:8069"),
        db=os.getenv("ODOO_DB", "odoo"),
        username=os.getenv("ODOO_USERNAME", "admin"),
        password=os.getenv("ODOO_PASSWORD", "admin"),
    )


# Backward compat alias
OdooIntegration = CrmIntegration
