from __future__ import annotations

from teencare_ai.core.types import Step1Output, Step2Output
from teencare_ai.storage.profiles import ProfileStore


def _approx_tokens(text: str) -> int:
    # MVP heuristic: 1 token ~ 0.75 word (very rough); we just need a guardrail.
    words = max(1, len(text.split()))
    return int(words / 0.75)


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    words = text.split()
    if not words:
        return ""
    # Convert tokens back to words using the same ratio.
    max_words = max(1, int(max_tokens * 0.75))
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip()


def assemble_context(
    step1: Step1Output,
    teen_id: str,
    family_goals: list[str],
    profile_store: ProfileStore,
    token_budget: dict[str, int] | None = None,
) -> Step2Output:
    budget = token_budget or {"profile_tokens": 100, "history_tokens": 300, "session_tokens": 800}

    profile = profile_store.get_profile(teen_id)
    layer_1_profile = profile.profile_summary if profile else ""
    if family_goals:
        goals = ", ".join([g.strip() for g in family_goals if g.strip()])
        if goals:
            layer_1_profile = (layer_1_profile + f"\nFamily goals: {goals}").strip()
    layer_1_profile = _truncate_to_tokens(layer_1_profile, budget["profile_tokens"])

    # Phase 1: history left empty (top-k by date can be added later).
    layer_2_history: list[str] = []

    # Layer 3: formatted clean turns.
    session_lines = [f"[{t['speaker']}]: {t['text']}" for t in step1["turns"]]
    session_text = "\n".join(session_lines)
    session_text = _truncate_to_tokens(session_text, budget["session_tokens"])
    layer_3_session = [ln for ln in session_text.split("\n") if ln.strip()]

    return {
        "session_id": step1["session_id"],
        "context": {
            "layer_1_profile": layer_1_profile,
            "layer_2_history": layer_2_history,
            "layer_3_session": layer_3_session,
        },
        "token_budget": {
            "profile_tokens": budget["profile_tokens"],
            "history_tokens": budget["history_tokens"],
            "session_tokens": budget["session_tokens"],
        },
    }

