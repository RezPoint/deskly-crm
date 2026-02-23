from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.activity import ActivityLogOut
from ...services.activity_service import ActivityService

router = APIRouter(tags=["activity"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("", response_model=List[ActivityLogOut])
def api_list_activity(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None, ge=1),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    service = ActivityService(db, tenant_id)
    return service.list_activity(limit, offset, user_id, entity_type, action, date_from, date_to)
