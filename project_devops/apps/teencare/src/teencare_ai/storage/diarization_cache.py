from __future__ import annotations

import json
from pathlib import Path

from teencare_ai.core.types import Speaker


class DQCache:
    """
    Tiny JSON cache for ambiguous-turn speaker decisions by session.
    Key: session_id + normalized text.
    """

    def __init__(self, path: str | Path = "samples/runs/diarization_cache.json"):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Speaker]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Speaker]) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> Speaker | None:
        return self._load().get(key)

    def set(self, key: str, speaker: Speaker) -> None:
        data = self._load()
        data[key] = speaker
        self._save(data)

