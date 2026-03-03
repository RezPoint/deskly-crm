from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import Payment, Order
from ..schemas.payment import PaymentCreate

class PaymentService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_by_order(self, order_id: int):
        order = self.db.execute(
            select(Order.id).where(Order.id == order_id, Order.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return self.db.execute(
            select(Payment)
            .where(Payment.order_id == order_id, Payment.tenant_id == self.tenant_id)
            .order_by(Payment.id.desc())
        ).scalars().all()

    def create_payment(self, data: PaymentCreate) -> Payment:
        order = self.db.execute(
            select(Order).where(Order.id == data.order_id, Order.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        paid_raw = self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.order_id == data.order_id, Payment.tenant_id == self.tenant_id)
        ).scalar_one()

        paid = Decimal(str(paid_raw))
        price = Decimal(str(order.price))
        if data.amount <= 0:
            raise HTTPException(status_code=422, detail="Payment amount must be positive")
        if paid + data.amount > price:
            raise HTTPException(status_code=409, detail="Payment exceeds order remaining balance")

        p = Payment(tenant_id=self.tenant_id, order_id=data.order_id, amount=data.amount)
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def delete_payment(self, payment_id: int):
        p = self.db.execute(
            select(Payment).where(Payment.id == payment_id, Payment.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        self.db.delete(p)
        self.db.commit()
