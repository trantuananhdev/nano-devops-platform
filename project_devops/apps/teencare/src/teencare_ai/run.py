from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from teencare_ai.core.pipeline import run_pipeline
from teencare_ai.core.types import PipelineConfig
from teencare_ai.ingest.text_importer import text_to_session_input


def main() -> int:
    # Windows consoles may default to cp1252; force UTF-8 for Vietnamese output.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="TeenCare Parent Copilot MVP runner")
    ap.add_argument(
        "--input",
        default="",
        help="Path to session input (.json or .txt). Use --demo if you don't want to provide a file.",
    )
    ap.add_argument(
        "--demo",
        default="",
        choices=["session_demo_001", "session_demo_002", "session_real_001", "session_sample_003"],
        help="Run with built-in sample data (ignores --input).",
    )
    ap.add_argument("--teen-id", default="teen_demo_001", help="Teen id (required for .txt ingest)")
    ap.add_argument(
        "--family-goals",
        default="cải thiện kỷ luật,giảm screen time",
        help="Comma-separated family goals (used for .txt ingest)",
    )
    ap.add_argument(
        "--session-date",
        default="",
        help="Optional ISO8601 session_date override (used for .txt ingest)",
    )
    ap.add_argument("--output", default="", help="Optional output path for JSON")
    ap.add_argument("--grounding-threshold", type=float, default=0.75)
    ap.add_argument("--min-turns", type=int, default=10)
    ap.add_argument("--min-quality", type=float, default=0.5)
    args = ap.parse_args()

    if not args.demo and not args.input:
        raise SystemExit("Please provide --input or choose --demo.")

    if args.demo:
        demo_path = Path("samples/raw") / f"{args.demo}.json"
        session = json.loads(demo_path.read_text(encoding="utf-8"))
    else:
        p = Path(args.input)
        if p.suffix.lower() == ".txt":
            goals = [g.strip() for g in str(args.family_goals).split(",") if g.strip()]
            session = text_to_session_input(str(p), teen_id=str(args.teen_id), family_goals=goals)
            if args.session_date:
                session["session_date"] = str(args.session_date)
        else:
            session = json.loads(p.read_text(encoding="utf-8"))

    cfg = PipelineConfig(
        grounding_threshold=args.grounding_threshold,
        min_turns=args.min_turns,
        min_quality_score=args.min_quality,
    )
    out = run_pipeline(session, config=cfg)
    text = json.dumps(out, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

