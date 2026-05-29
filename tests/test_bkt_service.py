"""DB integration tests for BKT service + dashboard."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.ml.bkt import DEFAULT_PARAMS, update_mastery
from app.ml.bkt_service import (
    apply_bkt_for_attempt,
    get_or_create_mastery,
    mastery_vector,
)
from app.models import Attempt, MasteryState, Question, Topic, User
from app.security import hash_password


@pytest.fixture()
def engine_mem():
    e = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(e)
    yield e
    e.dispose()


@pytest.fixture()
def seeded_db(engine_mem):
    with Session(engine_mem) as s:
        # 4 topics
        for i in range(1, 5):
            s.add(Topic(id=i, name=f"Topic{i}", order_in_syllabus=i))
        s.commit()
        # 5 questions per topic
        for tid in range(1, 5):
            for k in range(5):
                s.add(Question(
                    topic_id=tid,
                    content=f"T{tid} Q{k}",
                    difficulty_level=1 + (k % 3),
                    options_json=json.dumps(["A", "B", "C", "D"]),
                    correct_answer="A",
                ))
        s.commit()
        # 1 user
        s.add(User(id=1, username="alice", password_hash=hash_password("x")))
        s.commit()
    return engine_mem


# ---- get_or_create_mastery ----

def test_get_or_create_creates_lazy(seeded_db):
    with Session(seeded_db) as s:
        m = get_or_create_mastery(user_id=1, topic_id=1, session=s)
        assert m.p_mastery == DEFAULT_PARAMS.p_l0
        # Idempotent
        m2 = get_or_create_mastery(user_id=1, topic_id=1, session=s)
        assert m2.user_id == m.user_id and m2.topic_id == m.topic_id


def test_get_or_create_preserves_existing(seeded_db):
    with Session(seeded_db) as s:
        s.add(MasteryState(user_id=1, topic_id=2, p_mastery=0.75))
        s.commit()
        m = get_or_create_mastery(user_id=1, topic_id=2, session=s)
        assert m.p_mastery == 0.75


# ---- apply_bkt_for_attempt ----

def test_apply_bkt_correct_raises_mastery(seeded_db):
    with Session(seeded_db) as s:
        q = s.exec(select(Question).where(Question.topic_id == 1)).first()
        prev, new = apply_bkt_for_attempt(
            user_id=1, question_id=q.id, is_correct=True, session=s
        )
        assert prev == DEFAULT_PARAMS.p_l0
        assert new > prev
        # Verify persisted
        m = s.get(MasteryState, (1, 1))
        assert m.p_mastery == new


def test_apply_bkt_independent_per_topic(seeded_db):
    """5 correct on topic 1 should not affect topic 2."""
    with Session(seeded_db) as s:
        topic1_qs = s.exec(select(Question).where(Question.topic_id == 1)).all()
        for q in topic1_qs:
            apply_bkt_for_attempt(1, q.id, is_correct=True, session=s)

        vec = mastery_vector(1, s)
        assert vec[1] > 0.5
        assert 2 not in vec  # topic 2 never touched


def test_apply_bkt_5_correct_streak_matches_pure_math(seeded_db):
    """End-to-end vs pure-math must match exactly (same params)."""
    expected = DEFAULT_PARAMS.p_l0
    for _ in range(5):
        expected = update_mastery(expected, is_correct=True)

    with Session(seeded_db) as s:
        topic1_qs = s.exec(select(Question).where(Question.topic_id == 1).limit(5)).all()
        for q in topic1_qs:
            apply_bkt_for_attempt(1, q.id, is_correct=True, session=s)
        m = s.get(MasteryState, (1, 1))
        assert abs(m.p_mastery - expected) < 1e-9


def test_apply_bkt_invalid_question_raises(seeded_db):
    with Session(seeded_db) as s:
        with pytest.raises(ValueError, match="Question 9999"):
            apply_bkt_for_attempt(1, 9999, True, s)


def test_mastery_vector_empty_user(seeded_db):
    with Session(seeded_db) as s:
        v = mastery_vector(user_id=999, session=s)
        assert v == {}


def test_mastery_vector_multi_topic(seeded_db):
    with Session(seeded_db) as s:
        for tid in (1, 3):
            q = s.exec(select(Question).where(Question.topic_id == tid)).first()
            apply_bkt_for_attempt(1, q.id, is_correct=True, session=s)
        v = mastery_vector(1, s)
        assert set(v.keys()) == {1, 3}
        for p in v.values():
            assert 0 <= p <= 1


# ---- E2E via TestClient: quiz attempt → mastery updates → dashboard reads ----

@pytest.fixture()
def client_with_db(seeded_db):
    def _override():
        with Session(seeded_db) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_quiz_answer_updates_mastery_e2e(client_with_db, seeded_db):
    # Register + login a NEW user (different from alice in seed)
    client_with_db.post(
        "/register",
        data={"username": "bob", "password": "secret123", "password2": "secret123"},
        follow_redirects=False,
    )
    r = client_with_db.post(
        "/login",
        data={"username": "bob", "password": "secret123"},
        follow_redirects=False,
    )
    assert r.status_code == 303

    # Find bob
    with Session(seeded_db) as s:
        bob = s.exec(select(User).where(User.username == "bob")).one()
        q = s.exec(select(Question).where(Question.topic_id == 2)).first()
        topic_id = q.topic_id

    # Submit a correct answer
    r = client_with_db.post(
        "/quiz/answer",
        data={
            "session_id": "test-bkt-session",
            "question_id": str(q.id),
            "selected_answer": "A",  # all our seed questions have correct = "A"
            "response_time_ms": "2000",
        },
    )
    assert r.status_code == 200

    # MasteryState should exist and be > P(L0)
    with Session(seeded_db) as s:
        m = s.get(MasteryState, (bob.id, topic_id))
        assert m is not None
        assert m.p_mastery > DEFAULT_PARAMS.p_l0


def test_dashboard_renders_after_attempts(client_with_db, seeded_db):
    client_with_db.post(
        "/register",
        data={"username": "carol", "password": "secret123", "password2": "secret123"},
    )
    client_with_db.post("/login", data={"username": "carol", "password": "secret123"})

    with Session(seeded_db) as s:
        carol = s.exec(select(User).where(User.username == "carol")).one()
        # Force a few attempts via direct service call
        for tid in (1, 2):
            q = s.exec(select(Question).where(Question.topic_id == tid)).first()
            apply_bkt_for_attempt(carol.id, q.id, is_correct=True, session=s)
        # add an Attempt row so dashboard stat counters > 0
        s.add(Attempt(user_id=carol.id, question_id=q.id, is_correct=True, session_id="x"))
        s.commit()

    r = client_with_db.get("/dashboard")
    assert r.status_code == 200
    assert "Mastery" in r.text or "mastery" in r.text
    assert "Topic1" in r.text and "Topic2" in r.text
    # Chart.js radar canvas present
    assert "masteryRadar" in r.text
    # Topic labels passed as JSON array
    assert '["Topic1"' in r.text or "Topic1" in r.text


def test_dashboard_requires_auth(client_with_db):
    r = client_with_db.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_dashboard_shows_zero_for_new_user(client_with_db):
    client_with_db.post(
        "/register",
        data={"username": "dora", "password": "secret123", "password2": "secret123"},
    )
    client_with_db.post("/login", data={"username": "dora", "password": "secret123"})
    r = client_with_db.get("/dashboard")
    assert r.status_code == 200
    # No attempts → 0 total, 0% accuracy
    assert "0%" in r.text or "0.0%" in r.text
