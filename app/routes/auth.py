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
from ..auth import get_current_user, require_role
from ..validators import validate_email
from .ui import templates


router = APIRouter(tags=["auth"])


def _get_user_by_email(db: Session, email: str, tenant_id: Optional[int] = None) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    if tenant_id is not None:
        stmt = stmt.where(User.tenant_id == tenant_id)
    return db.execute(stmt).scalar_one_or_none()


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

    try:
        email = validate_email(email)
    except ValueError:
        email = None
    if not email:
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


@router.get("/api/users")
def api_list_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    users = (
        db.execute(select(User).where(User.tenant_id == tenant_id).order_by(User.id.asc()))
        .scalars()
        .all()
    )
    return [{"id": u.id, "email": u.email, "role": u.role, "created_at": u.created_at} for u in users]


@router.post("/api/users")
def api_create_user(request: Request, payload: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    try:
        email = validate_email(payload.get("email"))
    except ValueError:
        email = None
    password = payload.get("password") or ""
    role = (payload.get("role") or "viewer").strip()
    if not email:
        raise HTTPException(status_code=422, detail="valid email required")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="password must be at least 6 chars")
    if role not in {"owner", "admin", "viewer"}:
        raise HTTPException(status_code=422, detail="invalid role")
    if _get_user_by_email(db, email, tenant_id=tenant_id):
        raise HTTPException(status_code=409, detail="user already exists")
    new_user = User(email=email, password_hash=hash_password(password), role=role, tenant_id=tenant_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "role": new_user.role}


@router.patch("/api/users/{user_id}/role")
def api_update_role(user_id: int, request: Request, payload: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner"})
    tenant_id = getattr(user, "tenant_id", 1)
    role = (payload.get("role") or "").strip()
    if role not in {"owner", "admin", "viewer"}:
        raise HTTPException(status_code=422, detail="invalid role")
    target = db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    target.role = role
    db.commit()
    return {"id": target.id, "role": target.role}


@router.post("/api/users/{user_id}/reset-password")
def api_reset_password(user_id: int, request: Request, payload: dict, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    password = payload.get("password") or ""
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="password must be at least 6 chars")
    target = db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    target.password_hash = hash_password(password)
    db.commit()
    return {"id": target.id}


@router.get("/ui/users", response_class=HTMLResponse)
def ui_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user.role == "viewer":
        return RedirectResponse(url="/ui/clients", status_code=303)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    users = (
        db.execute(select(User).where(User.tenant_id == tenant_id).order_by(User.id.asc()))
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "users.html",
        {"request": request, "users": users, "error": ""},
    )


@router.post("/ui/users")
def ui_create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("viewer"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    try:
        email = validate_email(email)
    except ValueError:
        email = None
    if not email:
        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "request": request,
                "users": db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all(),
                "error": "Valid email required",
            },
            status_code=422,
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "request": request,
                "users": db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all(),
                "error": "Password too short",
            },
            status_code=422,
        )
    if role not in {"owner", "admin", "viewer"}:
        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "request": request,
                "users": db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all(),
                "error": "Invalid role",
            },
            status_code=422,
        )
    if _get_user_by_email(db, email, tenant_id=tenant_id):
        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "request": request,
                "users": db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all(),
                "error": "User already exists",
            },
            status_code=409,
        )
    new_user = User(email=email, password_hash=hash_password(password), role=role, tenant_id=tenant_id)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/ui/users", status_code=303)


@router.post("/ui/users/{user_id}/role")
def ui_update_role(
    request: Request,
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    require_role(user, {"owner"})
    tenant_id = getattr(user, "tenant_id", 1)
    target = db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    if role not in {"owner", "admin", "viewer"}:
        raise HTTPException(status_code=422, detail="invalid role")
    target.role = role
    db.commit()
    return RedirectResponse(url="/ui/users", status_code=303)


@router.post("/ui/users/{user_id}/reset-password")
def ui_reset_password(
    request: Request,
    user_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    tenant_id = getattr(user, "tenant_id", 1)
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "users.html",
            {
                "request": request,
                "users": db.execute(select(User).where(User.tenant_id == tenant_id)).scalars().all(),
                "error": "Password too short",
            },
            status_code=422,
        )
    target = db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    target.password_hash = hash_password(password)
    db.commit()
    return RedirectResponse(url="/ui/users", status_code=303)
