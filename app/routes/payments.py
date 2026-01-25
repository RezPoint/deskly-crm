from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Payment
from ..schemas import PaymentCreate, PaymentOut

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
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