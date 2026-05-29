from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.ml.clustering import user_cluster_name
from app.models import Attempt, Question, Topic, User
from app.security import get_current_user, require_user

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")

THEORY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "theory"


@router.get("/", response_class=HTMLResponse)
def landing(request: Request, current_user: User | None = Depends(get_current_user)):
    return templates.TemplateResponse(
        "landing.html", {"request": request, "current_user": current_user}
    )


@router.get("/topics", response_class=HTMLResponse)
def topic_list_page(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    counts = dict(
        session.exec(
            select(Question.topic_id, func.count(Question.id)).group_by(Question.topic_id)
        ).all()
    )
    return templates.TemplateResponse(
        "topic_list.html",
        {
            "request": request,
            "current_user": current_user,
            "topics": topics,
            "counts": counts,
        },
    )


@router.get("/theory/{topic_id}", response_class=HTMLResponse)
def theory_page(
    topic_id: int,
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    topic = session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(404, "Topic không tồn tại")

    md_file = THEORY_DIR / f"topic-{topic_id:02d}.md"
    content = md_file.read_text(encoding="utf-8") if md_file.exists() else "*Chưa có nội dung.*"
    html = _markdown_to_html(content)

    all_topics = session.exec(select(Topic).order_by(Topic.order_in_syllabus)).all()
    return templates.TemplateResponse(
        "theory.html",
        {
            "request": request,
            "current_user": current_user,
            "topic": topic,
            "topics": all_topics,
            "content_html": html,
        },
    )


@router.get("/history", response_class=HTMLResponse)
def history_page(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
    limit: int = 50,
):
    rows = session.exec(
        select(Attempt, Question, Topic)
        .join(Question, Attempt.question_id == Question.id)
        .join(Topic, Question.topic_id == Topic.id)
        .where(Attempt.user_id == current_user.id)
        .order_by(Attempt.attempted_at.desc())
        .limit(limit)
    ).all()

    total = session.exec(
        select(func.count(Attempt.id)).where(Attempt.user_id == current_user.id)
    ).one()
    correct = session.exec(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == current_user.id, Attempt.is_correct == True  # noqa: E712
        )
    ).one()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "current_user": current_user,
            "attempts": rows,
            "total": total,
            "correct": correct,
            "accuracy": (correct / total * 100) if total else 0,
        },
    )


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    total = session.exec(
        select(func.count(Attempt.id)).where(Attempt.user_id == current_user.id)
    ).one()
    correct = session.exec(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == current_user.id, Attempt.is_correct == True  # noqa: E712
        )
    ).one()
    accuracy = (correct / total * 100) if total else 0.0
    cluster_name = user_cluster_name(session, current_user.id)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "current_user": current_user,
            "total_attempts": total,
            "correct_attempts": correct,
            "accuracy": accuracy,
            "cluster_name": cluster_name,
        },
    )


def _markdown_to_html(md: str) -> str:
    """Minimal Markdown → HTML. Đủ cho theory pages (heading, list, code, table, blockquote)."""
    import html as _html
    import re as _re

    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    code_buf: list[str] = []
    in_table = False
    table_header_done = False
    in_list_ul = False
    in_list_ol = False

    def close_lists():
        nonlocal in_list_ul, in_list_ol
        if in_list_ul:
            out.append("</ul>")
            in_list_ul = False
        if in_list_ol:
            out.append("</ol>")
            in_list_ol = False

    def close_table():
        nonlocal in_table, table_header_done
        if in_table:
            out.append("</tbody></table>")
            in_table = False
            table_header_done = False

    def inline(t: str) -> str:
        t = _html.escape(t)
        t = _re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = _re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" class="text-blue-600 hover:underline">\1</a>', t)
        return t

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                out.append(f"<pre><code>{_html.escape(chr(10).join(code_buf))}</code></pre>")
                code_buf = []
                in_code = False
            else:
                close_lists(); close_table()
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        if line.startswith("| ") and "|" in line[2:]:
            if not in_table:
                close_lists()
                out.append('<table><thead>')
                in_table = True
                table_header_done = False
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not table_header_done:
                if all(_re.match(r"^:?-+:?$", c) for c in cells):
                    out.append('</thead><tbody>')
                    table_header_done = True
                else:
                    out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        else:
            close_table()

        h_match = _re.match(r"^(#{1,6})\s+(.+)$", line)
        if h_match:
            close_lists()
            level = len(h_match.group(1))
            out.append(f"<h{level}>{inline(h_match.group(2))}</h{level}>")
            continue

        if line.startswith("> "):
            close_lists()
            out.append(f"<blockquote>{inline(line[2:])}</blockquote>")
            continue

        m_ol = _re.match(r"^\d+\.\s+(.+)$", line)
        m_ul = _re.match(r"^[-*]\s+(.+)$", line)
        if m_ol:
            if not in_list_ol:
                close_lists()
                out.append("<ol>")
                in_list_ol = True
            out.append(f"<li>{inline(m_ol.group(1))}</li>")
            continue
        if m_ul:
            if not in_list_ul:
                close_lists()
                out.append("<ul>")
                in_list_ul = True
            out.append(f"<li>{inline(m_ul.group(1))}</li>")
            continue
        close_lists()

        if line.strip() == "":
            continue
        out.append(f"<p>{inline(line)}</p>")

    close_lists(); close_table()
    if in_code:
        out.append(f"<pre><code>{_html.escape(chr(10).join(code_buf))}</code></pre>")
    return "\n".join(out)
