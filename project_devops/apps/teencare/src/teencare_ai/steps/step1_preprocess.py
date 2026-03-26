from __future__ import annotations

import re
from typing import Callable

from teencare_ai.core.types import Speaker, Step1Output, Turn


_FILLER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(ừ+|ờ+|à+|ừm+|um+|kiểu là|kiểu|hơi hơi|kiểu kiểu)\b", re.IGNORECASE),
    re.compile(r"\s{2,}"),
]


def _clean_text(text: str) -> str:
    t = text.strip()
    for p in _FILLER_PATTERNS:
        t = p.sub(" ", t)
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return t.strip()


def _split_turn_candidates(raw_transcript: str) -> list[str]:
    raw = raw_transcript.replace("\r\n", "\n").strip()
    if not raw:
        return []

    if ">>" in raw:
        parts = [p.strip() for p in raw.split(">>")]
        return [p for p in parts if p]

    lines = [ln.strip() for ln in raw.split("\n")]
    lines = [ln for ln in lines if ln]
    if len(lines) >= 2:
        return lines

    return [raw]


def _infer_speaker_with_confidence(text: str) -> tuple[Speaker, float]:
    t = text.strip()
    if not t:
        return "UNKNOWN", 0.0

    # 1. Standard Tags [TEEN]: or [MENTOR]:
    m = re.match(r"^\[(TEEN|MENTOR|PARENT)\]\s*:\s*(.+)$", t, re.IGNORECASE)
    if m:
        return m.group(1).upper(), 1.0  # type: ignore[return-value]

    # 2. Simple Tags Mentor: or Teen: (Common in raw text)
    m_simple = re.match(r"^(MENTOR|TEEN|PARENT)\s*:\s*(.+)$", t, re.IGNORECASE)
    if m_simple:
        return m_simple.group(1).upper(), 0.95  # type: ignore[return-value]

    # 3. Heuristics
    if t.endswith("?") or re.search(r"\b(con|em)\s+có\b", t.lower()):
        return "MENTOR", 0.8

    if re.search(r"\b(mẹ|bố|ba|phụ huynh|con tôi)\b", t.lower()):
        return "PARENT", 0.65

    # Colloquial/short emotional lines often teen
    if len(t.split()) <= 12:
        return "TEEN", 0.65

    return "UNKNOWN", 0.2


def _strip_speaker_tag(text: str) -> str:
    """Removes speaker tags like [MENTOR]: or Mentor: from the beginning of the string."""
    t = text.strip()
    t = re.sub(r"^\[(TEEN|MENTOR|PARENT)\]\s*:\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(TEEN|MENTOR|PARENT)\s*:\s*", "", t, flags=re.IGNORECASE)
    return t.strip()


def preprocess_and_diarize(
    session_id: str,
    raw_transcript: str,
    *,
    resolve_ambiguous: Callable[[str], Speaker] | None = None,
    ambiguous_threshold: float = 0.5,
) -> Step1Output:
    candidates = _split_turn_candidates(raw_transcript)
    turns: list[Turn] = []
    unknown = 0
    empty = 0
    llm_assisted = 0
    per_turn_conf: list[float] = []

    for idx, c in enumerate(candidates, start=1):
        cleaned = _clean_text(c)
        if not cleaned:
            empty += 1
            continue
        spk, conf = _infer_speaker_with_confidence(cleaned)
        
        # Strip tag if recognized to avoid double tagging in Step 2
        if conf >= 0.9:
            cleaned = _strip_speaker_tag(cleaned)
            
        if conf < ambiguous_threshold and resolve_ambiguous is not None:
            spk = resolve_ambiguous(cleaned)
            llm_assisted += 1
            conf = max(conf, 0.7 if spk != "UNKNOWN" else conf)
        if spk == "UNKNOWN":
            unknown += 1
        per_turn_conf.append(conf)
        turns.append({"speaker": spk, "text": cleaned, "index": idx})

    denom = max(1, len(turns) + empty)
    unknown_ratio = unknown / max(1, len(turns))
    empty_ratio = empty / denom
    conf_avg = sum(per_turn_conf) / max(1, len(per_turn_conf))
    quality_score = max(0.0, min(1.0, 0.8 * conf_avg + 0.2 * (1.0 - unknown_ratio - empty_ratio)))

    return {
        "session_id": session_id,
        "turns": turns,
        "quality_score": float(quality_score),
        "_meta": {
            "method": "hybrid_rule_llm" if llm_assisted > 0 else "rule_based",
            "llm_assisted_turns": llm_assisted,
            "avg_turn_confidence": round(conf_avg, 4),
        },
    }

