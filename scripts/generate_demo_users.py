"""Generate demo students with distinct learning patterns — for K-means demo.

Creates 3 users so clustering has separable groups:

    alice_weak    — trả lời sai nhiều, chậm  → cluster "Yếu".
    bob_avg       — ~60% đúng, tốc độ vừa     → cluster "Trung bình".
    carol_strong  — đúng nhiều, kể cả câu khó → cluster "Giỏi".

Mỗi user được simulate Attempt trên câu hỏi thật, chạy BKT update mastery, rồi
ước lượng IRT ability θ. Idempotent: bỏ qua user đã tồn tại.

Usage:
    python -m scripts.generate_demo_users            # tạo trên DB dev
    python -m scripts.generate_demo_users --force    # tạo lại kể cả đã có
"""
from __future__ import annotations

import argparse
import random

from sqlmodel import Session, delete, select

from app.db import engine
from app.ml.bkt_service import apply_bkt_for_attempt
from app.ml.irt import estimate_ability
from app.models import Attempt, LearningGoal, MasteryState, Question, Topic, User
from app.security import hash_password

DEMO_PASSWORD = "demo123456"

# (username, P(đúng câu dễ), P(đúng câu khó), response_time_ms trung bình)
DEMO_PROFILES = [
    ("alice_weak", 0.45, 0.15, 9000),
    ("bob_avg", 0.75, 0.45, 5500),
    ("carol_strong", 0.95, 0.80, 3000),
]

# Số câu mỗi user làm trên mỗi topic.
QUESTIONS_PER_TOPIC = 6


def _simulate_user(
    session: Session,
    username: str,
    p_easy: float,
    p_hard: float,
    avg_rt: int,
    rng: random.Random,
) -> User:
    user = User(username=username, password_hash=hash_password(DEMO_PASSWORD))
    session.add(user)
    session.commit()
    session.refresh(user)

    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    responses: list[tuple[float, bool]] = []
    session_id = f"demo-{username}"

    for topic in topics:
        questions = session.exec(
            select(Question).where(Question.topic_id == topic.id)
        ).all()
        rng.shuffle(questions)
        for q in questions[:QUESTIONS_PER_TOPIC]:
            # Xác suất đúng theo độ khó câu.
            p_correct = p_hard if q.difficulty_level >= 3 else p_easy
            if q.difficulty_level == 2:
                p_correct = (p_easy + p_hard) / 2
            is_correct = rng.random() < p_correct
            rt = max(500, int(rng.gauss(avg_rt, avg_rt * 0.25)))

            session.add(Attempt(
                user_id=user.id,
                question_id=q.id,
                is_correct=is_correct,
                response_time_ms=rt,
                selected_answer=q.correct_answer if is_correct else "Z",
                session_id=session_id,
            ))
            session.commit()
            apply_bkt_for_attempt(user.id, q.id, is_correct, session)
            responses.append((q.difficulty_b, is_correct))

    user.ability_theta = estimate_ability(responses)
    session.add(user)
    session.commit()
    return user


def generate_demo_users(session: Session, force: bool = False, seed: int = 42) -> list[str]:
    """Create demo users. Returns list of usernames actually created."""
    rng = random.Random(seed)
    created: list[str] = []
    for username, p_easy, p_hard, avg_rt in DEMO_PROFILES:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing is not None:
            if not force:
                continue
            _delete_user_cascade(session, existing.id)
        _simulate_user(session, username, p_easy, p_hard, avg_rt, rng)
        created.append(username)
    return created


def _delete_user_cascade(session: Session, user_id: int) -> None:
    """Xóa user + các bản ghi con (không có cascade FK trong schema SQLite)."""
    session.exec(delete(Attempt).where(Attempt.user_id == user_id))
    session.exec(delete(MasteryState).where(MasteryState.user_id == user_id))
    session.exec(delete(LearningGoal).where(LearningGoal.user_id == user_id))
    user = session.get(User, user_id)
    if user is not None:
        session.delete(user)
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo students for clustering.")
    parser.add_argument("--force", action="store_true", help="Recreate even if users exist.")
    args = parser.parse_args()

    with Session(engine) as session:
        created = generate_demo_users(session, force=args.force)
        if created:
            print(f"Created {len(created)} demo user(s): {', '.join(created)}")
            print(f"Password for all: {DEMO_PASSWORD}")
        else:
            print("Demo users already exist (use --force to recreate).")


if __name__ == "__main__":
    main()
