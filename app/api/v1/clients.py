from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.client import ClientCreate, ClientOut
from ...services.client_service import ClientService

router = APIRouter(tags=["clients"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

def get_user_id(user: User = Depends(get_current_user)):
    return getattr(user, "id", None)

@router.get("", response_model=List[ClientOut])
def api_list_clients(
    q: Optional[str] = Query(None, min_length=1, max_length=120),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|name_asc|name_desc)$"),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    service = ClientService(db, tenant_id)
    return service.list_clients(q, limit, offset, sort)

@router.post("", response_model=ClientOut)
def api_create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: int = Depends(get_user_id)
):
    service = ClientService(db, tenant_id)
    return service.create_client(payload, user_id)

@router.get("/{client_id}", response_model=ClientOut)
def api_get_client(
    client_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    service = ClientService(db, tenant_id)
    return service.get_client(client_id)

@router.delete("/{client_id}", status_code=204)
def api_delete_client(
):
    service = ClientService(db, tenant_id)
    service.delete_client(client_id)
