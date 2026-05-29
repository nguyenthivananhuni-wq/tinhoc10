from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models import User
from app.security import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    COOKIE_SECURE,
    get_current_user,
    hash_password,
    sign_session,
    verify_password,
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request, current_user=Depends(get_current_user)):
    if current_user:
        return RedirectResponse("/topics", status_code=303)
    return templates.TemplateResponse(
        "register.html", {"request": request, "current_user": None, "error": None}
    )


@router.post("/register", response_class=HTMLResponse)
def post_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
    session: Session = Depends(get_session),
):
    error = None
    username = username.strip()

    if not USERNAME_RE.match(username):
        error = "Username phải 3-20 ký tự, chỉ chữ/số/dấu gạch dưới."
    elif len(password) < 6:
        error = "Mật khẩu tối thiểu 6 ký tự."
    elif password != password2:
        error = "Hai mật khẩu không khớp."
    else:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            error = "Username đã tồn tại."

    if error:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "current_user": None, "error": error, "username": username},
            status_code=400,
        )

    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    return RedirectResponse("/login?registered=1", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request, registered: int = 0, current_user=Depends(get_current_user)):
    if current_user:
        return RedirectResponse("/topics", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "current_user": None,
            "error": None,
            "registered": bool(registered),
        },
    )


@router.post("/login", response_class=HTMLResponse)
def post_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == username.strip())).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "current_user": None,
                "error": "Sai username hoặc mật khẩu.",
                "username": username,
                "registered": False,
            },
            status_code=400,
        )

    token = sign_session(user.id)
    response = RedirectResponse("/topics", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return response


@router.post("/logout")
def post_logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
