from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user, require_role
from ...models import User, Invite
from ...schemas.auth import InviteCreate, InviteAccept, InviteOut
from ...services.invite_service import InviteService

router = APIRouter(tags=["invites"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("/invites", response_model=List[InviteOut])
def api_list_invites(
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db), 
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner", "admin"})
    service = InviteService(db, tenant_id)
    return service.list_invites()

@router.post("/invites", response_model=InviteOut)
def api_create_invite(
    payload: InviteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    require_role(user, {"owner", "admin"})
    service = InviteService(db, tenant_id)
    return service.create_invite(payload)

@router.post("/invites/accept")
def api_accept_invite(
    payload: InviteAccept,
    db: Session = Depends(get_db)
):
    # Этот маршрут не требует авторизации, так как это процесс принятия приглашения
    # Мы передаем tenant_id=1 как заглушку, сервис найдет арендатора по токену
    service = InviteService(db, 1)
    user = service.accept_invite(payload)
    return {"id": user.id, "email": user.email, "role": user.role}

@router.get("/invites/check")
def api_check_invite_token(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Вспомогательный эндпоинт для SPA, чтобы проверить валидность токена без попытки его принять"""
    from sqlalchemy import select
    from datetime import datetime, timezone
    invite = db.execute(select(Invite).where(Invite.token == token)).scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="invite not found")
    if invite.accepted_at:
        raise HTTPException(status_code=409, detail="invite already used")
        
    dt = invite.expires_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    if dt < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="invite expired")
        
    return {"email": invite.email, "role": invite.role}
