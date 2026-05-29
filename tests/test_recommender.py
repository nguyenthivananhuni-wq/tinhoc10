"""Tests for the recommendation engine: goal-based topic ranking + IRT item pick."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.ml.recommender import (
    DEFAULT_MASTERY,
    recommend_topic,
    recommend_topics,
    select_question,
)
from app.models import Attempt, Question, Topic, User
from app.security import hash_password


def _topics():
    return [
        Topic(id=1, name="T1", order_in_syllabus=1),
        Topic(id=2, name="T2", order_in_syllabus=2),
        Topic(id=3, name="T3", order_in_syllabus=3),
        Topic(id=4, name="T4", order_in_syllabus=4),
    ]


# ---- recommend_topics: goal branches ----

def test_exam_prioritizes_lowest_mastery():
    topics = _topics()
    mastery = {1: 0.9, 2: 0.2, 3: 0.6, 4: 0.5}
    recs = recommend_topics(topics, mastery, "exam", n=3)
    assert [r["topic"].id for r in recs] == [2, 4, 3]  # ascending mastery


def test_improve_only_below_threshold():
    topics = _topics()
    mastery = {1: 0.9, 2: 0.3, 3: 0.45, 4: 0.8}
    recs = recommend_topics(topics, mastery, "improve", n=3)
    ids = [r["topic"].id for r in recs]
    assert ids == [2, 3]  # only mastery < 0.5, ascending


def test_improve_fallback_when_all_strong():
    topics = _topics()
    mastery = {1: 0.9, 2: 0.85, 3: 0.7, 4: 0.95}
    recs = recommend_topics(topics, mastery, "improve", n=3)
    assert len(recs) == 1
    assert recs[0]["topic"].id == 3  # lowest among strong


def test_challenge_only_mastered_topics():
    topics = _topics()
    mastery = {1: 0.85, 2: 0.4, 3: 0.9, 4: 0.5}
    recs = recommend_topics(topics, mastery, "challenge", n=3)
    ids = [r["topic"].id for r in recs]
    assert ids == [3, 1]  # >= 0.8, descending


def test_challenge_fallback_when_none_strong():
    topics = _topics()
    mastery = {1: 0.5, 2: 0.4, 3: 0.6, 4: 0.3}
    recs = recommend_topics(topics, mastery, "challenge", n=3)
    assert len(recs) == 1
    assert recs[0]["topic"].id == 3  # strongest available


def test_new_topic_requires_prerequisite_met():
    topics = _topics()
    # T1 mastered (0.8 ≥ 0.7), T2 not yet → recommend T2 as the "new" topic.
    mastery = {1: 0.8, 2: 0.2, 3: 0.1, 4: 0.1}
    recs = recommend_topics(topics, mastery, "new_topic", n=3)
    assert recs[0]["topic"].id == 2
    assert "T1" in recs[0]["reason"]  # explain mentions prerequisite


def test_new_topic_first_topic_when_nothing_learned():
    topics = _topics()
    mastery = {}  # brand new user, all default
    recs = recommend_topics(topics, mastery, "new_topic", n=3)
    assert recs[0]["topic"].id == 1  # syllabus opener


def test_unknown_goal_defaults_to_exam_behavior():
    topics = _topics()
    mastery = {1: 0.9, 2: 0.2, 3: 0.6, 4: 0.5}
    recs = recommend_topics(topics, mastery, "???", n=1)
    assert recs[0]["topic"].id == 2


def test_recommend_topics_uses_default_mastery_for_missing():
    topics = _topics()
    recs = recommend_topics(topics, {}, "exam", n=4)
    for r in recs:
        assert r["p_mastery"] == DEFAULT_MASTERY


def test_recommend_empty_topics():
    assert recommend_topics([], {}, "exam") == []
    assert recommend_topic([], {}, "exam") is None


def test_recommend_topic_returns_single_best():
    topics = _topics()
    mastery = {1: 0.9, 2: 0.2, 3: 0.6, 4: 0.5}
    best = recommend_topic(topics, mastery, "exam")
    assert best.id == 2


# ---- select_question: IRT adaptive ----

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
        # questions with varied difficulty_b
        for qid, b in [(1, -2.0), (2, -0.5), (3, 0.3), (4, 1.0), (5, 2.5)]:
            s.add(Question(
                id=qid, topic_id=1, content=f"Q{qid}", difficulty_level=2,
                options_json=json.dumps(["A", "B", "C", "D"]),
                correct_answer="A", difficulty_b=b,
            ))
        s.commit()
        yield s
    e.dispose()


def test_select_question_closest_to_theta(db):
    q = select_question(db, topic_id=1, theta=0.4)
    assert q.id == 3  # b=0.3 is closest to theta=0.4


def test_select_question_high_theta_picks_hard(db):
    q = select_question(db, topic_id=1, theta=2.4)
    assert q.id == 5  # b=2.5 closest


def test_select_question_low_theta_picks_easy(db):
    q = select_question(db, topic_id=1, theta=-3.0)
    assert q.id == 1  # b=-2.0 closest


def test_select_question_excludes_session_qids(db):
    q = select_question(db, topic_id=1, theta=0.4, exclude_qids={3})
    assert q.id in (2, 4)  # 3 excluded, next closest to 0.4


def test_select_question_excludes_recent_attempts(db):
    # Mark q3 attempted just now → should be skipped for user 1.
    db.add(Attempt(user_id=1, question_id=3, is_correct=True, attempted_at=datetime.utcnow()))
    db.commit()
    q = select_question(db, topic_id=1, theta=0.4, user_id=1)
    assert q.id != 3


def test_select_question_old_attempts_not_excluded(db):
    # Attempt older than 24h should NOT exclude the question.
    old = datetime.utcnow() - timedelta(hours=48)
    db.add(Attempt(user_id=1, question_id=3, is_correct=True, attempted_at=old))
    db.commit()
    q = select_question(db, topic_id=1, theta=0.4, user_id=1)
    assert q.id == 3  # still the closest, old attempt ignored


def test_select_question_fallback_when_all_excluded(db):
    # Exclude everything → relax filter still returns a question (not None).
    q = select_question(db, topic_id=1, theta=0.0, exclude_qids={1, 2, 3, 4, 5})
    assert q is not None


def test_select_question_empty_topic_returns_none(db):
    assert select_question(db, topic_id=999, theta=0.0) is None
