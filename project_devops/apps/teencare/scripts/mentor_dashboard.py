"""
TeenCare Mentor Dashboard — Streamlit UI wired to `run_pipeline`.

Chạy trong Docker (platform): `streamlit run scripts/mentor_dashboard.py`
PYTHONPATH=/app/src — import `teencare_ai` không cần pip -e local.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st

# Local dev: allow `streamlit run` without PYTHONPATH
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_APP_ROOT / "src"))

from teencare_ai.core.pipeline import run_pipeline
from teencare_ai.core.types import PipelineConfig

SAMPLES_RAW = _APP_ROOT / "samples" / "raw"
SESSION_REAL_TXT = SAMPLES_RAW / "session_real_001.txt"
SESSION_SAMPLE_JSON = SAMPLES_RAW / "session_sample_003.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_demo_synthetic() -> None:
    st.session_state["raw_transcript_input"] = (
        "[MENTOR]: Chào con, tuần vừa rồi của con thế nào?\n"
        "[TEEN]: Dạ cũng bình thường ạ, nhưng mà con thấy hơi mệt.\n"
        "[MENTOR]: Con mệt vì việc học hay có chuyện gì khác không?\n"
        "[TEEN]: Dạ, tuần này con vướng ba lịch một lúc luôn, bài tập trên trường cũng nhiều nên con thấy hơi overload.\n"
        "[MENTOR]: Khi thấy quá tải như vậy, con thường làm gì?\n"
        "[TEEN]: Con hay thấy khó chịu, đôi khi con lỡ cáu với mọi người xung quanh ấy.\n"
        "[MENTOR]: Mẹ có biết con đang áp lực như vậy không?\n"
        "[TEEN]: Dạ không, con ngại nói nhiều vì sợ mẹ lo, nên mẹ hỏi thì con cứ bảo là bình thường thôi.\n"
        "[MENTOR]: Hôm nay con có trễ deadline nào không?\n"
        "[TEEN]: Dạ có, hôm nay con trễ deadline môn Toán, cô giáo nhắc nhiều nên con thấy áp lực lắm.\n"
        "[TEEN]: Cuối tuần này con chỉ muốn ngủ thôi, con không muốn đi học thêm lớp nào nữa đâu."
    )
    st.session_state["teen_id_input"] = "teen_demo_001"
    st.session_state["family_goals_input"] = "giảm áp lực học tập\ntăng tính tự giác"
    st.session_state["input_method_choice"] = "Nhập Text trực tiếp"


def _load_demo_real_txt() -> None:
    if SESSION_REAL_TXT.is_file():
        st.session_state["raw_transcript_input"] = SESSION_REAL_TXT.read_text(encoding="utf-8")
        st.session_state["teen_id_input"] = "teen_demo_001"
        st.session_state["family_goals_input"] = (
            "cải thiện giao tiếp với mẹ\ngiảm cáu kỉnh khi quá tải lịch"
        )
        st.session_state["input_method_choice"] = "Nhập Text trực tiếp"
    else:
        st.session_state["_demo_real_missing"] = True


def _load_demo_json_sample() -> None:
    if SESSION_SAMPLE_JSON.is_file():
        data = json.loads(SESSION_SAMPLE_JSON.read_text(encoding="utf-8"))
        st.session_state["raw_transcript_input"] = data.get("raw_transcript", "")
        st.session_state["teen_id_input"] = data.get("teen_id", "teen_demo_001")
        goals = data.get("family_goals") or []
        st.session_state["family_goals_input"] = "\n".join(str(g) for g in goals)
        st.session_state["input_method_choice"] = "Nhập Text trực tiếp"


def _gemini_configured() -> bool:
    return bool((os.environ.get("GEMINI_API_KEY") or "").strip())


def _render_output(output: dict) -> None:
    flag = (output.get("flag") or "").strip()
    meta = output.get("_meta") or {}
    delivery = output.get("_delivery") or {}

    st.markdown("#### Trạng thái pipeline")
    if flag == "insufficient_data":
        st.warning(
            "Dữ liệu đầu vào không đủ (quá ít turn hoặc chất lượng transcript thấp). "
            "Hệ thống cố tình không suy diễn để tránh sai lệch."
        )
    elif flag == "needs_review":
        st.error(
            "Output không vượt qua validation (schema/grounding). "
            "Cần mentor xem lại transcript hoặc cấu hình ngưỡng."
        )
        if meta.get("error"):
            st.code(str(meta["error"]), language="text")
    elif flag == "stale_data":
        st.warning("Đang dùng output cache do timeout LLM — đánh dấu stale_data.")
    elif flag in ("llm_error", "rate_limit_exceeded"):
        st.error(f"Lỗi LLM / hạn mức: {flag}")
    elif flag:
        st.info(f"Flag: `{flag}`")

    risk = output.get("risk_level", "low")
    rr = output.get("risk_reasoning", "")
    if risk == "high":
        st.error(f"**Rủi ro:** {risk.upper()} — {rr}")
    elif risk == "medium":
        st.warning(f"**Rủi ro:** {risk.upper()} — {rr}")
    else:
        st.success(f"**Rủi ro:** {risk.upper()} — {rr}")

    st.caption(f"confidence: `{output.get('confidence', '')}`")

    if delivery:
        with st.expander("Bản gửi phụ huynh (delivery preview)", expanded=True):
            st.markdown(f"**{delivery.get('title', '')}**")
            for b in delivery.get("summary_bullets") or []:
                st.markdown(f"- {b}")
            for a in delivery.get("actions") or []:
                st.markdown(
                    f"- **{a.get('label', '')}** — _{a.get('timing', '')}_  \n  {a.get('details', '')}"
                )

    insights = output.get("insights") or []
    if insights:
        st.markdown("### Insights (có quote)")
        for idx, ins in enumerate(insights):
            title = (ins.get("observation") or "")[:120]
            with st.expander(f"{idx + 1}. {title}", expanded=(idx == 0)):
                st.markdown(f"**Quan sát:** {ins.get('observation', '')}")
                st.markdown(f"**Bằng chứng (quote):** _{ins.get('evidence', '')}_")
                pm = (ins.get("pattern_match") or "").strip()
                if pm:
                    st.caption(f"Pattern: {pm}")

    recs = output.get("recommendations") or []
    if recs:
        st.markdown("### Gợi ý hành động")
        for idx, rec in enumerate(recs):
            st.success(
                f"**{idx + 1}. {rec.get('action', '')}**\n\n"
                f"Thời điểm: {rec.get('timing', '')}\n\n"
                f"Kỳ vọng: {rec.get('expected_outcome', '')}"
            )

    if meta:
        with st.expander("Kỹ thuật: _meta (latency, validation, step1)", expanded=False):
            st.json(meta)


st.set_page_config(
    page_title="TeenCare AI - Mentor Dashboard",
    page_icon="🧠",
    layout="wide",
)

st.title("TeenCare AI — Mentor Dashboard")

# --- HELP SECTION ---
with st.sidebar:
    with st.popover("❓ Trợ giúp & Hướng dẫn (Get Help)", use_container_width=True):
        st.markdown("""
        ### 🧠 Tổng quan Dự án
        **TeenCare Parent Copilot** là hệ thống AI hỗ trợ Mentor phân tích các buổi học 1-on-1 để gửi báo cáo chuyên sâu cho phụ huynh.
        
        ### 🎯 Đề bài & Thách thức
        - **Quá tải**: Mentor mất 30-60p viết báo cáo sau mỗi buổi học.
        - **Chủ quan**: Báo cáo dễ mang tính cảm tính, thiếu bằng chứng cụ thể.
        - **An toàn**: Cần phát hiện sớm các rủi ro tâm lý (Risk Level) một cách khách quan.

        ### 🚀 Giải pháp (Solution)
        Hệ thống sử dụng **Pipeline 5 bước** kết hợp **Gemini 2.5 Flash** và thuật toán **Fuzzy Grounding** để đảm bảo mọi Insight đều có bằng chứng (Evidence) trích dẫn trực tiếp từ transcript.

        ### ⚙️ Luồng hoạt động (Workflow)
        1. **Pre-processing**: Làm sạch text, gán nhãn người nói (Diarization).
        2. **Context Assembly**: Hợp nhất Transcript + Hồ sơ học sinh + Mục tiêu gia đình.
        3. **LLM Reasoning**: AI suy luận tìm Insight, đề xuất hành động và đánh giá rủi ro.
        4. **Validation**: Kiểm chứng chéo Insight với Transcript gốc (Chống ảo giác AI).
        5. **Delivery**: Đóng gói thành bản tin tóm tắt cho phụ huynh.

        ### 🛠 Giải thích Thông số (Tuning)
        - **`min_turns`**: Số câu đối thoại tối thiểu. Nếu buổi học quá ngắn (vd < 10 câu), AI sẽ từ chối phân tích để tránh kết luận vội vàng.
        - **`min_quality_score`**: Độ tin cậy của dữ liệu đầu vào (0.0 - 1.0). Dựa trên việc AI có nhận diện được ai đang nói hay không. Nếu transcript quá lộn xộn, hệ thống sẽ cảnh báo.
        - **`grounding_threshold`**: Độ khắt khe khi kiểm chứng bằng chứng (0.0 - 1.0). 
            - *Cao (0.8+)*: AI phải trích dẫn chính xác gần như từng chữ.
            - *Thấp (0.5+)*: Chấp nhận AI diễn đạt lại ý (paraphrase) một chút.

        ### 📥 Input & 📤 Output
        - **Input**: File `.txt` hoặc text thô, ID học sinh, Mục tiêu gia đình (Family Goals).
        - **Output**: Mức độ rủi ro (Risk), Insight kèm bằng chứng (Quote), và các hành động gợi ý (Recommendations) kèm thời điểm thực hiện.
        """)

st.markdown(
    "Upload file `.txt` hoặc dán transcript buổi học. Output: insight grounded + action cho phụ huynh."
)

if "teen_id_input" not in st.session_state:
    st.session_state["teen_id_input"] = "teen_demo_001"
if "family_goals_input" not in st.session_state:
    st.session_state["family_goals_input"] = "cải thiện kỷ luật\ngiảm screen time"
if "raw_transcript_input" not in st.session_state:
    st.session_state["raw_transcript_input"] = ""
if "input_method_choice" not in st.session_state:
    st.session_state["input_method_choice"] = "Nhập Text trực tiếp"
if "last_pipeline_output" not in st.session_state:
    st.session_state["last_pipeline_output"] = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Đầu vào")

    c_demo1, c_demo2, c_demo3 = st.columns(3)
    with c_demo1:
        st.button("Mẫu tổng hợp", on_click=_load_demo_synthetic, use_container_width=True)
    with c_demo2:
        st.button("Mẫu buổi thực tế (.txt)", on_click=_load_demo_real_txt, use_container_width=True)
    with c_demo3:
        st.button("Mẫu JSON (speaker tags)", on_click=_load_demo_json_sample, use_container_width=True)

    if st.session_state.pop("_demo_real_missing", False):
        st.warning(f"Không tìm thấy file mẫu: `{SESSION_REAL_TXT}` (rebuild image hoặc mount samples).")

    st.divider()

    input_method = st.radio(
        "Phương thức nhập transcript",
        ["Upload File (.txt)", "Nhập Text trực tiếp"],
        key="input_method_choice",
    )

    raw_transcript = ""
    if input_method == "Upload File (.txt)":
        uploaded_file = st.file_uploader("File .txt buổi học", type=["txt"])
        if uploaded_file is not None:
            raw_transcript = uploaded_file.getvalue().decode("utf-8")
            st.text_area("Xem trước file", value=raw_transcript, height=200, disabled=True)
    else:
        raw_transcript = st.text_area(
            "Transcript thô",
            height=320,
            key="raw_transcript_input",
            placeholder="Dán nội dung hoặc dùng nút mẫu…",
        )

    analyze_btn = st.button("Chạy phân tích", type="primary", use_container_width=True)

with st.sidebar:
    st.header("Cấu hình")
    api_key = st.text_input(
        "Gemini API Key (tùy chọn)",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Để trống = dùng Mock LLM trong container (demo offline). Nhập key = gọi Gemini như pipeline production.",
    )
    if api_key.strip():
        os.environ["GEMINI_API_KEY"] = api_key.strip()

    if _gemini_configured():
        st.success("Đang dùng Gemini (GEMINI_API_KEY).")
    else:
        st.info("Chưa có API key — pipeline dùng **MockLLMClient** (deterministic, phù hợp demo).")

    st.divider()
    st.subheader("Hồ sơ & mục tiêu")
    teen_id = st.text_input("Teen ID", key="teen_id_input")
    family_goals_raw = st.text_area(
        "Mục tiêu gia đình (mỗi dòng một mục)",
        key="family_goals_input",
    )
    family_goals = [g.strip() for g in family_goals_raw.split("\n") if g.strip()]

    with st.expander("Ngưỡng pipeline (tuning demo)", expanded=False):
        min_turns = st.number_input(
            "min_turns",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            help="Số câu hội thoại tối thiểu để bắt đầu phân tích. Dưới ngưỡng này AI sẽ báo 'insufficient_data'.",
        )
        min_quality = st.slider(
            "min_quality_score",
            0.0,
            1.0,
            0.5,
            0.05,
            help="Độ tin cậy của việc nhận diện người nói. Nếu transcript quá hỗn loạn, AI sẽ dừng lại.",
        )
        grounding_th = st.slider(
            "grounding_threshold",
            0.0,
            1.0,
            0.75,
            0.05,
            help="Ngưỡng đối soát bằng chứng. Cao = chính xác tuyệt đối; Thấp = cho phép AI tóm lược ý.",
        )

with col2:
    st.subheader("Kết quả")

    if analyze_btn:
        if not (raw_transcript or "").strip():
            st.warning("Cần nội dung transcript (upload hoặc dán).")
            st.session_state["last_pipeline_output"] = None
        else:
            with st.spinner("Đang chạy pipeline…"):
                try:
                    session_input = {
                        "session_id": f"session_{uuid4().hex[:8]}",
                        "teen_id": teen_id,
                        "raw_transcript": raw_transcript.strip(),
                        "session_date": _utc_now_iso(),
                        "family_goals": family_goals,
                    }
                    cfg = PipelineConfig(
                        min_turns=int(min_turns),
                        min_quality_score=float(min_quality),
                        grounding_threshold=float(grounding_th),
                    )
                    output = run_pipeline(session_input, config=cfg)
                    st.session_state["last_pipeline_output"] = output
                except Exception as e:
                    st.session_state["last_pipeline_output"] = None
                    st.exception(e)

    out = st.session_state.get("last_pipeline_output")
    if out is not None:
        _render_output(out)
        if st.checkbox("Xem JSON đầy đủ", value=False, key="show_full_json"):
            st.json(out)
