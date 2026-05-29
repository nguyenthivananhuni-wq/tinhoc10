from __future__ import annotations

import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.ml.clustering import DEFAULT_K, analyze_clusters
from app.models import Attempt, MasteryState, Question, Topic, User
from app.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

# Bảng màu cho từng cluster (theo rank avg_mastery: Yếu / TB / Giỏi).
CLUSTER_COLORS = {
    "Yếu": "rgb(239, 68, 68)",
    "Trung bình": "rgb(234, 179, 8)",
    "Giỏi": "rgb(34, 197, 94)",
}


def _cluster_map(session: Session) -> dict[int, str]:
    """user_id → cluster_name (rỗng nếu chưa đủ dữ liệu)."""
    result = analyze_clusters(session, k=DEFAULT_K)
    if not result["ok"]:
        return {}
    return {p["user_id"]: p["cluster_name"] for p in result["points"]}


def _student_stats(session: Session, user: User, clusters: dict[int, str]) -> dict:
    total = session.exec(
        select(func.count(Attempt.id)).where(Attempt.user_id == user.id)
    ).one()
    correct = session.exec(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == user.id, Attempt.is_correct == True  # noqa: E712
        )
    ).one()
    masteries = session.exec(
        select(MasteryState.p_mastery).where(MasteryState.user_id == user.id)
    ).all()
    avg_mastery = (sum(masteries) / len(masteries)) if masteries else 0.0
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total else 0.0,
        "avg_mastery_percent": round(avg_mastery * 100, 1),
        "theta": round(user.ability_theta, 2),
        "cluster": clusters.get(user.id, "—"),
    }


# ---- Class overview / statistics ----

@router.get("/overview", response_class=HTMLResponse)
def overview(
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    users = session.exec(select(User)).all()
    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    questions = session.exec(select(Question)).all()
    clusters = _cluster_map(session)

    # Per-question accuracy (chỉ tính câu có ≥1 lượt làm).
    q_rows = []
    for q in questions:
        ats = session.exec(select(Attempt).where(Attempt.question_id == q.id)).all()
        if not ats:
            continue
        acc = sum(1 for a in ats if a.is_correct) / len(ats)
        q_rows.append({"content": q.content, "n": len(ats), "accuracy": round(acc * 100, 1)})
    hardest = sorted(q_rows, key=lambda r: r["accuracy"])[:5]
    easiest = sorted(q_rows, key=lambda r: r["accuracy"], reverse=True)[:5]

    # Mastery trung bình toàn lớp theo topic.
    topic_avg = []
    for t in topics:
        ms = session.exec(
            select(MasteryState.p_mastery).where(MasteryState.topic_id == t.id)
        ).all()
        avg = (sum(ms) / len(ms)) if ms else 0.0
        topic_avg.append({"name": t.name, "percent": round(avg * 100, 1)})
    topic_avg.sort(key=lambda r: r["percent"])

    # Phân bố độ chính xác học sinh (buckets 20%).
    buckets = [0, 0, 0, 0, 0]  # 0-20, 20-40, 40-60, 60-80, 80-100
    student_count = 0
    for u in users:
        st = _student_stats(session, u, clusters)
        if st["total"] == 0:
            continue
        student_count += 1
        idx = min(4, int(st["accuracy"] // 20))
        buckets[idx] += 1

    return templates.TemplateResponse(
        "admin_overview.html",
        {
            "request": request,
            "current_user": admin,
            "n_students": len(users),
            "n_active": student_count,
            "n_questions": len(questions),
            "n_topics": len(topics),
            "hardest": hardest,
            "easiest": easiest,
            "topic_avg": topic_avg,
            "buckets": buckets,
            "bucket_labels": ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"],
        },
    )


# ---- Student list + detail ----

@router.get("/students", response_class=HTMLResponse)
def students(
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    clusters = _cluster_map(session)
    users = session.exec(select(User).order_by(User.id)).all()
    rows = [_student_stats(session, u, clusters) for u in users]
    rows.sort(key=lambda r: r["avg_mastery_percent"], reverse=True)
    return templates.TemplateResponse(
        "admin_students.html",
        {"request": request, "current_user": admin, "students": rows},
    )


@router.get("/students/{user_id}", response_class=HTMLResponse)
def student_detail(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Học sinh không tồn tại")

    clusters = _cluster_map(session)
    stat = _student_stats(session, user, clusters)

    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    mastery_rows = session.exec(
        select(MasteryState).where(MasteryState.user_id == user_id)
    ).all()
    mastery_map = {m.topic_id: m.p_mastery for m in mastery_rows}
    per_topic = [
        {"name": t.name, "percent": round(mastery_map.get(t.id, 0.1) * 100, 1)}
        for t in topics
    ]

    recent = session.exec(
        select(Attempt, Question, Topic)
        .join(Question, Attempt.question_id == Question.id)
        .join(Topic, Question.topic_id == Topic.id)
        .where(Attempt.user_id == user_id)
        .order_by(Attempt.attempted_at.desc())
        .limit(15)
    ).all()

    return templates.TemplateResponse(
        "admin_student_detail.html",
        {
            "request": request,
            "current_user": admin,
            "student": stat,
            "per_topic": per_topic,
            "recent": recent,
        },
    )


# ---- Question management ----

@router.get("/questions", response_class=HTMLResponse)
def questions_list(
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
    topic_id: int | None = None,
    error: str | None = None,
    added: int = 0,
):
    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    stmt = select(Question, Topic).join(Topic, Question.topic_id == Topic.id)
    if topic_id:
        stmt = stmt.where(Question.topic_id == topic_id)
    stmt = stmt.order_by(Question.topic_id, Question.difficulty_level)
    rows = session.exec(stmt).all()

    questions = []
    for q, t in rows:
        questions.append({
            "id": q.id,
            "topic_name": t.name,
            "content": q.content,
            "difficulty_level": q.difficulty_level,
            "options": json.loads(q.options_json),
            "correct_answer": q.correct_answer,
        })

    return templates.TemplateResponse(
        "admin_questions.html",
        {
            "request": request,
            "current_user": admin,
            "topics": topics,
            "questions": questions,
            "filter_topic_id": topic_id,
            "error": error,
            "added": added,
        },
    )


@router.post("/questions")
def add_question(
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
    topic_id: int = Form(...),
    content: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_answer: str = Form(...),
    difficulty_level: int = Form(...),
):
    options = [option_a.strip(), option_b.strip(), option_c.strip(), option_d.strip()]
    correct_answer = correct_answer.strip()
    error = None
    if session.get(Topic, topic_id) is None:
        error = "Chủ đề không hợp lệ."
    elif not content.strip():
        error = "Nội dung câu hỏi không được trống."
    elif any(not o for o in options):
        error = "Cả 4 đáp án phải được điền."
    elif len(set(options)) != 4:
        error = "4 đáp án không được trùng nhau."
    elif correct_answer not in options:
        error = "Đáp án đúng phải là một trong 4 lựa chọn."
    elif difficulty_level not in (1, 2, 3):
        error = "Mức độ khó phải là 1, 2 hoặc 3."

    if error:
        return RedirectResponse(f"/admin/questions?error={quote(error)}", status_code=303)

    session.add(Question(
        topic_id=topic_id,
        content=content.strip(),
        difficulty_level=difficulty_level,
        options_json=json.dumps(options, ensure_ascii=False),
        correct_answer=correct_answer,
    ))
    session.commit()
    return RedirectResponse(f"/admin/questions?topic_id={topic_id}&added=1", status_code=303)


# ---- Clustering (giữ nguyên) ----

@router.get("/clusters", response_class=HTMLResponse)
def clusters(
    request: Request,
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    result = analyze_clusters(session, k=DEFAULT_K)

    datasets = []
    if result["ok"]:
        by_name: dict[str, list[dict]] = {}
        for p in result["points"]:
            by_name.setdefault(p["cluster_name"], []).append(p)
        for name, pts in by_name.items():
            datasets.append({
                "label": name,
                "color": CLUSTER_COLORS.get(name, "rgb(59, 130, 246)"),
                "data": [{"x": p["x"], "y": p["y"], "username": p["username"]} for p in pts],
            })

    return templates.TemplateResponse(
        "admin_clusters.html",
        {
            "request": request,
            "current_user": admin,
            "result": result,
            "datasets": datasets,
        },
    )


@router.post("/seed_demo")
def seed_demo(
    admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    # Import tại đây để tránh nạp script (và DB engine của nó) lúc khởi động app.
    from scripts.generate_demo_users import generate_demo_users

    generate_demo_users(session)
    return RedirectResponse("/admin/clusters", status_code=303)
