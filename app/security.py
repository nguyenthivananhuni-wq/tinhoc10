"""Session-based auth helpers.

- hash_password / verify_password via passlib bcrypt
- sign_session / unsign_session via itsdangerous (HMAC-signed cookie payload)
- get_current_user / require_user FastAPI dependencies
"""
from __future__ import annotations

import os
import secrets

import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlmodel import Session

from app.db import get_session
from app.models import User

COOKIE_NAME = "tin10_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
# Trong production phục vụ qua HTTPS → cookie nên có Secure flag.
COOKIE_SECURE = os.environ.get("ENV", "development").lower() == "production"

_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_urlsafe(32)
_serializer = URLSafeTimedSerializer(_SECRET, salt="tin10-session")


def hash_password(plain: str) -> str:
    # bcrypt limits 72 bytes; truncate defensively to avoid raising on long passwords.
    raw = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        raw = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(raw, hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def sign_session(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def unsign_session(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=COOKIE_MAX_AGE)
        return int(data["uid"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        return None


def get_current_user(
    request_cookie: str | None = Cookie(default=None, alias=COOKIE_NAME),
    session: Session = Depends(get_session),
) -> User | None:
    """Returns User if cookie valid, else None (does NOT raise)."""
    if not request_cookie:
        return None
    uid = unsign_session(request_cookie)
    if uid is None:
        return None
    return session.get(User, uid)


def require_user(user: User | None = Depends(get_current_user)) -> User:
    """Raises 401 if no logged-in user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    """Raises 403 if the logged-in user is not an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return user
