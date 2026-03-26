from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

from teencare_ai.core.types import ParentCopilotOutput, Step2Output


class LLMClient:
    def generate_parent_copilot(
        self,
        *,
        session_id: str,
        prompt_version: str,
        temperature: float,
        context: Step2Output,
        strict: bool,
    ) -> ParentCopilotOutput:
        raise NotImplementedError


def _join_context_for_prompt(step2: Step2Output) -> str:
    c = step2["context"]
    parts = []
    if c["layer_1_profile"]:
        parts.append("## Profile\n" + c["layer_1_profile"])
    if c["layer_2_history"]:
        parts.append("## History\n" + "\n".join(c["layer_2_history"]))
    if c["layer_3_session"]:
        parts.append("## Session\n" + "\n".join(c["layer_3_session"]))
    return "\n\n".join(parts).strip()


class MockLLMClient(LLMClient):
    """
    Deterministic MVP mock.
    Produces a small set of grounded insights by pattern matching on session lines.
    """

    def generate_parent_copilot(
        self,
        *,
        session_id: str,
        prompt_version: str,
        temperature: float,
        context: Step2Output,
        strict: bool,
    ) -> ParentCopilotOutput:
        session_lines = context["context"]["layer_3_session"]
        joined = "\n".join(session_lines).lower()

        insights = []
        recs = []

        def quote_contains(substr: str) -> str | None:
            for ln in session_lines:
                if substr.lower() in ln.lower():
                    return ln
            return None

        q1 = quote_contains("vướng") or quote_contains("lịch")
        if q1:
            insights.append(
                {
                    "observation": "Teen đang overload lịch, dễ dẫn đến cảm xúc tiêu cực.",
                    "evidence": q1,
                    "pattern_match": "",
                }
            )
            recs.append(
                {
                    "action": "Hỏi con 1 câu về lịch tuần này trước bữa tối",
                    "timing": "Tối nay",
                    "expected_outcome": "Giúp con chủ động chia sẻ áp lực lịch thay vì giữ trong lòng",
                }
            )

        q2 = quote_contains("cáu") or quote_contains("khó chịu")
        if q2:
            insights.append(
                {
                    "observation": "Teen có dấu hiệu bực bội/cáu kỉnh và có thể trút cảm xúc lên người xung quanh.",
                    "evidence": q2,
                    "pattern_match": "",
                }
            )
            recs.append(
                {
                    "action": "Thống nhất 1 câu 'dừng lại' khi con bắt đầu cáu và hẹn nói lại sau 10 phút",
                    "timing": "Cuối tuần này",
                    "expected_outcome": "Giảm xung đột và tạo thói quen tạm dừng để điều chỉnh cảm xúc",
                }
            )

        q3 = quote_contains("bình thường")
        if q3:
            insights.append(
                {
                    "observation": "Khi được hỏi, teen có xu hướng trả lời 'bình thường' thay vì chia sẻ thật.",
                    "evidence": q3,
                    "pattern_match": "",
                }
            )
            recs.append(
                {
                    "action": "Thử hỏi con theo thang điểm 0-10: 'Hôm nay con mệt mấy điểm?' rồi hỏi tiếp 1 câu",
                    "timing": "Trong 24h tới",
                    "expected_outcome": "Tăng khả năng con trả lời cụ thể thay vì phản xạ 'bình thường'",
                }
            )

        risk_level = "low"
        risk_reasoning = "Không thấy tín hiệu rủi ro cao trong đoạn trao đổi."
        if "tự tử" in joined or "tự hại" in joined:
            risk_level = "high"
            risk_reasoning = "Có đề cập tự hại/tự tử trong transcript."
        elif any(k in joined for k in ["cáu", "khó chịu", "overload", "áp lực"]):
            risk_level = "medium"
            risk_reasoning = "Có dấu hiệu căng thẳng/cảm xúc tiêu cực trong transcript."

        confidence = "high" if insights else "low_signal"
        if strict and not insights:
            return {
                "session_id": session_id,
                "insights": [],
                "risk_level": "low",
                "risk_reasoning": "insufficient signal in transcript",
                "recommendations": [],
                "confidence": "low_signal",
            }

        return {
            "session_id": session_id,
            "insights": insights,
            "risk_level": risk_level,  # type: ignore[assignment]
            "risk_reasoning": risk_reasoning,
            "recommendations": recs,
            "confidence": confidence,  # type: ignore[assignment]
            "_meta": {"prompt_version": prompt_version, "temperature": temperature, "mock": True},
        }


@dataclass(frozen=True)
class HttpLLMConfig:
    endpoint: str
    api_key: str | None = None
    timeout_s: float = 10.0


class HttpLLMClient(LLMClient):
    """
    Minimal HTTP client for a structured-output LLM gateway you control.

    Contract (request):
      { session_id, prompt_version, temperature, context_text, strict }

    Contract (response):
      JSON body must match `output.parent_copilot.schema.json`.
    """

    def __init__(self, cfg: HttpLLMConfig):
        self._cfg = cfg

    @staticmethod
    def from_env() -> "HttpLLMClient":
        endpoint = os.environ.get("TEENCARE_LLM_ENDPOINT", "").strip()
        if not endpoint:
            raise ValueError("Missing TEENCARE_LLM_ENDPOINT")
        return HttpLLMClient(
            HttpLLMConfig(
                endpoint=endpoint,
                api_key=os.environ.get("TEENCARE_LLM_API_KEY"),
                timeout_s=float(os.environ.get("TEENCARE_LLM_TIMEOUT_S", "10")),
            )
        )

    def generate_parent_copilot(
        self,
        *,
        session_id: str,
        prompt_version: str,
        temperature: float,
        context: Step2Output,
        strict: bool,
    ) -> ParentCopilotOutput:
        headers = {"Content-Type": "application/json"}
        if self._cfg.api_key:
            headers["Authorization"] = f"Bearer {self._cfg.api_key}"

        payload: dict[str, Any] = {
            "session_id": session_id,
            "prompt_version": prompt_version,
            "temperature": temperature,
            "context_text": _join_context_for_prompt(context),
            "strict": strict,
        }

        resp = requests.post(
            self._cfg.endpoint,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=self._cfg.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()


class GeminiLLMClient(LLMClient):
    """
    LLM Client using Google Gemini Flash 2.5 (Direct HTTP Call)
    Logic matched with ai-powered-development/geminiProvider.js
    """

    def __init__(self, api_key: str, model_name: str, api_version: str, temperature: float, timeout_s: float):
        self._api_key = api_key
        self._model = model_name
        self._api_version = api_version
        self._temperature = temperature
        self._timeout_s = timeout_s

    @staticmethod
    def from_env() -> "GeminiLLMClient":
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")
        
        # User specified: Always use gemini-2.5-flash
        model_name = "gemini-2.5-flash"
            
        return GeminiLLMClient(
            api_key=api_key,
            model_name=model_name,
            api_version="v1beta",
            temperature=0.2,
            timeout_s=60.0
        )

    def generate_parent_copilot(
        self,
        *,
        session_id: str,
        prompt_version: str,
        temperature: float,
        context: Step2Output,
        strict: bool,
    ) -> ParentCopilotOutput:
        context_text = _join_context_for_prompt(context)

        system_instruction = (
            "You are an expert TeenCare Parent Copilot AI. "
            "Analyze the coaching session and provide insights and recommendations for parents. "
            "LANGUAGE RULES:\n"
            "0. You MUST write all natural-language fields in Vietnamese only (observation, evidence explanation, risk_reasoning, action, timing, expected_outcome, flag explanation). Do not output English sentences.\n"
            "SAFETY RULES:\n"
            "1. Every insight MUST have an 'evidence' field which is a VERBATIM DIRECT QUOTE from the '## Session' section below.\n"
            "2. Do not modify the quote (keep punctuation, capitalization, and spelling exactly as in the source).\n"
            "3. If you cannot find a direct quote to support an observation, do not include that insight.\n"
            "4. If there is not enough meaningful conversation to provide high-quality insights, return empty insights list and set flag to 'insufficient_data'.\n"
            "5. Output MUST be a valid JSON matching the schema."
        )

        # Senior Fix: Align with geminiProvider.js logic - merging instruction into prompt
        prompt = f"[INSTRUCTION]\n{system_instruction}\n\n"
        prompt += (
            f"Session ID: {session_id}\n"
            f"Prompt Version: {prompt_version}\n"
            f"Context:\n{context_text}\n\n"
            "Return a JSON object with keys: session_id, insights, risk_level, risk_reasoning, recommendations, confidence, flag.\n"
            "Reminder: all explanatory text fields must be Vietnamese only."
        )

        body = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        url = f"https://generativelanguage.googleapis.com/{self._api_version}/models/{self._model}:generateContent"

        try:
            resp = requests.post(
                url,
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                timeout=self._timeout_s
            )
            resp.raise_for_status()
            
            data = resp.json()
            
            # Extract text using safe extraction logic similar to user's optional chaining
            text = "No response"
            candidates = data.get("candidates")
            if candidates and len(candidates) > 0:
                content = candidates[0].get("content")
                if content:
                    parts = content.get("parts")
                    if parts and len(parts) > 0:
                        text = parts[0].get("text") or "No response"

            if text == "No response":
                raise ValueError(f"Gemini returned empty or invalid response: {json.dumps(data)}")

            # Clean markdown if present
            cleaned_text = text.strip()
            if cleaned_text.startswith("```"):
                # Extract content between first ```json or ``` and last ```
                lines = cleaned_text.splitlines()
                if len(lines) >= 2:
                    # Skip first line if it starts with ```
                    start_idx = 1 if lines[0].startswith("```") else 0
                    # Skip last line if it ends with ```
                    end_idx = -1 if lines[-1].strip() == "```" else None
                    cleaned_text = "\n".join(lines[start_idx:end_idx]).strip()

            output: ParentCopilotOutput = json.loads(cleaned_text)
            # Basic validation of required fields
            required = ["session_id", "insights", "risk_level", "risk_reasoning", "recommendations", "confidence"]
            for field in required:
                if field not in output:
                    output[field] = "" if field != "insights" and field != "recommendations" else [] # type: ignore
            return output

        except Exception as e:
            error_msg = str(e)
            flag = "llm_error"
            if "429" in error_msg or "quota" in error_msg.lower():
                flag = "rate_limit_exceeded"
                error_msg = "Gemini API Quota Exceeded. Please check your plan or try again later."
            elif "404" in error_msg:
                error_msg = f"Model '{self._model}' not found in version '{self._api_version}'. Please check your config."
            
            return {
                "session_id": session_id,
                "insights": [],
                "risk_level": "low",
                "risk_reasoning": f"LLM Error: {error_msg}",
                "recommendations": [],
                "confidence": "low_signal",
                "flag": flag,
            }

