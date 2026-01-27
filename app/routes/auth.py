from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import create_access_token, hash_password, verify_password


router = APIRouter(tags=["auth"])

TEMPLATES_DIR = __import__("pathlib").Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def _has_users(db: Session) -> bool:
    return db.execute(select(User.id)).first() is not None


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    if _has_users(db):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "setup.html",
        {"request": request, "error": "", "email": ""},
    )


@router.post("/setup")
def setup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if _has_users(db):
        return RedirectResponse(url="/login", status_code=303)

    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return templates.TemplateResponse(
            request,
            "setup.html",
            {"request": request, "error": "Valid email is required", "email": email},
            status_code=422,
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "setup.html",
            {"request": request, "error": "Password must be at least 6 characters", "email": email},
            status_code=422,
        )

    user = User(email=email, password_hash=hash_password(password), role="owner")
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if not _has_users(db):
        return RedirectResponse(url="/setup", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request, "error": "", "email": ""},
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = (email or "").strip().lower()
    user = _get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "Invalid credentials", "email": email},
            status_code=401,
        )
    token = create_access_token(user.id, user.role)
    resp = RedirectResponse(url="/ui/clients", status_code=303)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp


@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("access_token")
    return resp


@router.post("/api/auth/login")
def api_login(payload: dict, db: Session = Depends(get_db)):
    if not _has_users(db):
        raise HTTPException(status_code=409, detail="setup required")
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = _get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token = create_access_token(user.id, user.role)
    resp = JSONResponse({"access_token": token, "token_type": "bearer"})
    resp.set_cookie("access_token", token, httponly=True, samesite="lax")
    return resp
