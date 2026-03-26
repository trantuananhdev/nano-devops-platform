from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Event:
    name: str
    session_id: str
    ts_ms: int
    data: dict[str, Any]


class EventSink:
    def emit(self, e: Event) -> None:
        raise NotImplementedError


class JsonlFileSink(EventSink):
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, e: Event) -> None:
        line = json.dumps(
            {"name": e.name, "session_id": e.session_id, "ts_ms": e.ts_ms, "data": e.data},
            ensure_ascii=False,
        )
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def now_ms() -> int:
    return int(time.time() * 1000)

