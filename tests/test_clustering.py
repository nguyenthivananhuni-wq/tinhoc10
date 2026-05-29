"""Tests for K-means student clustering + demo data generation + admin routes."""
from __future__ import annotations

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.ml.clustering import (
    analyze_clusters,
    build_features,
    cluster_users,
    name_clusters,
    reduce_pca_2d,
    user_cluster_name,
)
from app.models import MasteryState, Question, Topic, User
from app.security import hash_password
from scripts.generate_demo_users import DEMO_PROFILES, generate_demo_users


@pytest.fixture()
def engine_mem():
    e = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(e)
    yield e
    e.dispose()


@pytest.fixture()
def seeded(engine_mem):
    """4 topics × 9 questions (3 per difficulty level)."""
    with Session(engine_mem) as s:
        for i in range(1, 5):
            s.add(Topic(id=i, name=f"Topic{i}", order_in_syllabus=i))
        s.commit()
        for tid in range(1, 5):
            for lvl in (1, 2, 3):
                for _ in range(3):
                    s.add(Question(
                        topic_id=tid, content=f"T{tid}L{lvl}", difficulty_level=lvl,
                        options_json=json.dumps(["A", "B", "C", "D"]),
                        correct_answer="A", difficulty_b=(lvl - 2) * 1.0,
                    ))
        s.commit()
    return engine_mem


# ---- pure helpers ----

def test_name_clusters_orders_by_mastery():
    # 3 clusters, feature col 0 = avg_mastery; labels arbitrary.
    features = np.array([
        [0.2, 0, 0, 0],  # label 0 → weak
        [0.9, 0, 0, 0],  # label 1 → strong
        [0.5, 0, 0, 0],  # label 2 → middle
    ])
    labels = np.array([0, 1, 2])
    names = name_clusters(features, labels, k=3)
    assert names[0] == "Yếu"
    assert names[2] == "Trung bình"
    assert names[1] == "Giỏi"


def test_cluster_users_requires_min_samples():
    features = np.array([[0.1, 0, 0, 0], [0.5, 0, 0, 0]])  # only 2 < k=3
    with pytest.raises(ValueError, match="ít nhất 3"):
        cluster_users(features, k=3)


def test_cluster_users_labels_shape():
    features = np.array([
        [0.1, 8000, 5, 0.1],
        [0.5, 5000, 20, 0.5],
        [0.9, 2000, 40, 0.9],
        [0.85, 2500, 38, 0.8],
    ])
    labels, scaled, scaler = cluster_users(features, k=3)
    assert len(labels) == 4
    assert set(labels).issubset({0, 1, 2})
    assert scaled.shape == features.shape


def test_reduce_pca_2d_returns_two_columns():
    features = np.random.RandomState(0).rand(5, 4)
    coords = reduce_pca_2d(features)
    assert coords.shape == (5, 2)


# ---- build_features ----

def test_build_features_shape(seeded):
    with Session(seeded) as s:
        s.add(User(id=1, username="u1", password_hash=hash_password("x")))
        s.add(User(id=2, username="u2", password_hash=hash_password("x")))
        s.commit()
        ids, names, feats = build_features(s)
    assert ids == [1, 2]
    assert feats.shape == (2, 4)


def test_build_features_default_mastery_for_new_user(seeded):
    with Session(seeded) as s:
        s.add(User(id=1, username="u1", password_hash=hash_password("x")))
        s.commit()
        ids, names, feats = build_features(s)
    # avg_mastery column defaults to 0.1 when no MasteryState.
    assert feats[0, 0] == pytest.approx(0.1)


# ---- analyze_clusters ----

def test_analyze_not_enough_users(seeded):
    with Session(seeded) as s:
        s.add(User(id=1, username="u1", password_hash=hash_password("x")))
        s.commit()
        result = analyze_clusters(s, k=3)
    assert result["ok"] is False
    assert result["n_users"] == 1


def test_analyze_with_demo_users(seeded):
    with Session(seeded) as s:
        created = generate_demo_users(s)
        assert len(created) == 3
        result = analyze_clusters(s, k=3)
    assert result["ok"] is True
    assert result["n_users"] == 3
    assert len(result["points"]) == 3
    # Each point has PCA coords and a cluster name.
    for p in result["points"]:
        assert "x" in p and "y" in p and p["cluster_name"]
    # Summary sorted ascending by avg_mastery.
    masteries = [s_["avg_mastery"] for s_ in result["summary"]]
    assert masteries == sorted(masteries)


def test_demo_users_separable_by_mastery(seeded):
    """carol_strong should end with higher mastery than alice_weak."""
    with Session(seeded) as s:
        generate_demo_users(s)
        alice = s.exec(select(User).where(User.username == "alice_weak")).one()
        carol = s.exec(select(User).where(User.username == "carol_strong")).one()
        a_m = np.mean(s.exec(
            select(MasteryState.p_mastery).where(MasteryState.user_id == alice.id)
        ).all())
        c_m = np.mean(s.exec(
            select(MasteryState.p_mastery).where(MasteryState.user_id == carol.id)
        ).all())
    assert c_m > a_m


def test_demo_users_idempotent(seeded):
    with Session(seeded) as s:
        first = generate_demo_users(s)
        second = generate_demo_users(s)
    assert len(first) == 3
    assert second == []  # already exist → nothing created


def test_demo_users_force_recreates_with_existing_data(seeded):
    """--force must delete child rows (Attempt/Mastery/Goal) first, no FK error."""
    from app.models import Attempt, MasteryState
    with Session(seeded) as s:
        generate_demo_users(s)  # creates users + attempts + mastery
        before_users = len(s.exec(select(User)).all())
        # Re-run with force — previously crashed on FK constraint.
        recreated = generate_demo_users(s, force=True)
        assert sorted(recreated) == ["alice_weak", "bob_avg", "carol_strong"]
        # No duplicate users, no orphaned rows.
        assert len(s.exec(select(User)).all()) == before_users
        # Mastery/attempts belong only to current users.
        user_ids = {u.id for u in s.exec(select(User)).all()}
        for m in s.exec(select(MasteryState)).all():
            assert m.user_id in user_ids
        for a in s.exec(select(Attempt)).all():
            assert a.user_id in user_ids


def test_user_cluster_name(seeded):
    with Session(seeded) as s:
        generate_demo_users(s)
        carol = s.exec(select(User).where(User.username == "carol_strong")).one()
        name = user_cluster_name(s, carol.id)
    assert name in ("Yếu", "Trung bình", "Giỏi")


# ---- admin routes ----

@pytest.fixture()
def client(seeded):
    def _override():
        with Session(seeded) as s:
            yield s

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_admin(seeded, username="boss"):
    with Session(seeded) as s:
        u = User(username=username, password_hash=hash_password("secret123"), is_admin=True)
        s.add(u)
        s.commit()


def test_admin_clusters_requires_login(client):
    r = client.get("/admin/clusters", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_admin_clusters_forbidden_for_normal_user(client, seeded):
    client.post("/register", data={"username": "norm", "password": "secret123", "password2": "secret123"})
    client.post("/login", data={"username": "norm", "password": "secret123"})
    r = client.get("/admin/clusters")
    assert r.status_code == 403


def test_admin_clusters_ok_for_admin(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.get("/admin/clusters")
    assert r.status_code == 200
    assert "K-means" in r.text


def test_admin_seed_demo_then_clusters(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.post("/admin/seed_demo", follow_redirects=False)
    assert r.status_code == 303
    # After seeding, clusters page should render the scatter canvas.
    r = client.get("/admin/clusters")
    assert "clusterScatter" in r.text
    assert "alice_weak" in r.text


# ---- teacher panel (overview / students / questions) ----

def test_admin_overview_requires_admin(client, seeded):
    client.post("/register", data={"username": "norm2", "password": "secret123", "password2": "secret123"})
    client.post("/login", data={"username": "norm2", "password": "secret123"})
    assert client.get("/admin/overview").status_code == 403
    assert client.get("/admin/students").status_code == 403
    assert client.get("/admin/questions").status_code == 403


def test_admin_overview_renders(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.get("/admin/overview")
    assert r.status_code == 200
    assert "Panel giáo viên" in r.text
    assert "distChart" in r.text


def test_admin_students_list_and_detail(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    client.post("/admin/seed_demo")
    r = client.get("/admin/students")
    assert r.status_code == 200
    assert "alice_weak" in r.text
    # detail page for one demo student
    with Session(seeded) as s:
        alice = s.exec(select(User).where(User.username == "alice_weak")).one()
    r = client.get(f"/admin/students/{alice.id}")
    assert r.status_code == 200
    assert "alice_weak" in r.text


def test_admin_student_detail_404(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    assert client.get("/admin/students/99999").status_code == 404


def test_admin_questions_list(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.get("/admin/questions")
    assert r.status_code == 200
    assert "Thêm câu hỏi" in r.text


def test_admin_add_question(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    before = None
    with Session(seeded) as s:
        before = len(s.exec(select(Question).where(Question.topic_id == 1)).all())
    r = client.post("/admin/questions", data={
        "topic_id": "1", "content": "Câu hỏi mới test?",
        "option_a": "A1", "option_b": "B1", "option_c": "C1", "option_d": "D1",
        "correct_answer": "A1", "difficulty_level": "2",
    }, follow_redirects=False)
    assert r.status_code == 303
    with Session(seeded) as s:
        after = len(s.exec(select(Question).where(Question.topic_id == 1)).all())
    assert after == before + 1


def test_admin_add_question_strips_whitespace(client, seeded):
    """Trailing space on correct_answer must be stripped so it matches an option."""
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.post("/admin/questions", data={
        "topic_id": "1", "content": "Thủ đô VN?",
        "option_a": "Hà Nội", "option_b": "Huế", "option_c": "Đà Nẵng", "option_d": "TP HCM",
        "correct_answer": "  Hà Nội  ",  # trailing/leading space
        "difficulty_level": "1",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert "error" not in r.headers["location"]  # accepted, not rejected
    with Session(seeded) as s:
        q = s.exec(select(Question).where(Question.content == "Thủ đô VN?")).one()
        assert q.correct_answer == "Hà Nội"  # stored stripped
        assert q.correct_answer in __import__("json").loads(q.options_json)


def test_admin_add_question_rejects_bad_correct(client, seeded):
    _make_admin(seeded)
    client.post("/login", data={"username": "boss", "password": "secret123"})
    r = client.post("/admin/questions", data={
        "topic_id": "1", "content": "Q?",
        "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
        "correct_answer": "Z",  # not among options
        "difficulty_level": "1",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert "error" in r.headers["location"]
