from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.ml.bkt_service import mastery_vector
from app.ml.clustering import user_cluster_name
from app.ml.recommender import recommend_topics
from app.models import Attempt, LearningGoal, Topic, User
from app.security import require_user

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    mastery_map = mastery_vector(current_user.id, session)

    topic_data = []
    for t in topics:
        p = mastery_map.get(t.id, 0.1)  # default = P(L0)
        topic_data.append(
            {
                "id": t.id,
                "name": t.name,
                "p_mastery": p,
                "percent": round(p * 100, 1),
                "level": (
                    "Yếu" if p < 0.4 else "Trung bình" if p < 0.7 else "Tốt"
                ),
            }
        )

    total = session.exec(
        select(func.count(Attempt.id)).where(Attempt.user_id == current_user.id)
    ).one()
    correct = session.exec(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == current_user.id, Attempt.is_correct == True  # noqa: E712
        )
    ).one()
    accuracy = (correct / total * 100) if total else 0.0
    avg_mastery = (
        sum(td["p_mastery"] for td in topic_data) / len(topic_data) if topic_data else 0.0
    )

    # K-means: nhóm của user (None nếu chưa đủ ≥3 user trong hệ thống).
    cluster_name = user_cluster_name(session, current_user.id)

    # Top-3 gợi ý từ recommendation engine (phase 06) theo goal hiện tại.
    active_goal = session.exec(
        select(LearningGoal)
        .where(LearningGoal.user_id == current_user.id, LearningGoal.is_active == True)  # noqa: E712
        .order_by(LearningGoal.set_at.desc())
    ).first()
    goal_type = active_goal.goal_type if active_goal else "exam"
    recommendations = recommend_topics(topics, mastery_map, goal_type, n=3)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "topics": topic_data,
            "topic_names_json": [td["name"] for td in topic_data],
            "mastery_percents_json": [td["percent"] for td in topic_data],
            "total_attempts": total,
            "correct_attempts": correct,
            "accuracy": accuracy,
            "avg_mastery_percent": round(avg_mastery * 100, 1),
            "cluster_name": cluster_name,
            "recommendations": recommendations,
        },
    )
