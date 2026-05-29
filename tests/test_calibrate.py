"""Tests for the offline IRT difficulty calibration script."""
from __future__ import annotations

import json

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models import Attempt, Question, Topic, User
from app.security import hash_password
from scripts.calibrate_difficulty import (
    apply_calibrations,
    compute_calibrations,
    difficulty_from_accuracy,
)


def test_difficulty_from_accuracy_easy_is_negative():
    # High accuracy → easy item → negative b.
    assert difficulty_from_accuracy(0.9) < 0


def test_difficulty_from_accuracy_hard_is_positive():
    assert difficulty_from_accuracy(0.2) > 0


def test_difficulty_from_accuracy_half_is_zero():
    assert difficulty_from_accuracy(0.5) == pytest.approx(0.0, abs=1e-9)


def test_difficulty_clamped_for_perfect_scores():
    # 100% / 0% must stay finite (clamped), not ±inf.
    assert -4.0 <= difficulty_from_accuracy(1.0) <= 4.0
    assert -4.0 <= difficulty_from_accuracy(0.0) <= 4.0


@pytest.fixture()
def db():
    e = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(e)
    with Session(e) as s:
        s.add(Topic(id=1, name="T1", order_in_syllabus=1))
        s.add(User(id=1, username="u", password_hash=hash_password("x")))
        s.commit()
        for qid in (1, 2):
            s.add(Question(
                id=qid, topic_id=1, content=f"Q{qid}", difficulty_level=2,
                options_json=json.dumps(["A", "B", "C", "D"]),
                correct_answer="A", difficulty_b=0.0,
            ))
        s.commit()
        yield s
    e.dispose()


def _add_attempts(s: Session, qid: int, n_correct: int, n_wrong: int):
    for _ in range(n_correct):
        s.add(Attempt(user_id=1, question_id=qid, is_correct=True, session_id="s"))
    for _ in range(n_wrong):
        s.add(Attempt(user_id=1, question_id=qid, is_correct=False, session_id="s"))
    s.commit()


def test_compute_skips_low_response_questions(db):
    _add_attempts(db, qid=1, n_correct=3, n_wrong=2)  # only 5 < 10
    assert compute_calibrations(db, min_responses=10) == []


def test_compute_calibrates_with_enough_responses(db):
    _add_attempts(db, qid=1, n_correct=9, n_wrong=1)  # 90% accuracy, easy
    cals = compute_calibrations(db, min_responses=10)
    assert len(cals) == 1
    c = cals[0]
    assert c["question_id"] == 1
    assert c["n"] == 10
    assert c["accuracy"] == pytest.approx(0.9)
    assert c["new_b"] < 0  # easy → negative difficulty


def test_apply_calibrations_persists(db):
    _add_attempts(db, qid=1, n_correct=2, n_wrong=8)  # 20% accuracy, hard
    cals = compute_calibrations(db, min_responses=10)
    updated = apply_calibrations(db, cals)
    assert updated == 1
    q = db.get(Question, 1)
    assert q.difficulty_b > 0  # hard → positive b persisted


def test_apply_idempotent_no_change(db):
    _add_attempts(db, qid=1, n_correct=5, n_wrong=5)
    cals = compute_calibrations(db, min_responses=10)
    apply_calibrations(db, cals)
    # Re-applying same calibration → nothing changes.
    cals2 = compute_calibrations(db, min_responses=10)
    assert apply_calibrations(db, cals2) == 0
