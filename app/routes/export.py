import csv
from io import StringIO
from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..db import get_db
from ..models import Client, Order, Payment

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/orders.csv")
def export_orders_csv(db: Session = Depends(get_db)):
    # total paid per order
    paid_map = dict(
        db.execute(
            select(Payment.order_id, func.coalesce(func.sum(Payment.amount), 0))
            .group_by(Payment.order_id)
        ).all()
    )

    rows = db.execute(
        select(Order, Client)
        .join(Client, Client.id == Order.client_id)
        .order_by(Order.id.desc())
    ).all()

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