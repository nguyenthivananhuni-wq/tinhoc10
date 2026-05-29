"""Offline batch calibration of IRT item difficulty `Question.difficulty_b`.

Derives difficulty from observed Attempt accuracy per question. Under the Rasch
model, with average ability assumed ≈ 0, the proportion correct p relates to
difficulty by p = sigmoid(0 - b), hence:

    b ≈ -logit(p) = -log( p / (1 - p) )

Easy items (high p) get negative b; hard items (low p) get positive b.

Questions with fewer than MIN_RESPONSES attempts are skipped (kept at their
current b) because the estimate would be too noisy.

Usage:
    python -m scripts.calibrate_difficulty            # apply changes
    python -m scripts.calibrate_difficulty --dry-run  # print, don't write
    python -m scripts.calibrate_difficulty --min 20   # require ≥20 responses
"""
from __future__ import annotations

import argparse
import math

from sqlmodel import Session, select

from app.db import engine
from app.models import Attempt, Question

MIN_RESPONSES = 10
# Clamp accuracy away from 0/1 so logit stays finite; also clamp b range.
_P_FLOOR = 0.02
_P_CEIL = 0.98
B_MIN, B_MAX = -4.0, 4.0


def difficulty_from_accuracy(accuracy: float) -> float:
    """b = -logit(p), clamped. accuracy = proportion correct."""
    p = min(_P_CEIL, max(_P_FLOOR, accuracy))
    b = -math.log(p / (1.0 - p))
    return max(B_MIN, min(B_MAX, b))


def compute_calibrations(
    session: Session, min_responses: int = MIN_RESPONSES
) -> list[dict]:
    """Return proposed b changes for questions with enough responses.

    Each item: {question_id, n, correct, accuracy, old_b, new_b}.
    """
    questions = session.exec(select(Question)).all()
    out: list[dict] = []
    for q in questions:
        attempts = session.exec(
            select(Attempt).where(Attempt.question_id == q.id)
        ).all()
        n = len(attempts)
        if n < min_responses:
            continue
        correct = sum(1 for a in attempts if a.is_correct)
        accuracy = correct / n
        out.append({
            "question_id": q.id,
            "n": n,
            "correct": correct,
            "accuracy": accuracy,
            "old_b": q.difficulty_b,
            "new_b": difficulty_from_accuracy(accuracy),
        })
    return out


def apply_calibrations(session: Session, calibrations: list[dict]) -> int:
    """Write new_b values back to Question rows. Returns count updated."""
    updated = 0
    for c in calibrations:
        q = session.get(Question, c["question_id"])
        if q is not None and q.difficulty_b != c["new_b"]:
            q.difficulty_b = c["new_b"]
            session.add(q)
            updated += 1
    session.commit()
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate IRT question difficulty.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes only.")
    parser.add_argument(
        "--min", type=int, default=MIN_RESPONSES, dest="min_responses",
        help=f"Min responses per question (default {MIN_RESPONSES}).",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        cals = compute_calibrations(session, args.min_responses)
        if not cals:
            print(f"No question has >={args.min_responses} responses yet - nothing to calibrate.")
            return

        print(f"{'q_id':>5} {'n':>4} {'acc':>6} {'old_b':>7} {'new_b':>7}")
        print("-" * 34)
        for c in cals:
            print(
                f"{c['question_id']:>5} {c['n']:>4} {c['accuracy']*100:>5.1f}% "
                f"{c['old_b']:>7.3f} {c['new_b']:>7.3f}"
            )

        if args.dry_run:
            print(f"\n[dry-run] {len(cals)} question(s) would be recalibrated.")
            return

        updated = apply_calibrations(session, cals)
        print(f"\nDone - {updated} question(s) updated.")


if __name__ == "__main__":
    main()
