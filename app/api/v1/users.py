from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user, require_role
from ...models import User
from ...schemas.auth import UserOut
from ...services.user_service import UserService

router = APIRouter(tags=["users"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

class UserCreateInput(BaseModel):
    email: str
    password: str
    role: str = "viewer"

class UserRoleUpdate(BaseModel):
    role: str

class UserPasswordUpdate(BaseModel):
    password: str

@router.get("", response_model=List[UserOut])
def api_list_users(
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db), 
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner", "admin"})
    service = UserService(db, tenant_id)
    return service.list_users()

@router.post("", response_model=UserOut)
def api_create_user(
    payload: UserCreateInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner", "admin"})
    service = UserService(db, tenant_id)
    return service.create_user(payload.email, payload.password, payload.role)

@router.patch("/{user_id}/role", response_model=UserOut)
def api_update_role(
    payload: UserRoleUpdate,
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner"}) # Только владельцы могут менять роли
    service = UserService(db, tenant_id)
    return service.update_role(user_id, payload.role)

@router.post("/{user_id}/reset-password")
def api_reset_password(
    payload: UserPasswordUpdate,
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner", "admin"})
    service = UserService(db, tenant_id)
    service.reset_password(user_id, payload.password)
    return {"detail": "password updated"}
