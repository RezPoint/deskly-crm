from typing import Optional
from datetime import datetime
from pydantic import Field

from ..schemas.base import APIModel

class UserRole(str):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"

class UserOut(APIModel):
    id: int
    email: str
    role: str
    created_at: datetime

class LoginIn(APIModel):
    email: str
    password: str

class InviteCreate(APIModel):
    email: str
    role: str = "viewer"
    expires_in_days: int = Field(7, ge=1, le=30)

class InviteAccept(APIModel):
    token: str
    password: str

class InviteOut(APIModel):
    id: int
    email: str
    role: str
    token: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
