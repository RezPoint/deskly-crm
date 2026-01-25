from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Client, Order, Payment, OrderExtra
from ..schemas import (
    OrderCreate,
    OrderExtraCreate,
    OrderExtraOut,
    OrderOut,
    OrderPriceUpdate,
    OrderStatus,
    OrderStatusUpdate,
    OrderSummaryOut,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _paid_total(db: Session, order_id: int) -> Decimal:
    return db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()


def _extras_total(db: Session, order_id: int) -> Decimal:
    return db.execute(
        select(func.coalesce(func.sum(OrderExtra.amount), 0)).where(OrderExtra.order_id == order_id)
    ).scalar_one()


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


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if o is None:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@router.get("/{order_id}/summary", response_model=OrderSummaryOut)
def order_summary(order_id: int, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total = _paid_total(db, order_id)
    extras_total = _extras_total(db, order_id)

    base_price: Decimal = order.price
    total_price: Decimal = base_price + extras_total
    balance: Decimal = total_price - paid_total

    return {
        "order_id": order.id,
        "base_price": base_price,
        "extras_total": extras_total,
        "total_price": total_price,
        "paid_total": paid_total,
        "balance": balance,
    }


@router.get("/{order_id}/extras", response_model=List[OrderExtraOut])
def list_extras(order_id: int, db: Session = Depends(get_db)):
    exists = db.execute(select(Order.id).where(Order.id == order_id)).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="order not found")

    return db.execute(
        select(OrderExtra).where(OrderExtra.order_id == order_id).order_by(OrderExtra.id.desc())
    ).scalars().all()


@router.post("/{order_id}/extras", response_model=OrderExtraOut)
def add_extra(order_id: int, payload: OrderExtraCreate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    reason = payload.reason.strip() if payload.reason else None
    e = OrderExtra(order_id=order_id, amount=payload.amount, reason=reason)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    client_id = db.execute(select(Client.id).where(Client.id == payload.client_id)).scalar_one_or_none()
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


@router.patch("/{order_id}/price", response_model=OrderOut)
def update_order_price(order_id: int, payload: OrderPriceUpdate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total = _paid_total(db, order_id)
    extras_total = _extras_total(db, order_id)

    new_total_price = payload.price + extras_total
    if new_total_price < paid_total:
        raise HTTPException(status_code=409, detail="new total price is below already paid total")

    order.price = payload.price
    db.commit()
    db.refresh(order)
    return order