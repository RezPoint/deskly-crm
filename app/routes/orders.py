from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from datetime import datetime, time

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
from ..activity import log_activity

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _parse_date(value: Optional[str], field: str, is_end: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{field} must be ISO date or datetime")
    if value and len(value) == 10:
        dt = datetime.combine(dt.date(), time.max if is_end else time.min)
    return dt


@router.get("", response_model=List[OrderOut])
def list_orders(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[OrderStatus] = None,
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|price_desc|price_asc)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    start_dt = _parse_date(date_from, "date_from", is_end=False)
    end_dt = _parse_date(date_to, "date_to", is_end=True)
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")

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

    if start_dt:
        stmt = stmt.where(Order.created_at >= start_dt)
    if end_dt:
        stmt = stmt.where(Order.created_at <= end_dt)

    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    o = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if o is None:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@router.delete("/{order_id}", status_code=204)
def delete_order(request: Request, order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    title = order.title
    db.delete(order)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.deleted", "order", order_id, title)


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


@router.get("/summary/total", response_model=OrderSummaryOut)
def orders_summary(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[OrderStatus] = None,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    start_dt = _parse_date(date_from, "date_from", is_end=False)
    end_dt = _parse_date(date_to, "date_to", is_end=True)
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")

    stmt = select(func.coalesce(func.sum(Order.price), 0))
    if client_id is not None:
        stmt = stmt.where(Order.client_id == client_id)
    if status is not None:
        stmt = stmt.where(Order.status == status.value)
    if start_dt:
        stmt = stmt.where(Order.created_at >= start_dt)
    if end_dt:
        stmt = stmt.where(Order.created_at <= end_dt)

    total_price_raw = db.execute(stmt).scalar_one()
    total_price = Decimal(str(total_price_raw))

    paid_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).join(
        Order, Order.id == Payment.order_id
    )
    if client_id is not None:
        paid_stmt = paid_stmt.where(Order.client_id == client_id)
    if status is not None:
        paid_stmt = paid_stmt.where(Order.status == status.value)
    if start_dt:
        paid_stmt = paid_stmt.where(Order.created_at >= start_dt)
    if end_dt:
        paid_stmt = paid_stmt.where(Order.created_at <= end_dt)

    paid_total_raw = db.execute(paid_stmt).scalar_one()
    paid_total = Decimal(str(paid_total_raw))
    balance = total_price - paid_total

    return {
        "order_id": 0,
        "price": total_price,
        "paid_total": paid_total,
        "balance": balance,
    }


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int, payload: OrderStatusUpdate, request: Request, db: Session = Depends(get_db)
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    order.status = payload.status.value
    db.commit()
    db.refresh(order)
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.status_updated", "order", order_id, order.status)
    return order


@router.patch("/{order_id}/price", response_model=OrderOut)
def update_order_price(order_id: int, payload: OrderPriceUpdate, request: Request, db: Session = Depends(get_db)):
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
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.price_updated", "order", order_id, str(order.price))
    return order


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, request: Request, db: Session = Depends(get_db)):
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
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.created", "order", o.id, o.title)
    return o
