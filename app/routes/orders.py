from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db import get_db
from ..models import Client, Order, Payment
from ..schemas import (
    OrderCreate,
    OrderOut,
    OrderStatus,
    OrderStatusUpdate,
    OrderSummaryOut,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=List[OrderOut])
def list_orders(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
):
    q = select(Order).order_by(Order.id.desc())

    if client_id is not None:
        q = q.where(Order.client_id == client_id)

    if status is not None:
        q = q.where(Order.status == status.value)

    return db.execute(q).scalars().all()


@router.get("/{order_id}/summary", response_model=OrderSummaryOut)
def order_summary(order_id: int, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()

    price = float(order.price)
    paid_total_f = float(paid_total)
    balance = price - paid_total_f

    return {
        "order_id": order.id,
        "price": price,
        "paid_total": paid_total_f,
        "balance": balance,
    }


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if o is None:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    client_id = db.execute(
        select(Client.id).where(Client.id == payload.client_id)
    ).scalar_one_or_none()
    if client_id is None:
        raise HTTPException(status_code=404, detail="client not found")

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="title must not be empty")

    comment = payload.comment.strip() if payload.comment else None

    o = Order(
        client_id=payload.client_id,
        title=title,
        price=payload.price,
        status=payload.status.value,
        comment=comment,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    order.status = payload.status.value
    db.commit()
    db.refresh(order)
    return order