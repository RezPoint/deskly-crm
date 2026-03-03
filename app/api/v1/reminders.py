from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from ...services.reminder_service import ReminderService

router = APIRouter(tags=["reminders"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)
    
def get_user_id(user: User = Depends(get_current_user)):
    return getattr(user, "id", None)

@router.get("", response_model=List[ReminderOut])
def api_list_reminders(
    status: Optional[str] = Query(None, pattern="^(open|done)$"),
    overdue: Optional[bool] = Query(None),
    today: Optional[bool] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    service = ReminderService(db, tenant_id)
    return service.list_reminders(status, overdue, today, entity_type, entity_id, limit, offset)

@router.post("", response_model=ReminderOut)
def api_create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: Optional[int] = Depends(get_user_id)
):
    service = ReminderService(db, tenant_id)
    return service.create_reminder(payload, user_id)

@router.patch("/{reminder_id}", response_model=ReminderOut)
def api_update_reminder(
    payload: ReminderUpdate,
    reminder_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: Optional[int] = Depends(get_user_id)
):
    service = ReminderService(db, tenant_id)
    return service.update_reminder(reminder_id, payload, user_id)

@router.delete("/{reminder_id}", status_code=204)
def api_delete_reminder(
    reminder_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: Optional[int] = Depends(get_user_id)
):
    service = ReminderService(db, tenant_id)
    service.delete_reminder(reminder_id, user_id)
