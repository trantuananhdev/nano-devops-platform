from __future__ import annotations

from dataclasses import dataclass

from teencare_ai.core.schema import validate_json
from teencare_ai.core.types import ParentCopilotOutput, Step2Output
from teencare_ai.validation.grounding import grounding_score


class HallucinationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    schema_valid: bool
    grounding_scores: list[float]
    hallucination_flag: bool


def _transcript_chunks(step2: Step2Output) -> list[str]:
    # For MVP: validate against the session lines directly.
    return step2["context"]["layer_3_session"]


def validate_parent_output(
    *,
    output: ParentCopilotOutput,
    step2: Step2Output,
    grounding_threshold: float,
) -> ValidationResult:
    validate_json(output, "output.parent_copilot.schema.json")

    chunks = _transcript_chunks(step2)
    scores: list[float] = []
    hallucinated = False

    for ins in output.get("insights", []):
        obs = ins.get("observation", "")
        ev = ins.get("evidence", "")
        score = grounding_score(observation=obs, evidence=ev, transcript_chunks=chunks)
        scores.append(float(score))
        if score < grounding_threshold:
            hallucinated = True

    if hallucinated:
        raise HallucinationError(f"Grounding below threshold {grounding_threshold}: {scores}")

    return ValidationResult(schema_valid=True, grounding_scores=scores, hallucination_flag=False)

