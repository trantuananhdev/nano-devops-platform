from __future__ import annotations

import re

from teencare_ai.core.types import Speaker


class DiarizationClassifier:
    def classify_turn(self, text: str) -> Speaker:
        raise NotImplementedError


class MockDiarizationClassifier(DiarizationClassifier):
    """
    Deterministic fallback classifier for ambiguous turns.
    Replace with real LLM classification endpoint in Phase 2.
    """

    def classify_turn(self, text: str) -> Speaker:
        t = text.lower().strip()
        if "?" in t or re.search(r"\b(con|em)\s+(có|thấy|muốn|đang)\b", t):
            return "MENTOR"
        if re.search(r"\b(mẹ|bố|ba|phụ huynh|con tôi)\b", t):
            return "PARENT"
        if re.search(r"\b(con|em|mình)\b", t):
            return "TEEN"
        return "UNKNOWN"

