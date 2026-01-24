from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Client, Order
from ..schemas import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    orders = db.execute(select(Order).order_by(Order.id.desc())).scalars().all()
    return orders


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    client = db.execute(select(Client).where(Client.id == payload.client_id)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    o = Order(
        client_id=payload.client_id,
        title=payload.title.strip(),
        price=payload.price,
        status=payload.status.value,
        comment=payload.comment,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status.value
    db.commit()
    db.refresh(order)
    return order