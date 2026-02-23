from datetime import datetime, timedelta, timezone
import secrets
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import Invite, User
from ..schemas.auth import InviteCreate, InviteAccept
from ..core.security import hash_password

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _normalize(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", cleaned):
        raise ValueError("Invalid email format")
    return cleaned

class InviteService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_invites(self):
        return self.db.execute(
            select(Invite)
            .where(Invite.tenant_id == self.tenant_id)
            .order_by(Invite.id.desc())
        ).scalars().all()

    def create_invite(self, data: InviteCreate) -> Invite:
        try:
            email = validate_email(data.email)
        except ValueError:
            raise HTTPException(status_code=422, detail="valid email required")

        existing = self.db.execute(
            select(User.id).where(User.email == email, User.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="user already exists")

        token = secrets.token_urlsafe(32)
        expires_at = _now() + timedelta(days=data.expires_in_days)
        invite = Invite(
            tenant_id=self.tenant_id,
            email=email,
            role=data.role,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def accept_invite(self, data: InviteAccept):
        invite = self.db.execute(select(Invite).where(Invite.token == data.token)).scalar_one_or_none()
        if invite is None:
            raise HTTPException(status_code=404, detail="invite not found")
        if invite.accepted_at is not None:
            raise HTTPException(status_code=409, detail="invite already used")
        if _normalize(invite.expires_at) < _now():
            raise HTTPException(status_code=410, detail="invite expired")
        if len(data.password) < 6:
            raise HTTPException(status_code=422, detail="password must be at least 6 chars")

        existing = self.db.execute(
            select(User.id).where(User.email == invite.email, User.tenant_id == invite.tenant_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="user already exists")

        user = User(
            email=invite.email,
            password_hash=hash_password(data.password),
            role=invite.role,
            tenant_id=invite.tenant_id,
        )
        self.db.add(user)
        self.db.flush()
        
        invite.accepted_at = _now()
        invite.accepted_by = user.id
        self.db.commit()
        return user
