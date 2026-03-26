from __future__ import annotations

import time
from dataclasses import asdict

from teencare_ai.core.schema import validate_json
from teencare_ai.core.types import ParentCopilotOutput, PipelineConfig, SessionInput
from teencare_ai.delivery.render import render_parent_payload
from teencare_ai.llm.diarization_classifier import MockDiarizationClassifier
from teencare_ai.llm.client import LLMClient, MockLLMClient, GeminiLLMClient
from teencare_ai.steps.step1_preprocess import preprocess_and_diarize
from teencare_ai.storage.diarization_cache import DQCache
from teencare_ai.storage.output_cache import LatestOutputCache
from teencare_ai.steps.step2_context import assemble_context
from teencare_ai.storage.profiles import JsonProfileStore, ProfileStore
from teencare_ai.validation.validator import HallucinationError, validate_parent_output
from teencare_ai.validation.grounding import trigram_jaccard


def _insufficient_data_output(session_id: str) -> ParentCopilotOutput:
    return {
        "session_id": session_id,
        "insights": [],
        "risk_level": "low",
        "risk_reasoning": "insufficient data",
        "recommendations": [],
        "confidence": "low_signal",
        "flag": "insufficient_data",
    }


def _sanitize_parent_output(*, output: ParentCopilotOutput, session_id: str, step2) -> ParentCopilotOutput:
    """
    Make LLM output schema-safe and grounded-friendly:
    - ensure required keys exist and enum values are valid
    - ensure insights have pattern_match
    - repair evidence by snapping to best transcript line when close
    - drop insights that still fail grounding later (validator will enforce)
    """
    out: ParentCopilotOutput = dict(output or {})  # type: ignore[arg-type]
    out["session_id"] = str(out.get("session_id") or session_id)

    # Required scalar fields
    risk_level = str(out.get("risk_level") or "low").lower()
    if risk_level not in ("low", "medium", "high"):
        risk_level = "low"
    out["risk_level"] = risk_level  # type: ignore[assignment]

    rr = str(out.get("risk_reasoning") or "").strip()
    out["risk_reasoning"] = rr or "insufficient signal in transcript"

    conf = str(out.get("confidence") or "").strip().lower()
    if conf not in ("high", "medium", "low_signal"):
        # default to low_signal unless we have at least 1 insight
        conf = "medium" if out.get("insights") else "low_signal"
    out["confidence"] = conf  # type: ignore[assignment]

    # Optional flag in schema, but if present it must be a string (Gemini can return null).
    raw_flag = out.get("flag")
    if raw_flag is None:
        out.pop("flag", None)
    else:
        out["flag"] = str(raw_flag).strip()

    # Lists
    insights_in = out.get("insights") or []
    if not isinstance(insights_in, list):
        insights_in = []
    recs_in = out.get("recommendations") or []
    if not isinstance(recs_in, list):
        recs_in = []

    # Evidence repair: snap to closest transcript chunk when LLM paraphrases.
    chunks = step2["context"]["layer_3_session"]

    def best_chunk_for(evidence: str) -> str | None:
        ev = str(evidence or "").strip()
        if not ev:
            return None
        best = ("", 0.0)
        for c in chunks:
            s = trigram_jaccard(ev, c)
            if s > best[1]:
                best = (c, s)
        # If it's reasonably close, snap evidence to the real line (hard grounding).
        return best[0] if best[1] >= 0.55 else None

    insights_clean = []
    for it in insights_in:
        if not isinstance(it, dict):
            continue
        obs = str(it.get("observation") or "").strip()
        ev = str(it.get("evidence") or "").strip()
        if not obs or not ev:
            continue
        pm = it.get("pattern_match")
        if pm is None:
            pm = ""
        pm = str(pm)

        snapped = best_chunk_for(ev)
        if snapped:
            ev = snapped

        insights_clean.append({"observation": obs, "evidence": ev, "pattern_match": pm})

    recs_clean = []
    for r in recs_in:
        if not isinstance(r, dict):
            continue
        action = str(r.get("action") or "").strip()
        timing = str(r.get("timing") or "").strip()
        eo = str(r.get("expected_outcome") or "").strip()
        if not action or not timing or not eo:
            continue
        recs_clean.append({"action": action, "timing": timing, "expected_outcome": eo})

    out["insights"] = insights_clean
    out["recommendations"] = recs_clean

    # If strict output is empty, make it explicitly low_signal
    if not out["insights"]:
        out["confidence"] = "low_signal"  # type: ignore[assignment]
        if "flag" not in out:
            out["flag"] = "insufficient_data"

    return out


def run_pipeline(
    session: SessionInput,
    *,
    config: PipelineConfig | None = None,
    profile_store: ProfileStore | None = None,
    llm: LLMClient | None = None,
) -> ParentCopilotOutput:
    cfg = config or PipelineConfig()
    
    # Try to use GeminiLLMClient if API key is available, else fallback to Mock
    if llm:
        llm_client = llm
    else:
        try:
            llm_client = GeminiLLMClient.from_env()
        except ValueError:
            llm_client = MockLLMClient()
            
    profiles = profile_store or JsonProfileStore("samples/profiles/teens.json")
    dq_cache = DQCache()
    latest_cache = LatestOutputCache()
    diar_clf = MockDiarizationClassifier()

    t0 = time.time()
    validate_json(session, "input.session.schema.json")

    # Step 1
    s1_t0 = time.time()
    def _resolve_ambiguous(turn_text: str):
        key = f"{session['session_id']}::{turn_text.strip().lower()}"
        cached = dq_cache.get(key)
        if cached is not None:
            return cached
        pred = diar_clf.classify_turn(turn_text)
        dq_cache.set(key, pred)
        return pred

    step1 = preprocess_and_diarize(
        session["session_id"],
        session["raw_transcript"],
        resolve_ambiguous=_resolve_ambiguous if cfg.enable_hybrid_diarization else None,
        ambiguous_threshold=cfg.diarization_unknown_threshold,
    )
    s1_ms = int((time.time() - s1_t0) * 1000)

    if len(step1["turns"]) < cfg.min_turns or step1["quality_score"] < cfg.min_quality_score:
        out = _insufficient_data_output(session["session_id"])
        out["_delivery"] = render_parent_payload(out)
        out["_meta"] = {
            "prompt_version": cfg.prompt_version,
            "temperature": cfg.temperature,
            "step1": {
                "turns": len(step1["turns"]),
                "quality_score": step1["quality_score"],
                "ms": s1_ms,
                "method": step1.get("_meta", {}).get("method", "rule_based"),
                "llm_assisted_turns": step1.get("_meta", {}).get("llm_assisted_turns", 0),
                "avg_turn_confidence": step1.get("_meta", {}).get("avg_turn_confidence", 0.0),
            },
            "pipeline_ms": int((time.time() - t0) * 1000),
        }
        return out

    # Step 2
    s2_t0 = time.time()
    step2 = assemble_context(
        step1,
        teen_id=session["teen_id"],
        family_goals=session["family_goals"],
        profile_store=profiles,
    )
    s2_ms = int((time.time() - s2_t0) * 1000)

    # Step 3+4 (single call + validate, with retry)
    last_err: str | None = None
    for attempt in range(cfg.max_retries + 1):
        s3_t0 = time.time()
        output = llm_client.generate_parent_copilot(
            session_id=session["session_id"],
            prompt_version=cfg.prompt_version,
            temperature=cfg.temperature,
            context=step2,
            strict=True,
        )
        s3_ms = int((time.time() - s3_t0) * 1000)

        output = _sanitize_parent_output(output=output, session_id=session["session_id"], step2=step2)

        try:
            s4_t0 = time.time()
            v = validate_parent_output(
                output=output,
                step2=step2,
                grounding_threshold=cfg.grounding_threshold,
            )
            s4_ms = int((time.time() - s4_t0) * 1000)

            output["_meta"] = {
                "prompt_version": cfg.prompt_version,
                "temperature": cfg.temperature,
                "attempt": attempt,
                "validation": asdict(v),
                "step1": {
                    "turns": len(step1["turns"]),
                    "quality_score": step1["quality_score"],
                    "method": step1.get("_meta", {}).get("method", "rule_based"),
                    "llm_assisted_turns": step1.get("_meta", {}).get("llm_assisted_turns", 0),
                    "avg_turn_confidence": step1.get("_meta", {}).get("avg_turn_confidence", 0.0),
                },
                "timings_ms": {"step1": s1_ms, "step2": s2_ms, "llm": s3_ms, "validation": s4_ms},
                "pipeline_ms": int((time.time() - t0) * 1000),
            }
            output["_delivery"] = render_parent_payload(output)
            # cache successful output for stale_data fallback
            latest_cache.set(session["teen_id"], output)
            return output
        except HallucinationError as e:
            last_err = str(e)
            # Retry once with tighter constraints would happen here for real LLM.
            continue
        except TimeoutError as e:
            last_err = str(e)
            cached = latest_cache.get(session["teen_id"])
            if cached:
                stale = dict(cached)
                stale["session_id"] = session["session_id"]
                stale["flag"] = "stale_data"
                stale["_delivery"] = render_parent_payload(stale)
                stale["_meta"] = {
                    "error": last_err,
                    "fallback": "latest_output_cache",
                    "prompt_version": cfg.prompt_version,
                    "temperature": cfg.temperature,
                    "pipeline_ms": int((time.time() - t0) * 1000),
                }
                return stale  # type: ignore[return-value]
            break
        except Exception as e:  # schema invalid or other
            last_err = str(e)
            break

    # Fallback: block questionable outputs
    blocked = _insufficient_data_output(session["session_id"])
    blocked["flag"] = "needs_review"
    blocked["risk_reasoning"] = "validation failed"
    blocked["_delivery"] = render_parent_payload(blocked)
    blocked["_meta"] = {
        "error": last_err,
        "prompt_version": cfg.prompt_version,
        "temperature": cfg.temperature,
        "pipeline_ms": int((time.time() - t0) * 1000),
    }
    return blocked

