"""End-to-end route tests using FastAPI TestClient against in-memory SQLite.

Covers: register/login/logout, goal flow, full 10-question quiz session,
quiz result, history page, FK persistence via Attempt.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.models import Attempt, LearningGoal, Question, Topic, User
from app.security import hash_password


@pytest.fixture()
def test_engine_in_mem():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def seeded(test_engine_in_mem):
    with Session(test_engine_in_mem) as s:
        for i in range(1, 5):
            s.add(Topic(id=i, name=f"Topic {i}", order_in_syllabus=i, description=f"d{i}"))
        s.commit()
        # 12 questions per topic so we have enough for a 10-question quiz
        for tid in range(1, 5):
            for level in (1, 2, 3):
                for k in range(4):
                    correct = f"opt{k}_correct"
                    s.add(Question(
                        topic_id=tid,
                        content=f"T{tid}L{level} câu {k}?",
                        difficulty_level=level,
                        type="mcq",
                        options_json=json.dumps([correct, "wrong1", "wrong2", "wrong3"]),
                        correct_answer=correct,
                    ))
        s.commit()
    return test_engine_in_mem


@pytest.fixture()
def client(seeded):
    def _override():
        with Session(seeded) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, username: str = "alice", password: str = "secret123"):
    r = client.post(
        "/register",
        data={"username": username, "password": password, "password2": password},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    r = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


# ---- Pages ----

def test_landing_anonymous(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "Tin 10" in r.text or "Tin học 10" in r.text


def test_topics_requires_auth(client: TestClient):
    r = client.get("/topics", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


# ---- Register ----

def test_register_then_login(client: TestClient):
    r = client.post(
        "/register",
        data={"username": "bob", "password": "secret123", "password2": "secret123"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"].startswith("/login")


def test_register_username_taken(client: TestClient, seeded):
    with Session(seeded) as s:
        s.add(User(username="taken", password_hash=hash_password("x")))
        s.commit()
    r = client.post(
        "/register",
        data={"username": "taken", "password": "secret123", "password2": "secret123"},
    )
    assert r.status_code == 400
    assert "tồn tại" in r.text.lower()


def test_register_password_mismatch(client: TestClient):
    r = client.post(
        "/register",
        data={"username": "carol", "password": "secret123", "password2": "different1"},
    )
    assert r.status_code == 400
    assert "không khớp" in r.text


def test_register_short_password(client: TestClient):
    r = client.post(
        "/register",
        data={"username": "carol", "password": "12345", "password2": "12345"},
    )
    assert r.status_code == 400
    assert "tối thiểu" in r.text.lower()


def test_register_invalid_username(client: TestClient):
    r = client.post(
        "/register",
        data={"username": "a b!", "password": "secret123", "password2": "secret123"},
    )
    assert r.status_code == 400


# ---- Login / Logout ----

def test_login_wrong_password(client: TestClient, seeded):
    with Session(seeded) as s:
        s.add(User(username="dave", password_hash=hash_password("rightpass")))
        s.commit()
    r = client.post("/login", data={"username": "dave", "password": "wrong"})
    assert r.status_code == 400
    assert "sai" in r.text.lower()


def test_login_sets_cookie(client: TestClient):
    _register_and_login(client, "eve")
    assert "tin10_session" in client.cookies


def test_logout_clears_cookie(client: TestClient):
    _register_and_login(client, "frank")
    r = client.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    # After logout, /topics should redirect to /login
    r = client.get("/topics", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_authenticated_topics(client: TestClient):
    _register_and_login(client, "gina")
    r = client.get("/topics")
    assert r.status_code == 200
    assert "Topic 1" in r.text


# ---- Goal ----

def test_goal_flow(client: TestClient, seeded):
    _register_and_login(client, "hank")
    r = client.get("/goal")
    assert r.status_code == 200
    r = client.post("/goal", data={"goal_type": "exam"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/topics"

    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "hank")).one()
        goals = s.exec(select(LearningGoal).where(LearningGoal.user_id == user.id)).all()
        active = [g for g in goals if g.is_active]
        assert len(active) == 1
        assert active[0].goal_type == "exam"


def test_goal_replaces_old(client: TestClient, seeded):
    _register_and_login(client, "iris")
    client.post("/goal", data={"goal_type": "exam"})
    client.post("/goal", data={"goal_type": "challenge"})

    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "iris")).one()
        actives = s.exec(
            select(LearningGoal).where(
                LearningGoal.user_id == user.id, LearningGoal.is_active == True  # noqa: E712
            )
        ).all()
        assert len(actives) == 1
        assert actives[0].goal_type == "challenge"


def test_goal_invalid_type(client: TestClient):
    _register_and_login(client, "jane")
    r = client.post("/goal", data={"goal_type": "garbage"})
    assert r.status_code == 400


# ---- Quiz flow ----

def test_start_quiz_renders_question(client: TestClient):
    _register_and_login(client, "kara")
    r = client.get("/quiz/1")
    assert r.status_code == 200
    assert "Câu 1 / 10" in r.text
    # Hidden inputs present
    assert 'name="session_id"' in r.text
    assert 'name="question_id"' in r.text


def test_full_quiz_session_creates_10_attempts(client: TestClient, seeded):
    _register_and_login(client, "leo")

    # Start quiz
    r = client.get("/quiz/2")
    assert r.status_code == 200
    # Extract session_id and first question id
    import re as _re
    session_id = _re.search(r'name="session_id" value="([^"]+)"', r.text).group(1)
    qid = int(_re.search(r'name="question_id" value="(\d+)"', r.text).group(1))

    # Answer 10 questions
    for i in range(10):
        # Get current question's correct answer
        with Session(seeded) as s:
            q = s.get(Question, qid)
            correct = q.correct_answer
        # Submit answer (alternate correct/wrong to make accuracy != 100%)
        selected = correct if i % 2 == 0 else "wrong1"
        r = client.post(
            "/quiz/answer",
            data={
                "session_id": session_id,
                "question_id": str(qid),
                "selected_answer": selected,
                "response_time_ms": "3000",
            },
        )
        assert r.status_code == 200, f"answer {i} failed: {r.text[:300]}"
        # Feedback partial should show "Đáp án đúng"
        assert ("Đáp án đúng" in r.text) or ("Chính xác" in r.text)

        if i == 9:
            # Last: should be flagged as is_last
            assert "Xem kết quả" in r.text
        else:
            # Not last: should have Next button
            assert "Câu tiếp theo" in r.text
            # Fetch next via /quiz/{topic}/next
            r2 = client.get(f"/quiz/2/next?session_id={session_id}")
            assert r2.status_code == 200
            qid_match = _re.search(r'name="question_id" value="(\d+)"', r2.text)
            assert qid_match, "next question card missing question_id"
            qid = int(qid_match.group(1))

    # Verify 10 Attempts persisted
    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "leo")).one()
        attempts = s.exec(
            select(Attempt).where(Attempt.session_id == session_id)
        ).all()
        assert len(attempts) == 10
        assert all(a.user_id == user.id for a in attempts)
        # 5 correct (every other one)
        assert sum(a.is_correct for a in attempts) == 5
        # response_time_ms persisted
        assert all(a.response_time_ms == 3000 for a in attempts)


def test_next_after_quiz_complete_redirects_via_htmx(client: TestClient, seeded):
    _register_and_login(client, "mona")

    # Manually insert 10 attempts with same session_id
    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "mona")).one()
        qs = s.exec(select(Question).where(Question.topic_id == 1).limit(10)).all()
        sid = "session-mona-abc"
        for q in qs:
            s.add(Attempt(
                user_id=user.id,
                question_id=q.id,
                is_correct=True,
                session_id=sid,
            ))
        s.commit()

    r = client.get(f"/quiz/1/next?session_id={sid}")
    assert r.status_code == 200
    assert r.headers.get("HX-Redirect") == f"/quiz/result/{sid}"


def test_quiz_result_renders(client: TestClient, seeded):
    _register_and_login(client, "nick")

    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "nick")).one()
        qs = s.exec(select(Question).where(Question.topic_id == 3).limit(5)).all()
        sid = "session-nick-xyz"
        for i, q in enumerate(qs):
            s.add(Attempt(
                user_id=user.id,
                question_id=q.id,
                is_correct=(i % 2 == 0),
                selected_answer=q.correct_answer if i % 2 == 0 else "wrong",
                session_id=sid,
            ))
        s.commit()

    r = client.get(f"/quiz/result/{sid}")
    assert r.status_code == 200
    assert "3/5" in r.text or "3 / 5" in r.text or "3/5" in r.text
    assert "Topic 3" in r.text


def test_quiz_result_nonexistent_404(client: TestClient):
    _register_and_login(client, "oscar")
    r = client.get("/quiz/result/does-not-exist")
    assert r.status_code == 404


def test_quiz_invalid_topic_404(client: TestClient):
    _register_and_login(client, "pat")
    r = client.get("/quiz/999")
    assert r.status_code == 404


def test_quiz_answer_wrong_question_404(client: TestClient):
    _register_and_login(client, "quinn")
    r = client.post(
        "/quiz/answer",
        data={
            "session_id": "x",
            "question_id": "99999",
            "selected_answer": "anything",
            "response_time_ms": "100",
        },
    )
    assert r.status_code == 404


# ---- History ----

def test_history_empty(client: TestClient):
    _register_and_login(client, "rosa")
    r = client.get("/history")
    assert r.status_code == 200
    assert "Tổng" in r.text
    assert "Chưa có" in r.text or ">0<" in r.text


def test_history_with_attempts(client: TestClient, seeded):
    _register_and_login(client, "sam")
    with Session(seeded) as s:
        user = s.exec(select(User).where(User.username == "sam")).one()
        q = s.exec(select(Question)).first()
        s.add(Attempt(user_id=user.id, question_id=q.id, is_correct=True, response_time_ms=2500))
        s.add(Attempt(user_id=user.id, question_id=q.id, is_correct=False, response_time_ms=4100))
        s.commit()
    r = client.get("/history")
    assert r.status_code == 200
    assert "✓" in r.text or "Đúng" in r.text
