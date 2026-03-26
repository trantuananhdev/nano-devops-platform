from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TeenProfile:
    teen_id: str
    profile_summary: str


class ProfileStore:
    def get_profile(self, teen_id: str) -> TeenProfile | None:
        raise NotImplementedError


class JsonProfileStore(ProfileStore):
    """
    Loads teen profiles from a simple JSON file.

    Expected format:
    {
      "<teen_id>": { "profile_summary": "..." },
      ...
    }
    """

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def get_profile(self, teen_id: str) -> TeenProfile | None:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        item = data.get(teen_id)
        if not item:
            return None
        summary = (item.get("profile_summary") or "").strip()
        if not summary:
            return None
        return TeenProfile(teen_id=teen_id, profile_summary=summary)

