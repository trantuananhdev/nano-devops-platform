from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


Speaker = Literal["TEEN", "MENTOR", "PARENT", "UNKNOWN"]
RiskLevel = Literal["low", "medium", "high"]
Confidence = Literal["high", "medium", "low_signal"]


class SessionInput(TypedDict):
    session_id: str
    teen_id: str
    raw_transcript: str
    session_date: str
    family_goals: list[str]


class Turn(TypedDict):
    speaker: Speaker
    text: str
    index: int


class Step1Output(TypedDict):
    session_id: str
    turns: list[Turn]
    quality_score: float


class ContextLayers(TypedDict):
    layer_1_profile: str
    layer_2_history: list[str]
    layer_3_session: list[str]


class Step2Output(TypedDict):
    session_id: str
    context: ContextLayers
    token_budget: dict[str, int]


class Insight(TypedDict):
    observation: str
    evidence: str
    pattern_match: str


class Recommendation(TypedDict):
    action: str
    timing: str
    expected_outcome: str


class ParentCopilotOutput(TypedDict, total=False):
    session_id: str
    insights: list[Insight]
    risk_level: RiskLevel
    risk_reasoning: str
    recommendations: list[Recommendation]
    confidence: Confidence
    flag: str
    _meta: dict[str, Any]


@dataclass(frozen=True)
class PipelineConfig:
    prompt_version: str = "v0.1"
    temperature: float = 0.0
    min_turns: int = 10
    min_quality_score: float = 0.5
    grounding_threshold: float = 0.75
    max_retries: int = 1
    enable_hybrid_diarization: bool = True
    diarization_unknown_threshold: float = 0.5

