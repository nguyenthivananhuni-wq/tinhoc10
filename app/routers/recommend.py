from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.ml.bkt_service import mastery_vector
from app.ml.recommender import recommend_topics
from app.models import LearningGoal, Topic, User
from app.security import require_user

router = APIRouter(tags=["recommend"])
templates = Jinja2Templates(directory="app/templates")

GOAL_LABELS = {
    "exam": ("Ôn thi học kỳ", "📝"),
    "new_topic": ("Học chủ đề mới", "🌱"),
    "improve": ("Cải thiện điểm yếu", "🔧"),
    "challenge": ("Thách thức nâng cao", "🔥"),
}


@router.get("/recommend", response_class=HTMLResponse)
def recommend(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    active = session.exec(
        select(LearningGoal)
        .where(LearningGoal.user_id == current_user.id, LearningGoal.is_active == True)  # noqa: E712
        .order_by(LearningGoal.set_at.desc())
    ).first()
    goal_type = active.goal_type if active else "exam"

    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    mastery_map = mastery_vector(current_user.id, session)
    recs = recommend_topics(topics, mastery_map, goal_type, n=3)

    goal_label, goal_icon = GOAL_LABELS.get(goal_type, ("Ôn thi học kỳ", "📝"))

    return templates.TemplateResponse(
        "recommend.html",
        {
            "request": request,
            "current_user": current_user,
            "recommendations": recs,
            "goal_type": goal_type,
            "goal_label": goal_label,
            "goal_icon": goal_icon,
            "has_goal": active is not None,
            "ability_theta": round(current_user.ability_theta, 2),
        },
    )
