from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Order, Payment
from ..schemas import PaymentCreate, PaymentOut, OrderFinanceOut

router = APIRouter(prefix="/api/orders", tags=["payments"])


@router.post("/{order_id}/payments", response_model=PaymentOut)
def add_payment(order_id: int, payload: PaymentCreate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    p = Payment(order_id=order_id, amount=float(payload.amount))
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{order_id}/payments", response_model=List[PaymentOut])
def list_payments(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    q = select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
    return db.execute(q).scalars().all()


@router.get("/{order_id}/finance", response_model=OrderFinanceOut)
def order_finance(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    q = select(Payment).where(Payment.order_id == order_id)
    payments = db.execute(q).scalars().all()
    paid_total = float(sum(float(p.amount) for p in payments))
    price = float(order.price)
    balance_due = max(0.0, price - paid_total)

    return {
        "order_id": order_id,
        "price": price,
        "paid_total": paid_total,
        "balance_due": balance_due,
    }