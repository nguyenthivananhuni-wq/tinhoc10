import json
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import (
    Attempt,
    GOAL_TYPES,
    LearningGoal,
    MasteryState,
    Question,
    Topic,
    User,
)


def _make_user(session: Session, username: str = "alice") -> User:
    u = User(username=username, password_hash="hashed")
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _make_topic(session: Session, name: str = "Test", order: int = 1) -> Topic:
    t = Topic(name=name, order_in_syllabus=order)
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def _make_question(session: Session, topic_id: int, level: int = 1) -> Question:
    q = Question(
        topic_id=topic_id,
        content="2 + 2 = ?",
        difficulty_level=level,
        type="mcq",
        options_json=json.dumps(["3", "4", "5", "6"]),
        correct_answer="4",
    )
    session.add(q)
    session.commit()
    session.refresh(q)
    return q


# ---- User ----

def test_create_user_defaults(session: Session):
    u = _make_user(session)
    assert u.id is not None
    assert u.ability_theta == 0.0
    assert u.is_admin is False
    assert isinstance(u.created_at, datetime)


def test_username_unique(session: Session):
    _make_user(session, "bob")
    with pytest.raises(IntegrityError):
        dup = User(username="bob", password_hash="x")
        session.add(dup)
        session.commit()


# ---- Topic ----

def test_topic_self_ref(session: Session):
    parent = _make_topic(session, "Parent", 1)
    child = Topic(name="Child", order_in_syllabus=2, parent_id=parent.id)
    session.add(child)
    session.commit()
    session.refresh(child)
    assert child.parent_id == parent.id


def test_topic_parent_invalid_fk_rejected(session: Session):
    bad = Topic(name="Orphan", order_in_syllabus=1, parent_id=999)
    session.add(bad)
    with pytest.raises(IntegrityError):
        session.commit()


# ---- Question ----

def test_create_question_with_fk(session: Session):
    t = _make_topic(session)
    q = _make_question(session, t.id)
    assert q.id is not None
    assert q.difficulty_b == 0.0
    assert q.type == "mcq"
    assert json.loads(q.options_json) == ["3", "4", "5", "6"]


def test_question_topic_fk_invalid(session: Session):
    q = Question(
        topic_id=999,
        content="x",
        difficulty_level=1,
        options_json="[]",
        correct_answer="a",
    )
    session.add(q)
    with pytest.raises(IntegrityError):
        session.commit()


# ---- Attempt ----

def test_attempt_full_chain(session: Session):
    u = _make_user(session)
    t = _make_topic(session)
    q = _make_question(session, t.id)

    a = Attempt(
        user_id=u.id,
        question_id=q.id,
        is_correct=True,
        response_time_ms=1500,
        selected_answer="4",
        session_id="quiz-abc",
    )
    session.add(a)
    session.commit()
    session.refresh(a)
    assert a.id is not None
    assert a.is_correct is True
    assert a.session_id == "quiz-abc"


def test_attempt_invalid_user_fk(session: Session):
    t = _make_topic(session)
    q = _make_question(session, t.id)
    a = Attempt(user_id=999, question_id=q.id, is_correct=False)
    session.add(a)
    with pytest.raises(IntegrityError):
        session.commit()


def test_attempt_invalid_question_fk(session: Session):
    u = _make_user(session)
    a = Attempt(user_id=u.id, question_id=999, is_correct=False)
    session.add(a)
    with pytest.raises(IntegrityError):
        session.commit()


# ---- MasteryState ----

def test_mastery_state_default(session: Session):
    u = _make_user(session)
    t = _make_topic(session)
    m = MasteryState(user_id=u.id, topic_id=t.id)
    session.add(m)
    session.commit()
    session.refresh(m)
    assert m.p_mastery == 0.1


def test_mastery_state_composite_pk_unique(session: Session):
    u = _make_user(session)
    t = _make_topic(session)
    session.add(MasteryState(user_id=u.id, topic_id=t.id, p_mastery=0.5))
    session.commit()
    with pytest.raises(IntegrityError):
        session.add(MasteryState(user_id=u.id, topic_id=t.id, p_mastery=0.8))
        session.commit()


def test_mastery_state_per_user_per_topic(session: Session):
    u1 = _make_user(session, "u1")
    u2 = _make_user(session, "u2")
    t1 = _make_topic(session, "T1", 1)
    t2 = _make_topic(session, "T2", 2)
    for uid, tid in [(u1.id, t1.id), (u1.id, t2.id), (u2.id, t1.id), (u2.id, t2.id)]:
        session.add(MasteryState(user_id=uid, topic_id=tid))
    session.commit()
    rows = session.exec(select(MasteryState)).all()
    assert len(rows) == 4


# ---- LearningGoal ----

def test_learning_goal_valid_types(session: Session):
    u = _make_user(session)
    for gt in GOAL_TYPES:
        session.add(LearningGoal(user_id=u.id, goal_type=gt))
    session.commit()
    rows = session.exec(select(LearningGoal).where(LearningGoal.user_id == u.id)).all()
    assert len(rows) == len(GOAL_TYPES)
    assert all(g.is_active for g in rows)


def test_learning_goal_invalid_user_fk(session: Session):
    g = LearningGoal(user_id=999, goal_type="exam")
    session.add(g)
    with pytest.raises(IntegrityError):
        session.commit()


# ---- Schema integrity ----

def test_all_tables_created(test_engine):
    from sqlalchemy import inspect

    inspector = inspect(test_engine)
    expected = {"user", "topic", "question", "attempt", "mastery_state", "learning_goal"}
    actual = set(inspector.get_table_names())
    assert expected.issubset(actual), f"missing tables: {expected - actual}"


def test_fk_pragma_enabled(test_engine):
    with test_engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1
