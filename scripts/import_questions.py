"""Import question bank JSON files into Question table.

Usage:
    python -m scripts.import_questions             # import từ data/questions/
    python -m scripts.import_questions --dry-run   # validate only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, select

from app.db import engine
from app.models import Question, Topic

REQUIRED_FIELDS = {"topic_id", "content", "difficulty_level", "options", "correct_answer"}
QUESTIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "questions"


class ValidationError(Exception):
    pass


def validate_question(q: dict, file_label: str, idx: int) -> None:
    missing = REQUIRED_FIELDS - q.keys()
    if missing:
        raise ValidationError(f"{file_label}[{idx}]: missing fields {missing}")
    if not isinstance(q["content"], str) or not q["content"].strip():
        raise ValidationError(f"{file_label}[{idx}]: content must be non-empty string")
    if q["difficulty_level"] not in (1, 2, 3):
        raise ValidationError(
            f"{file_label}[{idx}]: difficulty_level must be 1, 2 or 3, got {q['difficulty_level']}"
        )
    options = q["options"]
    if not isinstance(options, list) or len(options) != 4:
        raise ValidationError(
            f"{file_label}[{idx}]: options must be a list of exactly 4 items"
        )
    if len(set(options)) != 4:
        raise ValidationError(f"{file_label}[{idx}]: options must be unique")
    if q["correct_answer"] not in options:
        raise ValidationError(
            f"{file_label}[{idx}]: correct_answer '{q['correct_answer']}' not in options"
        )


def load_and_validate(files: Iterable[Path]) -> list[dict]:
    all_q: list[dict] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValidationError(f"{f.name}: invalid JSON — {e}") from e
        if not isinstance(data, list):
            raise ValidationError(f"{f.name}: root must be JSON array")
        for idx, q in enumerate(data):
            validate_question(q, f.name, idx)
            all_q.append(q)
    return all_q


def import_questions(questions: list[dict], session: Session) -> tuple[int, int]:
    """Returns (inserted, skipped_existing). Idempotent: skips if table already has rows."""
    topic_ids = {t.id for t in session.exec(select(Topic)).all()}

    existing = session.exec(select(Question)).first()
    if existing is not None:
        return (0, len(questions))

    inserted = 0
    for q in questions:
        if q["topic_id"] not in topic_ids:
            raise ValidationError(
                f"topic_id {q['topic_id']} không tồn tại (chạy seed_topics trước)"
            )
        session.add(
            Question(
                topic_id=q["topic_id"],
                content=q["content"],
                difficulty_level=q["difficulty_level"],
                type=q.get("type", "mcq"),
                difficulty_b=float(q.get("difficulty_b", 0.0)),
                options_json=json.dumps(q["options"], ensure_ascii=False),
                correct_answer=q["correct_answer"],
                source_page=q.get("source_page"),
            )
        )
        inserted += 1
    session.commit()
    return (inserted, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=QUESTIONS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = sorted(args.dir.glob("topic-*.json"))
    if not files:
        print(f"[import] no topic-*.json found in {args.dir}", file=sys.stderr)
        return 1

    print(f"[import] found {len(files)} files in {args.dir}")
    try:
        questions = load_and_validate(files)
    except ValidationError as e:
        print(f"[import] VALIDATION FAILED: {e}", file=sys.stderr)
        return 2

    print(f"[import] {len(questions)} questions validated OK")
    if args.dry_run:
        print("[import] dry-run mode → not writing to DB")
        return 0

    with Session(engine) as session:
        inserted, skipped = import_questions(questions, session)
        if skipped:
            print(f"[import] DB already has questions — skipped {skipped} (idempotent)")
        else:
            print(f"[import] inserted {inserted} questions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
