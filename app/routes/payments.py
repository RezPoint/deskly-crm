from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Order, OrderExtra, Payment
from ..schemas import PaymentCreate, PaymentOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _paid_total(db: Session, order_id: int) -> Decimal:
    return db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()


def _extras_total(db: Session, order_id: int) -> Decimal:
    return db.execute(
        select(func.coalesce(func.sum(OrderExtra.amount), 0)).where(OrderExtra.order_id == order_id)
    ).scalar_one()


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == payload.order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total = _paid_total(db, payload.order_id)
    extras_total = _extras_total(db, payload.order_id)

    total_price: Decimal = order.price + extras_total

    if paid_total + payload.amount > total_price:
        raise HTTPException(status_code=409, detail="payment would exceed total order price")

    p = Payment(order_id=payload.order_id, amount=payload.amount)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/by-order/{order_id}", response_model=list[PaymentOut])
def list_payments_by_order(order_id: int, db: Session = Depends(get_db)):
    return db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
    ).scalars().all()