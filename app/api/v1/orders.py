from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, OrderPriceUpdate, OrderSummaryOut
from ...services.order_service import OrderService

router = APIRouter(tags=["orders"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("", response_model=List[OrderOut])
def list_orders(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = None,
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|price_desc|price_asc)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    service = OrderService(db, tenant_id)
    return service.list_orders(client_id, status, q, limit, offset, sort, date_from, date_to)

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    return service.get_order(order_id)

@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    return service.create_order(payload)

@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    service.delete_order(order_id)

@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    return service.update_status(order_id, payload.status)

@router.patch("/{order_id}/price", response_model=OrderOut)
def update_price(order_id: int, payload: OrderPriceUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    return service.update_price(order_id, payload.price)

@router.get("/{order_id}/summary", response_model=OrderSummaryOut)
def order_summary(order_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = OrderService(db, tenant_id)
    return service.get_summary(order_id)
