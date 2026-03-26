from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> int:
    runs = Path("samples/runs")
    files = sorted(runs.glob("*.json"))
    if not files:
        print("No runs found in samples/runs/*.json")
        print("Tip: python -m teencare_ai --input samples/raw/session_demo_002.json --output samples/runs/demo_002.json")
        return 1

    flags = Counter()
    risk = Counter()
    conf = Counter()
    schema_ok = 0
    n = 0
    invalid_files: list[str] = []

    for fp in files:
        obj = json.loads(fp.read_text(encoding="utf-8"))
        n += 1
        required = {"session_id", "insights", "risk_level", "risk_reasoning", "recommendations", "confidence"}
        if not required.issubset(set(obj.keys())):
            invalid_files.append(fp.name)
            continue
        flags[obj.get("flag", "")] += 1
        risk[obj.get("risk_level", "")] += 1
        conf[obj.get("confidence", "")] += 1
        meta = obj.get("_meta", {})
        v = meta.get("validation", {})
        if v.get("schema_valid") is True or obj.get("flag") in {"insufficient_data", "stale_data", "needs_review"}:
            schema_ok += 1

    print(f"runs: {n}")
    print(f"schema_valid: {schema_ok}/{n}")
    print(f"risk_level: {dict(risk)}")
    print(f"confidence: {dict(conf)}")
    print(f"flags: {dict(flags)}")
    if invalid_files:
        print(f"invalid_files_skipped: {invalid_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

