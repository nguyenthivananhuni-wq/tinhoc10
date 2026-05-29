import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Question, Topic
from app.routers import admin, auth, dashboard, pages, quiz, recommend
from app.seed import init_db

# Trong production (ENV=production) ẩn Swagger/Redoc để giảm bề mặt tấn công.
_IS_PROD = os.environ.get("ENV", "development").lower() == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Hệ thống học Tin học 10 - Cánh Diều",
    description="Web app cá nhân hóa lộ trình học Tin 10 (BKT + IRT + K-means)",
    version="0.7.0",
    lifespan=lifespan,
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.exception_handler(401)
async def unauthorized_redirect(request: Request, exc: StarletteHTTPException):
    """Chưa đăng nhập mà vào trang cần auth → chuyển về /login thay vì trả JSON 401."""
    return RedirectResponse("/login", status_code=303)

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)
app.include_router(recommend.router)
app.include_router(admin.router)


# ---- legacy JSON endpoints (kept for debugging/Swagger) ----

@app.get("/api/topics")
def api_topics(session: Session = Depends(get_session)):
    counts = dict(
        session.exec(
            select(Question.topic_id, func.count(Question.id)).group_by(Question.topic_id)
        ).all()
    )
    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "order": t.order_in_syllabus,
            "description": t.description,
            "question_count": counts.get(t.id, 0),
        }
        for t in topics
    ]


@app.get("/api/stats")
def api_stats(session: Session = Depends(get_session)):
    total = session.exec(select(func.count(Question.id))).one()
    by_level = dict(
        session.exec(
            select(Question.difficulty_level, func.count(Question.id)).group_by(
                Question.difficulty_level
            )
        ).all()
    )
    return {
        "total_questions": total,
        "total_topics": session.exec(select(func.count(Topic.id))).one(),
        "by_difficulty": {
            "level_1_easy": by_level.get(1, 0),
            "level_2_medium": by_level.get(2, 0),
            "level_3_hard": by_level.get(3, 0),
        },
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": app.version}
