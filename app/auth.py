from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User
from .security import decode_access_token


PUBLIC_PATHS = {
    "/",
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/login",
    "/logout",
    "/setup",
    "/api/auth/login",
}


def _get_token_from_request(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie
    return None


def get_current_user(request: Request, db: Session) -> User:
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="not authenticated")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="invalid token")
    user_id = int(payload["sub"])
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid token")
    request.state.user = user
    return user


def has_users(db: Session) -> bool:
    return db.execute(select(User.id)).first() is not None


def require_role(user: User, allowed: set[str]) -> None:
    if user.role not in allowed:
        raise HTTPException(status_code=403, detail="forbidden")
