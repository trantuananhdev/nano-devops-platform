"""T-21: Auto-execute chained tools after a parent tool completes."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Dossier
from app.services.orchestrator.helpers import normalize_tool_input
from app.services.tools.base import get_tool_by_name

logger = logging.getLogger(__name__)


def build_chained_input(
    dossier: Dossier,
    parent_tool: str,
    parent_output: dict[str, Any],
    output_mapping: dict[str, Any],
    *,
    parent_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map parent tool output fields into the chained tool's input dict."""
    chained_input = normalize_tool_input(dossier, None)
    for out_field, in_field in output_mapping.items():
        if out_field in parent_output:
            chained_input[in_field] = parent_output[out_field]
    chained_input["chained_from"] = parent_tool
    if parent_input is not None:
        chained_input["chain_parent_input"] = parent_input
    chained_input["chain_mapping"] = output_mapping
    return chained_input


async def resolve_chain_targets(tool_name: str) -> tuple[list[str], dict[str, Any]]:
    """Load chains_to and output_mapping from tool_configs (empty if unset)."""
    tool_config = await get_tool_by_name(tool_name)
    if not tool_config:
        return [], {}
    chains_to = tool_config.chains_to or []
    if isinstance(chains_to, dict):
        targets = list(chains_to.keys())
    else:
        targets = [t for t in chains_to if isinstance(t, str)]
    return targets, dict(tool_config.output_mapping or {})


async def get_chained_steps(
    parent_tool: str,
    parent_output: dict[str, Any],
    dossier: Dossier,
    *,
    parent_input: dict[str, Any] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Return (tool_name, tool_input) pairs to execute after parent_tool.

    Skips targets when required mapped fields are absent from parent output.
    """
    targets, output_mapping = await resolve_chain_targets(parent_tool)
    if not targets:
        return []

    steps: list[tuple[str, dict[str, Any]]] = []
    for target in targets:
        if output_mapping and not any(k in parent_output for k in output_mapping):
            logger.debug(
                "Skipping chain %s → %s: no mapped fields in output",
                parent_tool,
                target,
            )
            continue
        tool_input = build_chained_input(
            dossier,
            parent_tool,
            parent_output,
            output_mapping,
            parent_input=parent_input,
        )
        steps.append((target, tool_input))
    return steps
