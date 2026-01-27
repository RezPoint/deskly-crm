from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Invite, User
from ..schemas import InviteCreate, InviteAccept, InviteOut
from ..auth import get_current_user, require_role
from ..security import hash_password
from ..validators import validate_email
from .ui import templates


router = APIRouter(tags=["invites"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/api/invites", response_model=list[InviteOut])
def list_invites(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    invites = (
        db.execute(
            select(Invite)
            .where(Invite.tenant_id == user.tenant_id)
            .order_by(Invite.id.desc())
        )
        .scalars()
        .all()
    )
    return invites


@router.post("/api/invites", response_model=InviteOut)
def create_invite(payload: InviteCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})

    try:
        email = validate_email(payload.email)
    except ValueError:
        email = None
    if not email:
        raise HTTPException(status_code=422, detail="valid email required")

    existing = db.execute(
        select(User.id).where(User.email == email, User.tenant_id == user.tenant_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="user already exists")

    token = secrets.token_urlsafe(32)
    expires_at = _now() + timedelta(days=payload.expires_in_days)
    invite = Invite(
        tenant_id=user.tenant_id,
        email=email,
        role=payload.role.value,
        token=token,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/api/invites/accept")
def accept_invite(payload: InviteAccept, db: Session = Depends(get_db)):
    invite = db.execute(select(Invite).where(Invite.token == payload.token)).scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="invite not found")
    if invite.accepted_at is not None:
        raise HTTPException(status_code=409, detail="invite already used")
    if _normalize(invite.expires_at) < _now():
        raise HTTPException(status_code=410, detail="invite expired")
    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="password must be at least 6 chars")

    existing = db.execute(
        select(User.id).where(User.email == invite.email, User.tenant_id == invite.tenant_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="user already exists")

    user = User(
        email=invite.email,
        password_hash=hash_password(payload.password),
        role=invite.role,
        tenant_id=invite.tenant_id,
    )
    db.add(user)
    db.flush()
    invite.accepted_at = _now()
    invite.accepted_by = user.id
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.get("/invite", response_class=HTMLResponse)
def invite_page(
    request: Request,
    token: str = Query(""),
    db: Session = Depends(get_db),
):
    invite = None
    if token:
        invite = db.execute(select(Invite).where(Invite.token == token)).scalar_one_or_none()
    return templates.TemplateResponse(
        request,
        "invite.html",
        {
            "request": request,
            "token": token,
            "invite": invite,
            "error": "",
        },
    )


@router.post("/invite")
def invite_accept_form(
    request: Request,
    token: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        accept_invite(InviteAccept(token=token, password=password), db)
    except HTTPException as exc:
        invite = db.execute(select(Invite).where(Invite.token == token)).scalar_one_or_none()
        return templates.TemplateResponse(
            request,
            "invite.html",
            {
                "request": request,
                "token": token,
                "invite": invite,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )
    return RedirectResponse(url="/login", status_code=303)


@router.get("/ui/invites", response_class=HTMLResponse)
def ui_invites(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    invites = (
        db.execute(
            select(Invite)
            .where(Invite.tenant_id == user.tenant_id)
            .order_by(Invite.id.desc())
        )
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "invites.html",
        {"request": request, "invites": invites, "error": ""},
    )


@router.post("/ui/invites")
def ui_create_invite(
    request: Request,
    email: str = Form(""),
    role: str = Form("viewer"),
    expires_in_days: int = Form(7),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    require_role(user, {"owner", "admin"})
    try:
        email = validate_email(email)
    except ValueError:
        email = None
    if not email:
        return templates.TemplateResponse(
            request,
            "invites.html",
            {"request": request, "invites": [], "error": "Valid email required"},
            status_code=422,
        )
    if role not in {"owner", "admin", "viewer"}:
        return templates.TemplateResponse(
            request,
            "invites.html",
            {"request": request, "invites": [], "error": "Invalid role"},
            status_code=422,
        )
    try:
        expires_days = int(expires_in_days)
    except Exception:
        expires_days = 7
    expires_days = max(1, min(expires_days, 30))

    invite = create_invite(
        InviteCreate(email=email, role=role, expires_in_days=expires_days), request, db
    )
    return RedirectResponse(url=f"/ui/invites?created={invite.id}", status_code=303)
