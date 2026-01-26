from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from ..db import get_db
from ..models import Client, Order, Payment
from ..schemas import (
    OrderCreate,
    OrderOut,
    OrderStatus,
    OrderStatusUpdate,
    OrderSummaryOut,
    OrderPriceUpdate,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=List[OrderOut])
def list_orders(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[OrderStatus] = None,
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|price_desc|price_asc)$"),
    db: Session = Depends(get_db),
):
    if sort == "created_asc":
        stmt = select(Order).order_by(Order.id.asc())
    elif sort == "price_desc":
        stmt = select(Order).order_by(Order.price.desc(), Order.id.desc())
    elif sort == "price_asc":
        stmt = select(Order).order_by(Order.price.asc(), Order.id.asc())
    else:
        stmt = select(Order).order_by(Order.id.desc())

    if client_id is not None:
        stmt = stmt.where(Order.client_id == client_id)

    if status is not None:
        stmt = stmt.where(Order.status == status.value)

    if q:
        s = f"%{q.strip()}%"
        stmt = stmt.where(or_(Order.title.ilike(s), Order.comment.ilike(s)))

    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    o = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if o is None:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    db.delete(order)
    db.commit()


@router.get("/{order_id}/summary", response_model=OrderSummaryOut)
def order_summary(order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()

    paid_total = Decimal(str(paid_total_raw))
    price = Decimal(str(order.price))
    balance = price - paid_total

    return {
        "order_id": order.id,
        "price": price,
        "paid_total": paid_total,
        "balance": balance,
    }


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)
):
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

    # нельзя уменьшить цену ниже уже оплаченной суммы
    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()

    paid_total = Decimal(str(paid_total_raw))
    if payload.price < paid_total:
        raise HTTPException(status_code=409, detail="new price is below already paid total")

    order.price = payload.price
    db.commit()
    db.refresh(order)
    return order


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
