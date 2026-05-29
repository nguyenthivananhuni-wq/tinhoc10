from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.ml.bkt_service import apply_bkt_for_attempt
from app.ml.irt import estimate_ability
from app.ml.recommender import select_question
from app.models import GOAL_TYPES, Attempt, LearningGoal, Question, Topic, User
from app.security import require_user

router = APIRouter(tags=["learn"])
templates = Jinja2Templates(directory="app/templates")

QUIZ_LENGTH = 10  # số câu mỗi quiz session

GOAL_LABELS = {
    "exam": ("Ôn thi học kỳ", "📝", "Tập trung củng cố các chủ đề đã học."),
    "new_topic": ("Học chủ đề mới", "🌱", "Tiếp cận chủ đề chưa từng học."),
    "improve": ("Cải thiện điểm yếu", "🔧", "Tăng cường chủ đề có mastery thấp."),
    "challenge": ("Thách thức nâng cao", "🔥", "Làm các câu khó để vượt giới hạn."),
}


# ---- Goal ----

@router.get("/goal", response_class=HTMLResponse)
def get_goal(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    active = session.exec(
        select(LearningGoal)
        .where(LearningGoal.user_id == current_user.id, LearningGoal.is_active == True)  # noqa: E712
        .order_by(LearningGoal.set_at.desc())
    ).first()
    return templates.TemplateResponse(
        "goal_select.html",
        {
            "request": request,
            "current_user": current_user,
            "goal_options": GOAL_LABELS,
            "current_goal": active.goal_type if active else None,
        },
    )


@router.post("/goal")
def post_goal(
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
    goal_type: str = Form(...),
):
    if goal_type not in GOAL_TYPES:
        raise HTTPException(400, "Goal type không hợp lệ")
    actives = session.exec(
        select(LearningGoal).where(
            LearningGoal.user_id == current_user.id, LearningGoal.is_active == True  # noqa: E712
        )
    ).all()
    for g in actives:
        g.is_active = False
        session.add(g)
    session.add(LearningGoal(user_id=current_user.id, goal_type=goal_type, is_active=True))
    session.commit()
    return RedirectResponse("/topics", status_code=303)


# ---- Quiz ----

def _pick_next_question(
    session: Session, topic_id: int, user: User, attempted_qids: set[int]
) -> Question | None:
    """IRT adaptive selection (Phase 06): câu trong topic có độ khó b gần năng lực θ
    của user nhất, loại các câu đã làm trong session hiện tại và trong 24h gần đây.
    """
    return select_question(
        session,
        topic_id,
        theta=user.ability_theta,
        user_id=user.id,
        exclude_qids=attempted_qids,
    )


def _update_ability_from_session(
    session: Session, user: User, attempts: list[Attempt]
) -> None:
    """End-of-session: re-estimate θ qua MLE từ (difficulty_b, is_correct) và lưu."""
    responses: list[tuple[float, bool]] = []
    for a in attempts:
        q = session.get(Question, a.question_id)
        if q is not None:
            responses.append((q.difficulty_b, a.is_correct))
    if not responses:
        return
    user.ability_theta = estimate_ability(responses)
    session.add(user)
    session.commit()


def _attempts_in_session(session: Session, session_id: str) -> list[Attempt]:
    return session.exec(
        select(Attempt)
        .where(Attempt.session_id == session_id)
        .order_by(Attempt.attempted_at)
    ).all()


@router.get("/quiz/{topic_id}", response_class=HTMLResponse)
def start_quiz(
    topic_id: int,
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    topic = session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(404, "Topic không tồn tại")

    new_session_id = uuid.uuid4().hex
    q = _pick_next_question(session, topic_id, current_user, attempted_qids=set())
    if q is None:
        raise HTTPException(404, "Chưa có câu hỏi cho chủ đề này")

    return templates.TemplateResponse(
        "quiz.html",
        {
            "request": request,
            "current_user": current_user,
            "topic": topic,
            "question": q,
            "options": json.loads(q.options_json),
            "session_id": new_session_id,
            "current_index": 1,
            "total": QUIZ_LENGTH,
            "phase": "answer",
        },
    )


@router.post("/quiz/answer", response_class=HTMLResponse)
def submit_answer(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
    session_id: str = Form(...),
    question_id: int = Form(...),
    selected_answer: str = Form(...),
    response_time_ms: int = Form(default=0),
):
    q = session.get(Question, question_id)
    if q is None:
        raise HTTPException(404, "Question không tồn tại")

    is_correct = (selected_answer == q.correct_answer)
    attempt = Attempt(
        user_id=current_user.id,
        question_id=q.id,
        is_correct=is_correct,
        response_time_ms=max(0, int(response_time_ms or 0)),
        selected_answer=selected_answer,
        session_id=session_id,
    )
    session.add(attempt)
    session.commit()

    # BKT update: mastery for this topic
    apply_bkt_for_attempt(
        user_id=current_user.id,
        question_id=q.id,
        is_correct=is_correct,
        session=session,
    )

    attempts = _attempts_in_session(session, session_id)
    answered = len(attempts)
    is_last = answered >= QUIZ_LENGTH

    # End of session → re-estimate IRT ability θ from this session's responses.
    if is_last:
        _update_ability_from_session(session, current_user, attempts)

    return templates.TemplateResponse(
        "_quiz_card.html",
        {
            "request": request,
            "topic": q.topic_id,
            "topic_obj": session.get(Topic, q.topic_id),
            "question": q,
            "options": json.loads(q.options_json),
            "session_id": session_id,
            "current_index": answered,
            "total": QUIZ_LENGTH,
            "phase": "feedback",
            "selected_answer": selected_answer,
            "is_correct": is_correct,
            "is_last": is_last,
        },
    )


@router.get("/quiz/{topic_id}/next", response_class=HTMLResponse)
def next_question(
    topic_id: int,
    request: Request,
    session_id: str,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    attempts = _attempts_in_session(session, session_id)
    if len(attempts) >= QUIZ_LENGTH:
        # Trigger redirect via HTMX
        return Response(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/quiz/result/{session_id}"},
        )

    attempted_qids = {a.question_id for a in attempts}
    q = _pick_next_question(session, topic_id, current_user, attempted_qids)
    topic = session.get(Topic, topic_id)
    if q is None:
        return Response(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/quiz/result/{session_id}"},
        )

    return templates.TemplateResponse(
        "_quiz_card.html",
        {
            "request": request,
            "topic": topic_id,
            "topic_obj": topic,
            "question": q,
            "options": json.loads(q.options_json),
            "session_id": session_id,
            "current_index": len(attempts) + 1,
            "total": QUIZ_LENGTH,
            "phase": "answer",
            "selected_answer": None,
            "is_correct": None,
            "is_last": False,
        },
    )


@router.get("/quiz/result/{session_id}", response_class=HTMLResponse)
def quiz_result(
    session_id: str,
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Attempt, Question, Topic)
        .join(Question, Attempt.question_id == Question.id)
        .join(Topic, Question.topic_id == Topic.id)
        .where(Attempt.session_id == session_id, Attempt.user_id == current_user.id)
        .order_by(Attempt.attempted_at)
    ).all()

    if not rows:
        raise HTTPException(404, "Quiz session không tồn tại")

    total = len(rows)
    correct = sum(1 for a, _, _ in rows if a.is_correct)
    accuracy = correct / total * 100 if total else 0
    topic = rows[0][2]
    wrong_attempts = [(a, q) for a, q, _ in rows if not a.is_correct]

    return templates.TemplateResponse(
        "quiz_result.html",
        {
            "request": request,
            "current_user": current_user,
            "session_id": session_id,
            "topic": topic,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "wrong_attempts": [
                {
                    "content": q.content,
                    "selected": a.selected_answer,
                    "correct": q.correct_answer,
                    "options": json.loads(q.options_json),
                }
                for a, q in wrong_attempts
            ],
        },
    )
