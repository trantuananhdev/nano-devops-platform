from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

def text_to_session_input(file_path: str, teen_id: str, family_goals: list[str]) -> dict:
    """
    Reads a raw text file and converts it into the standard session input JSON format.
    """
    transcript = Path(file_path).read_text(encoding="utf-8")
    session_id = f"session_{uuid4().hex[:8]}"
    
    return {
        "session_id": session_id,
        "teen_id": teen_id,
        "raw_transcript": transcript,
        "session_date": datetime.utcnow().isoformat(),
        "family_goals": family_goals,
    }

def main():
    """Example usage"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m teencare_ai.ingest.text_importer <file_path> <teen_id> [goal1,goal2,...]")
        return
    
    file_path = sys.argv[1]
    teen_id = sys.argv[2]
    goals = sys.argv[3].split(',') if len(sys.argv) > 3 else []
    
    session_json = text_to_session_input(file_path, teen_id, goals)
    print(json.dumps(session_json, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
