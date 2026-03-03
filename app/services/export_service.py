import csv
from io import StringIO
from decimal import Decimal
from datetime import datetime, time
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models import Client, Order, Payment

class ExportService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def _parse_date(self, value: Optional[str], is_end: bool = False) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=f"Invalid date format: {value}")
        if len(value) == 10:
            dt = datetime.combine(dt.date(), time.max if is_end else time.min)
        return dt

    def generate_orders_csv(
        self,
        client_id: Optional[int],
        status: Optional[str],
        q: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> str:
        start_dt = self._parse_date(date_from, is_end=False)
        end_dt = self._parse_date(date_to, is_end=True)

        paid_map = dict(
            self.db.execute(
                select(Payment.order_id, func.coalesce(func.sum(Payment.amount), 0))
                .where(Payment.tenant_id == self.tenant_id)
                .group_by(Payment.order_id)
            ).all()
        )

        stmt = select(Order, Client).join(Client, Client.id == Order.client_id)
        stmt = stmt.where(Order.tenant_id == self.tenant_id, Client.tenant_id == self.tenant_id)

        if client_id is not None:
            stmt = stmt.where(Order.client_id == client_id)
        if status:
            stmt = stmt.where(Order.status == status)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where((Order.title.ilike(like)) | (Order.comment.ilike(like)))
        if start_dt:
            stmt = stmt.where(Order.created_at >= start_dt)
        if end_dt:
            stmt = stmt.where(Order.created_at <= end_dt)

        stmt = stmt.order_by(Order.id.desc())
        rows = self.db.execute(stmt).all()

        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "order_id", "client_id", "client_name",
            "title", "status", "price", "paid_total", "balance", "created_at"
        ])

        for order, client in rows:
            paid_total = Decimal(str(paid_map.get(order.id, 0)))
            price = Decimal(str(order.price))
            balance = price - paid_total

            writer.writerow([
                order.id, client.id, client.name, order.title, order.status,
                str(price), str(paid_total), str(balance),
                order.created_at.isoformat() if order.created_at else "",
            ])

        return buf.getvalue()

    def generate_clients_csv(self) -> str:
        clients = (
            self.db.execute(
                select(Client).where(Client.tenant_id == self.tenant_id).order_by(Client.id.desc())
            ).scalars().all()
        )

        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["client_id", "name", "phone", "telegram", "notes", "created_at"])

        for c in clients:
            writer.writerow([
                c.id, c.name, c.phone or "", c.telegram or "", c.notes or "",
                c.created_at.isoformat() if c.created_at else "",
            ])

        return buf.getvalue()

    @staticmethod
    def generate_clients_template() -> str:
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["name", "phone", "telegram", "notes"])
        return buf.getvalue()

    @staticmethod
    def generate_orders_template() -> str:
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["client_id", "title", "price", "status", "comment"])
        return buf.getvalue()
