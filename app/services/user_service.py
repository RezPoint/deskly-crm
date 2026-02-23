from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import User, Tenant
from ..core.security import hash_password
from ..services.invite_service import validate_email

def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = value.replace(" ", "-")
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch == "-")
    cleaned = cleaned.strip("-")
    return cleaned or "default"

def _unique_slug(db: Session, base: str) -> str:
    slug = base
    counter = 1
    while db.execute(select(Tenant.id).where(Tenant.slug == slug)).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug

class UserService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_users(self):
        return self.db.execute(
            select(User)
            .where(User.tenant_id == self.tenant_id)
            .order_by(User.id.asc())
        ).scalars().all()

    def create_user(self, email: str, password: str, role: str):
        try:
            email = validate_email(email)
        except ValueError:
            raise HTTPException(status_code=422, detail="valid email required")
            
        if len(password) < 6:
            raise HTTPException(status_code=422, detail="password must be at least 6 chars")
        if role not in {"owner", "admin", "viewer"}:
            raise HTTPException(status_code=422, detail="invalid role")
            
        existing = self.db.execute(
            select(User).where(User.email == email, User.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="user already exists")
            
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            tenant_id=self.tenant_id
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_role(self, user_id: int, role: str):
        if role not in {"owner", "admin", "viewer"}:
            raise HTTPException(status_code=422, detail="invalid role")
            
        target = self.db.execute(
            select(User).where(User.id == user_id, User.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="user not found")
            
        target.role = role
        self.db.commit()
        return target

    def reset_password(self, user_id: int, password: str):
        if len(password) < 6:
            raise HTTPException(status_code=422, detail="password must be at least 6 chars")
            
        target = self.db.execute(
            select(User).where(User.id == user_id, User.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="user not found")
            
        target.password_hash = hash_password(password)
        self.db.commit()
        return target

    @classmethod
    def setup_account(cls, db: Session, email: str, password: str, workspace_name: str):
        if db.execute(select(User.id)).first():
            raise HTTPException(status_code=409, detail="setup already completed")
            
        try:
            email = validate_email(email)
        except ValueError:
            raise HTTPException(status_code=422, detail="valid email required")
            
        if len(password) < 6:
            raise HTTPException(status_code=422, detail="password must be at least 6 chars")
            
        workspace_name = (workspace_name or "").strip() or "Default"
        slug_base = _slugify(workspace_name)
        slug = _unique_slug(db, slug_base)
        
        tenant = Tenant(name=workspace_name, slug=slug)
        db.add(tenant)
        db.flush()
        
        user = User(
            email=email,
            password_hash=hash_password(password),
            role="owner",
            tenant_id=tenant.id
        )
        db.add(user)
        db.commit()
        return user
