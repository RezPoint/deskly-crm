from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db import get_db
from ..models import Payment, Order
from ..schemas import PaymentCreate, PaymentOut
from ..activity import log_activity

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    order = db.execute(
        select(Order).where(Order.id == payload.order_id, Order.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.order_id == payload.order_id, Payment.tenant_id == tenant_id)
    ).scalar_one()

    paid_total = Decimal(str(paid_total_raw))
    # защита от переплаты (с учетом Decimal)
    price = Decimal(str(order.price))
    if paid_total + payload.amount > price:
        raise HTTPException(status_code=409, detail="payment exceeds order remaining balance")

    p = Payment(
        tenant_id=tenant_id,
        order_id=payload.order_id,
        amount=payload.amount,
        note=(payload.note.strip() if payload.note else None),
    )
    db.add(p)
    prev_status = order.status
    new_paid_total = paid_total + payload.amount
    if order.status != "canceled":
        if new_paid_total >= price:
            order.status = "done"
        else:
            order.status = "in_progress"
    db.commit()
    db.refresh(p)
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "payment.created",
        "payment",
        p.id,
        str(p.amount),
        tenant_id=tenant_id,
    )
    if order.status != prev_status:
        log_activity(
            db,
            getattr(user, "id", None),
            "order.status_updated",
            "order",
            order.id,
            order.status,
            tenant_id=tenant_id,
        )
    return p


@router.get("/by-order/{order_id}", response_model=list[PaymentOut])
def list_payments_by_order(
    request: Request, order_id: int = Path(..., ge=1), db: Session = Depends(get_db)
):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    order = db.execute(
        select(Order.id).where(Order.id == order_id, Order.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    return db.execute(
        select(Payment)
        .where(Payment.order_id == order_id, Payment.tenant_id == tenant_id)
        .order_by(Payment.id.desc())
    ).scalars().all()


@router.delete("/{payment_id}", status_code=204)
def delete_payment(request: Request, payment_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    payment = db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    amount = payment.amount
    order_id = payment.order_id
    db.delete(payment)
    db.commit()
    order = db.execute(
        select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    ).scalar_one_or_none()
    status_changed = False
    if order is not None:
        paid_total_raw = db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.order_id == order_id, Payment.tenant_id == tenant_id)
        ).scalar_one()
        paid_total = Decimal(str(paid_total_raw))
        prev_status = order.status
        if paid_total >= Decimal(str(order.price)):
            order.status = "done"
        elif paid_total == Decimal("0.00"):
            order.status = "new"
        else:
            order.status = "in_progress"
        if order.status != prev_status:
            status_changed = True
            db.commit()
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "payment.deleted",
        "payment",
        payment_id,
        str(amount),
        tenant_id=tenant_id,
    )
    if order is not None and status_changed:
        log_activity(
            db,
            getattr(user, "id", None),
            "order.status_updated",
            "order",
            order_id,
            order.status,
            tenant_id=tenant_id,
        )
