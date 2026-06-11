"""Shared helpers for orchestrator modules (T-17)."""

import json
from typing import Any

from app.models.entities import Dossier

CHECK_TEMPLATES: dict[str, dict[str, Any]] = {
    "LegalGraphRAG": {
        "label": "Kiểm tra căn cứ pháp lý",
        "pass_key": lambda o: len(o.get("results", [])) > 0,
        "desc_pass": "Đã đính kèm văn bản, còn hiệu lực.",
        "desc_fail": "Thiếu căn cứ pháp lý.",
    },
    "ErpBudgetCheck": {
        "label": "Đối chiếu Tổng mức đầu tư (ERP)",
        "pass_key": lambda o: not o.get("exceeded", False),
        "desc_pass": "Nằm trong hạn mức an toàn.",
        "desc_fail": "Vượt quá ngân sách đã phê duyệt.",
    },
    "ErpInventoryCheck": {
        "label": "Kiểm tra Vật tư tồn kho (ERP INV)",
        "pass_key": lambda o: not o.get("waste_warning", False),
        "desc_pass": "Không có vật tư tồn đọng.",
        "desc_fail": "Phát hiện vật tư tồn kho — cảnh báo lãng phí.",
    },
    "DOfficeLookup": {
        "label": "Đối chiếu DOffice",
        "pass_key": lambda o: o.get("signed", False),
        "desc_pass": "Hồ sơ đã đăng ký và ký.",
        "desc_fail": "Hồ sơ chưa đủ chữ ký.",
    },
    "PmisProjectCheck": {
        "label": "Checklist PMIS",
        "pass_key": lambda o: o.get("on_schedule", True),
        "desc_pass": "Dự án đúng tiến độ.",
        "desc_fail": "Dự án trễ tiến độ.",
    },
    "EcoOcrExtract": {
        "label": "Trích xuất nội dung PDF",
        "pass_key": lambda o: o.get("extracted_text") is not None,
        "desc_pass": "Đã trích xuất nội dung PDF.",
        "desc_fail": "Không thể trích xuất PDF.",
    },
}


def normalize_tool_input(dossier: Dossier, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge dossier defaults into tool input without mutating the plan.

    Also coerces dossier_id to int so that LLM-generated string values
    (e.g. "123") do not trip the type-check in tools/base.py.
    """
    base = {
        "dossier_id": dossier.id,
        "doc_no": dossier.doc_no,
        "title": dossier.title,
        "query": dossier.title,
    }
    if raw:
        base.update(raw)
    base.setdefault("dossier_id", dossier.id)
    base.setdefault("doc_no", dossier.doc_no)
    base.setdefault("title", dossier.title)
    base.setdefault("query", dossier.title)
    # Coerce dossier_id to int — LLM may produce "123" (string) instead of 123
    try:
        base["dossier_id"] = int(base["dossier_id"])
    except (TypeError, ValueError):
        base["dossier_id"] = dossier.id
    return base


def build_check(tool_name: str, output: dict[str, Any]) -> dict[str, Any]:
    """Build a standardized check result from tool output."""
    tpl = CHECK_TEMPLATES.get(
        tool_name,
        {"label": tool_name, "pass_key": lambda o: True, "desc_pass": "OK", "desc_fail": "Fail"},
    )
    passed = tpl["pass_key"](output)
    return {
        "tool": tool_name,
        "label": tpl["label"],
        "status": "pass" if passed else "fail",
        "desc": tpl["desc_pass"] if passed else tpl["desc_fail"],
        "details": json.dumps(output, ensure_ascii=False, indent=2),
    }
