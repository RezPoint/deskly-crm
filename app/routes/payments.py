from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db import get_db
from ..models import Payment, Order
from ..schemas import PaymentCreate, PaymentOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    order = db.execute(select(Order).where(Order.id == payload.order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == payload.order_id)
    ).scalar_one()

    paid_total = Decimal(str(paid_total_raw))
    # защита от переплаты (с учетом Decimal)
    price = Decimal(str(order.price))
    if paid_total + payload.amount > price:
        raise HTTPException(status_code=409, detail="payment exceeds order remaining balance")

    p = Payment(order_id=payload.order_id, amount=payload.amount)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/by-order/{order_id}", response_model=list[PaymentOut])
def list_payments_by_order(order_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    order = db.execute(select(Order.id).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    return db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
    ).scalars().all()


@router.delete("/{payment_id}", status_code=204)
def delete_payment(payment_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    payment = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    db.delete(payment)
    db.commit()
