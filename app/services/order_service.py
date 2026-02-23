from decimal import Decimal
from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, time

from ..models import Order, Payment, Client
from ..schemas.order import OrderCreate, OrderStatusUpdate, OrderPriceUpdate

def _parse_date(value: Optional[str], is_end: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="Date must be ISO format")
    if len(value) == 10:
        dt = datetime.combine(dt.date(), time.max if is_end else time.min)
    return dt

class OrderService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_orders(self, client_id: Optional[int], status: Optional[str], q: Optional[str],
                    limit: int, offset: int, sort: str, date_from: Optional[str], date_to: Optional[str]):
        start_dt = _parse_date(date_from, is_end=False)
        end_dt = _parse_date(date_to, is_end=True)
        if start_dt and end_dt and start_dt > end_dt:
            raise HTTPException(status_code=422, detail="date_from must be <= date_to")

        stmt = select(Order).where(Order.tenant_id == self.tenant_id)
        
        if client_id:
            stmt = stmt.where(Order.client_id == client_id)
        if status:
            stmt = stmt.where(Order.status == status)
        if q:
            s = f"%{q.strip()}%"
            stmt = stmt.where(or_(Order.title.ilike(s), Order.comment.ilike(s)))
        if start_dt:
            stmt = stmt.where(Order.created_at >= start_dt)
        if end_dt:
            stmt = stmt.where(Order.created_at <= end_dt)

        if sort == "created_asc":
            stmt = stmt.order_by(Order.id.asc())
        elif sort == "price_desc":
            stmt = stmt.order_by(Order.price.desc(), Order.id.desc())
        elif sort == "price_asc":
            stmt = stmt.order_by(Order.price.asc(), Order.id.asc())
        else:
            stmt = stmt.order_by(Order.id.desc())

        return self.db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    def get_order(self, order_id: int):
        o = self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not o:
            raise HTTPException(status_code=404, detail="Order not found")
        return o

    def create_order(self, data: OrderCreate) -> Order:
        client = self.db.execute(
            select(Client.id).where(Client.id == data.client_id, Client.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        o = Order(
            tenant_id=self.tenant_id,
            client_id=data.client_id,
            title=data.title.strip(),
            price=data.price,
            status=data.status,
            comment=data.comment.strip() if data.comment else None,
        )
        self.db.add(o)
        self.db.commit()
        self.db.refresh(o)
        return o

    def delete_order(self, order_id: int):
        o = self.get_order(order_id)
        self.db.delete(o)
        self.db.commit()

    def get_summary(self, order_id: int):
        o = self.get_order(order_id)
        paid_raw = self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.order_id == order_id, Payment.tenant_id == self.tenant_id)
        ).scalar_one()

        paid = Decimal(str(paid_raw))
        price = Decimal(str(o.price))
        
        return {
            "order_id": o.id,
            "price": price,
            "paid_total": paid,
            "balance": price - paid,
        }

    def update_status(self, order_id: int, status: str):
        o = self.get_order(order_id)
        o.status = status
        self.db.commit()
        self.db.refresh(o)
        return o

    def update_price(self, order_id: int, price: Decimal):
        o = self.get_order(order_id)
        paid_raw = self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.order_id == order_id, Payment.tenant_id == self.tenant_id)
        ).scalar_one()

        paid = Decimal(str(paid_raw))
        if price < paid:
            raise HTTPException(status_code=409, detail="New price is below already paid total")
            
        o.price = price
        self.db.commit()
        self.db.refresh(o)
        return o
