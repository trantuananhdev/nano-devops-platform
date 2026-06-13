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
        # Confidence: high when results list is populated with detail
        "confidence_fn": lambda o, passed: (
            min(0.95, 0.65 + len(o.get("results", [])) * 0.1) if passed
            else 0.80  # Fail with no results is usually clear-cut
        ),
    },
    "ErpBudgetCheck": {
        "label": "Đối chiếu Tổng mức đầu tư (ERP)",
        "pass_key": lambda o: not o.get("exceeded", False),
        "desc_pass": "Nằm trong hạn mức an toàn.",
        "desc_fail": "Vượt quá ngân sách đã phê duyệt.",
        "confidence_fn": lambda o, passed: (
            0.90 if o.get("budget_amount") and o.get("requested_amount") else 0.65
        ),
    },
    "ErpInventoryCheck": {
        "label": "Kiểm tra Vật tư tồn kho (ERP INV)",
        "pass_key": lambda o: not o.get("waste_warning", False),
        "desc_pass": "Không có vật tư tồn đọng.",
        "desc_fail": "Phát hiện vật tư tồn kho — cảnh báo lãng phí.",
        "confidence_fn": lambda o, passed: (
            0.85 if "inventory_items" in o else 0.60
        ),
    },
    "TechnicalStandardCheck": {
        "label": "Kiểm tra Tiêu chuẩn kỹ thuật",
        "pass_key": lambda o: not o.get("issues") and o.get("compliant", True),
        "desc_pass": "Tiêu chuẩn kỹ thuật đáp ứng yêu cầu.",
        "desc_fail": "Phát hiện vấn đề trong tiêu chuẩn kỹ thuật.",
        "confidence_fn": lambda o, passed: (
            0.80 if o.get("checked_items") else 0.55
        ),
    },
    "ProcurementCheck": {
        "label": "Kiểm tra Quy trình Mua sắm",
        "pass_key": lambda o: not o.get("violations") and o.get("compliant", True),
        "desc_pass": "Quy trình mua sắm hợp lệ.",
        "desc_fail": "Phát hiện vi phạm quy trình mua sắm.",
        "confidence_fn": lambda o, passed: (
            0.82 if o.get("checked_items") else 0.58
        ),
    },
    "DOfficeLookup": {
        "label": "Đối chiếu DOffice",
        "pass_key": lambda o: o.get("signed", False),
        "desc_pass": "Hồ sơ đã đăng ký và ký.",
        "desc_fail": "Hồ sơ chưa đủ chữ ký.",
        "confidence_fn": lambda o, passed: (
            0.92 if "document_id" in o else 0.60
        ),
    },
    "PmisProjectCheck": {
        "label": "Checklist PMIS",
        "pass_key": lambda o: o.get("on_schedule", True),
        "desc_pass": "Dự án đúng tiến độ.",
        "desc_fail": "Dự án trễ tiến độ.",
        "confidence_fn": lambda o, passed: (
            0.88 if "delay_days" in o else 0.62
        ),
    },
    "EcoOcrExtract": {
        "label": "Trích xuất nội dung PDF",
        "pass_key": lambda o: o.get("extracted_text") is not None,
        "desc_pass": "Đã trích xuất nội dung PDF.",
        "desc_fail": "Không thể trích xuất PDF.",
        "confidence_fn": lambda o, passed: (
            min(0.95, 0.5 + len(o.get("extracted_text", "")) / 2000) if passed else 0.90
        ),
    },
}

# Default confidence when tool is not in templates
_DEFAULT_CONFIDENCE_FN = lambda o, passed: _compute_generic_confidence(o, passed)


def _compute_generic_confidence(output: dict[str, Any], passed: bool) -> float:
    """Generic confidence estimation based on output richness.

    Factors:
    - Output field count: more fields = more information
    - Presence of 'mock' flag: simulated outputs are less confident
    - Presence of structured data (lists, nested dicts)
    """
    if not output:
        return 0.30  # Empty output → very uncertain

    # Mock/simulated tool outputs
    if output.get("mock") or output.get("simulated") or output.get("_mock"):
        # Mocks are less reliable but still carry signal
        field_richness = min(len(output) / 6, 0.3)
        return 0.45 + field_richness  # 0.45-0.75 range

    # Count meaningful fields (non-metadata)
    skip_keys = {"error", "mock", "simulated", "_mock", "tool_name", "dossier_id", "doc_no"}
    meaningful = [k for k in output if k not in skip_keys and output[k] is not None]
    field_score = min(len(meaningful) / 5, 0.25)

    # Structured data presence (lists or nested dicts = richer info)
    has_structure = any(
        isinstance(v, (list, dict)) and v
        for k, v in output.items()
        if k not in skip_keys
    )
    structure_bonus = 0.10 if has_structure else 0.0

    # Base confidence differs slightly by pass/fail
    # Fail is usually clearer (tool found a problem) vs pass (absence of problem)
    base = 0.70 if passed else 0.72

    return min(base + field_score + structure_bonus, 0.94)


def normalize_tool_input(dossier: Dossier, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge dossier context into tool input.

    Injects:
    - dossier_id, doc_no, title, query (baseline)
    - unit: dossier's organizational unit (helps tools contextualize)
    - pdf_excerpt: first 600 chars of pdf_text if available (helps AI-backed tools)
    - risk_level: current known risk level (helps tools calibrate severity)

    Coerces dossier_id to int — LLM may produce "123" (string).
    """
    pdf_text = getattr(dossier, "pdf_text", None) or ""
    pdf_excerpt = pdf_text[:600].strip() if pdf_text else ""

    base = {
        "dossier_id": dossier.id,
        "doc_no": dossier.doc_no,
        "title": dossier.title,
        "query": dossier.title,
        "unit": getattr(dossier, "unit", "") or "",
    }
    if pdf_excerpt:
        base["pdf_excerpt"] = pdf_excerpt
    risk = getattr(dossier, "risk_level", None)
    if risk:
        base["risk_level"] = risk.value if hasattr(risk, "value") else str(risk)

    if raw:
        base.update(raw)

    # Ensure required keys are present
    base.setdefault("dossier_id", dossier.id)
    base.setdefault("doc_no", dossier.doc_no)
    base.setdefault("title", dossier.title)
    base.setdefault("query", dossier.title)

    try:
        base["dossier_id"] = int(base["dossier_id"])
    except (TypeError, ValueError):
        base["dossier_id"] = dossier.id

    return base


def build_check(tool_name: str, output: dict[str, Any]) -> dict[str, Any]:
    """Build a standardized check result from tool output.

    Returns:
      tool, label, status (pass/fail/warning), desc, details, confidence (0.0-1.0)

    Confidence score semantics:
      > 0.85: High confidence — Critic can trust this result
      0.65-0.85: Medium — worth a second look on borderline cases
      < 0.65: Low — mock or sparse output, treat as indicative only
    """
    tpl = CHECK_TEMPLATES.get(tool_name)
    if tpl is None:
        tpl = {
            "label": tool_name,
            "pass_key": lambda o: not o.get("error"),
            "desc_pass": "Kiểm tra hoàn tất.",
            "desc_fail": "Phát hiện vấn đề.",
            "confidence_fn": _DEFAULT_CONFIDENCE_FN,
        }

    passed = tpl["pass_key"](output)

    # Compute confidence
    conf_fn = tpl.get("confidence_fn", _DEFAULT_CONFIDENCE_FN)
    try:
        confidence = float(conf_fn(output, passed))
    except Exception:
        confidence = _compute_generic_confidence(output, passed)
    confidence = max(0.0, min(1.0, confidence))

    # Determine status: warning when passed but low confidence
    if passed and confidence < 0.60:
        status = "warning"
    elif not passed:
        status = "fail"
    else:
        status = "pass"

    return {
        "tool": tool_name,
        "label": tpl["label"],
        "status": status,
        "desc": tpl["desc_pass"] if passed else tpl["desc_fail"],
        "details": json.dumps(output, ensure_ascii=False, indent=2),
        "confidence": round(confidence, 3),
    }
