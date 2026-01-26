import csv
from io import StringIO
from decimal import Decimal

from datetime import datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Response, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db import get_db
from ..models import Client, Order, Payment

router = APIRouter(prefix="/api/export", tags=["export"])


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


@router.get("/orders.csv")
def export_orders_csv(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    start_dt = _parse_date(date_from, "date_from", is_end=False)
    end_dt = _parse_date(date_to, "date_to", is_end=True)
    if status and status not in {"new", "in_progress", "done", "canceled"}:
        raise HTTPException(status_code=422, detail="status must be one of: new, in_progress, done, canceled")

    # total paid per order
    paid_map = dict(
        db.execute(
            select(Payment.order_id, func.coalesce(func.sum(Payment.amount), 0))
            .group_by(Payment.order_id)
        ).all()
    )

    stmt = select(Order, Client).join(Client, Client.id == Order.client_id)

    if client_id is not None:
        stmt = stmt.where(Order.client_id == client_id)
    if status:
        stmt = stmt.where(Order.status == status)
    if start_dt:
        stmt = stmt.where(Order.created_at >= start_dt)
    if end_dt:
        stmt = stmt.where(Order.created_at <= end_dt)

    stmt = stmt.order_by(Order.id.desc())
    rows = db.execute(stmt).all()

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
            order.id,
            client.id,
            client.name,
            order.title,
            order.status,
            str(price),
            str(paid_total),
            str(balance),
            order.created_at.isoformat() if order.created_at else "",
        ])

    content = buf.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="orders.csv"'},
    )


@router.get("/clients.csv")
def export_clients_csv(db: Session = Depends(get_db)):
    clients = db.execute(select(Client).order_by(Client.id.desc())).scalars().all()

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["client_id", "name", "phone", "telegram", "notes", "created_at"])

    for c in clients:
        writer.writerow([
            c.id,
            c.name,
            c.phone or "",
            c.telegram or "",
            c.notes or "",
            c.created_at.isoformat() if c.created_at else "",
        ])

    content = buf.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="clients.csv"'},
    )
