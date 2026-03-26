from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LatestOutputCache:
    """
    Stores the latest successful output per teen_id for stale_data fallback.
    """

    def __init__(self, path: str | Path | None = None):
        if path is None:
            # MVP: Fallback to a relative path that works in most dev layouts
            path = "samples/runs/latest_output_by_teen.json"
        self._path = Path(path)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback for read-only filesystems or permission issues
            pass

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, teen_id: str) -> dict[str, Any] | None:
        return self._load().get(teen_id)

    def set(self, teen_id: str, payload: dict[str, Any]) -> None:
        data = self._load()
        data[teen_id] = payload
        self._save(data)

