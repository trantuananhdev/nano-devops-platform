from __future__ import annotations

import re


def _trigrams(s: str) -> set[str]:
    # Normalize for trigrams: lower, basic clean
    s = s.lower().strip()
    s = re.sub(r"[^0-9a-zàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < 3:
        return {s} if s else set()
    return {s[i : i + 3] for i in range(len(s) - 2)}


def trigram_jaccard(a: str, b: str) -> float:
    A = _trigrams(a)
    B = _trigrams(b)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0


def _normalize_for_grounding(text: str) -> str:
    """Normalize text for better matching: lowercase, strip punctuation, remove speaker tags."""
    if not text:
        return ""
    # Remove [SPEAKER]: or Speaker: tags
    t = re.sub(r"^\[(TEEN|MENTOR|PARENT)\]\s*:\s*", "", text, flags=re.IGNORECASE)
    t = re.sub(r"^(TEEN|MENTOR|PARENT)\s*:\s*", "", t, flags=re.IGNORECASE)
    
    t = t.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    return " ".join(t.split())


def grounding_score(*, observation: str, evidence: str, transcript_chunks: list[str]) -> float:
    """
    MVP grounding:
    - If evidence is found verbatim in transcript chunks => score 1.0 (hard grounding).
    - Else try fuzzy matching between evidence and chunks.
    - Else fallback to trigram Jaccard similarity between observation and chunks.
    """
    ev_norm = _normalize_for_grounding(evidence)
    if ev_norm:
        # 1. Hard verbatim match (after normalization)
        for c in transcript_chunks:
            if ev_norm in _normalize_for_grounding(c):
                return 1.0
        
        # 2. Fuzzy match for evidence (handles small AI-generated changes)
        best_ev_match = 0.0
        for c in transcript_chunks:
            # Match normalized evidence against normalized chunk
            best_ev_match = max(best_ev_match, trigram_jaccard(ev_norm, _normalize_for_grounding(c)))
        
        if best_ev_match > 0.8: # Threshold for evidence
            return best_ev_match

    # 3. Fallback to matching the observation (summary) against the transcript
    best_obs_match = 0.0
    obs_norm = _normalize_for_grounding(observation)
    for c in transcript_chunks:
        best_obs_match = max(best_obs_match, trigram_jaccard(obs_norm, _normalize_for_grounding(c)))
    return best_obs_match
