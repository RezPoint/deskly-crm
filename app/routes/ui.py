from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from ..db import get_db
from ..models import Client, Order, Payment

router = APIRouter(prefix="/ui", tags=["ui"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def money(v) -> str:
    """Красивый вывод денег в шаблонах."""
    if v is None:
        return "0.00"
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    try:
        return f"{Decimal(str(v)):.2f}"
    except Exception:
        return str(v)


templates.env.filters["money"] = money


def _to_decimal(s: str, field_name: str) -> Decimal:
    try:
        d = Decimal(s.replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a number")
    return d


def _as_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _render_orders(
    request: Request,
    db: Session,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    error: str = "",
    status_code: int = 200,
):
    clients = db.execute(select(Client).order_by(Client.name.asc())).scalars().all()

    if sort == "created_asc":
        stmt = select(Order).order_by(Order.id.asc())
    elif sort == "price_desc":
        stmt = select(Order).order_by(Order.price.desc(), Order.id.desc())
    elif sort == "price_asc":
        stmt = select(Order).order_by(Order.price.asc(), Order.id.asc())
    else:
        stmt = select(Order).order_by(Order.id.desc())
    if client_id:
        stmt = stmt.where(Order.client_id == client_id)
    if status:
        stmt = stmt.where(Order.status == status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Order.title.ilike(like)) | (Order.comment.ilike(like)))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    page_size = max(1, min(page_size, 200))
    page = max(1, page)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    orders = db.execute(stmt).scalars().all()
    client_map = {c.id: c for c in clients}
    total_pages = max(1, (total + page_size - 1) // page_size)

    return templates.TemplateResponse(
        request,
        "orders.html",
        {
            "request": request,
            "orders": orders,
            "clients": clients,
            "client_map": client_map,
            "filter_client_id": client_id,
            "filter_status": status or "",
            "filter_q": q or "",
            "filter_sort": sort or "created_desc",
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "error": error,
        },
        status_code=status_code,
    )


@router.get("/clients")
def ui_clients(
    request: Request,
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if sort == "created_asc":
        stmt = select(Client).order_by(Client.id.asc())
    elif sort == "name_asc":
        stmt = select(Client).order_by(Client.name.asc())
    elif sort == "name_desc":
        stmt = select(Client).order_by(Client.name.desc())
    else:
        stmt = select(Client).order_by(Client.id.desc())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (Client.name.like(like))
            | (Client.phone.like(like))
            | (Client.telegram.like(like))
        )
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    page_size = max(1, min(page_size, 200))
    page = max(1, page)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    clients = db.execute(stmt).scalars().all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return templates.TemplateResponse(
        request,
        "clients.html",
        {
            "request": request,
            "clients": clients,
            "q": q or "",
            "filter_sort": sort or "created_desc",
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "error": "",
        },
    )


@router.post("/clients")
def ui_create_client(
    request: Request,
    name: str = Form(...),
    phone: Optional[str] = Form(None),
    telegram: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    name_clean = (name or "").strip()
    if not name_clean:
        return templates.TemplateResponse(
            request,
            "clients.html",
            {
                "request": request,
                "clients": db.execute(select(Client).order_by(Client.id.desc())).scalars().all(),
                "q": "",
                "filter_sort": "created_desc",
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
                "error": "Name must not be empty",
            },
            status_code=422,
        )

    phone_clean = phone.strip() if phone else None
    telegram_clean = telegram.strip() if telegram else None
    notes_clean = notes.strip() if notes else None

    # простая защита от дублей: если совпадает phone ИЛИ telegram -- считаем дубль
    conditions = []
    if phone_clean:
        conditions.append(Client.phone == phone_clean)
    if telegram_clean:
        conditions.append(Client.telegram == telegram_clean)

    if conditions:
        exists = db.execute(select(Client.id).where(or_(*conditions))).scalar_one_or_none()
        if exists is not None:
            return templates.TemplateResponse(
                request,
                "clients.html",
                {
                    "request": request,
                    "clients": db.execute(select(Client).order_by(Client.id.desc())).scalars().all(),
                    "q": "",
                    "filter_sort": "created_desc",
                    "page": 1,
                    "page_size": 50,
                    "total_pages": 1,
                    "error": "Client with same phone/telegram already exists",
                },
                status_code=409,
            )

    c = Client(name=name_clean, phone=phone_clean, telegram=telegram_clean, notes=notes_clean)
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "clients.html",
            {
                "request": request,
                "clients": db.execute(select(Client).order_by(Client.id.desc())).scalars().all(),
                "q": "",
                "filter_sort": "created_desc",
                "page": 1,
                "page_size": 50,
                "total_pages": 1,
                "error": "Client with same phone/telegram already exists",
            },
            status_code=409,
        )

    return RedirectResponse(url="/ui/clients", status_code=303)


@router.post("/clients/{client_id}/delete")
def ui_delete_client(
    request: Request,
    client_id: int,
    db: Session = Depends(get_db),
):
    client = db.execute(select(Client).where(Client.id == client_id)).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")
    db.delete(client)
    db.commit()
    return RedirectResponse(url="/ui/clients", status_code=303)


@router.get("/orders")
def ui_orders(
    request: Request,
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return _render_orders(
        request,
        db,
        client_id=client_id,
        status=status,
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.post("/orders")
def ui_create_order(
    request: Request,
    client_id: int = Form(...),
    title: str = Form(...),
    price: str = Form("0"),
    status: str = Form("new"),
    comment: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    client = db.execute(select(Client).where(Client.id == client_id)).scalar_one_or_none()
    if client is None:
        return _render_orders(
            request,
            db,
            error="Client not found",
            status_code=404,
        )

    title_clean = (title or "").strip()
    if not title_clean:
        return _render_orders(
            request,
            db,
            error="Title must not be empty",
            status_code=422,
        )

    price_dec = _to_decimal(price, "price")
    if price_dec < Decimal("0.00"):
        return _render_orders(
            request,
            db,
            error="Price must be >= 0",
            status_code=422,
        )

    allowed_statuses = {"new", "in_progress", "done", "canceled"}
    if status not in allowed_statuses:
        return _render_orders(
            request,
            db,
            error="Invalid status",
            status_code=422,
        )

    comment_clean = comment.strip() if comment else None

    o = Order(
        client_id=client_id,
        title=title_clean,
        price=price_dec,
        status=status,
        comment=comment_clean,
    )
    db.add(o)
    db.commit()
    db.refresh(o)

    return RedirectResponse(url=f"/ui/orders/{o.id}", status_code=303)


@router.post("/orders/{order_id}/delete")
def ui_delete_order(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    db.delete(order)
    db.commit()
    return RedirectResponse(url="/ui/orders", status_code=303)


@router.get("/orders/{order_id}")
def ui_order_detail(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    client = db.execute(select(Client).where(Client.id == order.client_id)).scalar_one_or_none()

    payments = db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
    ).scalars().all()

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()

    paid_total = _as_decimal(paid_total_raw)
    price = _as_decimal(order.price)
    balance: Decimal = price - paid_total

    return templates.TemplateResponse(
        request,
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "client": client,
            "payments": payments,
            "paid_total": paid_total,
            "balance": balance,
            "error": "",
        },
    )


@router.post("/orders/{order_id}/payments")
def ui_add_payment(
    request: Request,
    order_id: int,
    amount: str = Form(...),
    db: Session = Depends(get_db),
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    amount_dec = _to_decimal(amount, "amount")
    if amount_dec <= Decimal("0.00"):
        raise HTTPException(status_code=422, detail="amount must be > 0")

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()
    paid_total = _as_decimal(paid_total_raw)
    price = _as_decimal(order.price)

    # защита от переплаты
    if paid_total + amount_dec > price:
        payments = db.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        ).scalars().all()
        client = db.execute(select(Client).where(Client.id == order.client_id)).scalar_one_or_none()
        balance = price - paid_total

        return templates.TemplateResponse(
            request,
            "order_detail.html",
            {
                "request": request,
                "order": order,
                "client": client,
                "payments": payments,
                "paid_total": paid_total,
                "balance": balance,
                "error": "Payment exceeds order price (overpay is not allowed).",
            },
            status_code=409,
        )

    p = Payment(order_id=order_id, amount=amount_dec)
    db.add(p)
    db.commit()

    return RedirectResponse(url=f"/ui/orders/{order_id}", status_code=303)


@router.post("/payments/{payment_id}/delete")
def ui_delete_payment(
    request: Request,
    payment_id: int,
    db: Session = Depends(get_db),
):
    payment = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    order_id = payment.order_id
    db.delete(payment)
    db.commit()
    return RedirectResponse(url=f"/ui/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/status")
def ui_update_order_status(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    allowed = {"new", "in_progress", "done", "canceled"}
    if status not in allowed:
        raise HTTPException(status_code=422, detail="invalid status")

    order.status = status
    db.commit()

    return RedirectResponse(url=f"/ui/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/price")
def ui_update_order_price(
    request: Request,
    order_id: int,
    price: str = Form(...),
    db: Session = Depends(get_db),
):
    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    new_price = _to_decimal(price, "price")
    if new_price < Decimal("0.00"):
        raise HTTPException(status_code=422, detail="price must be >= 0")

    paid_total_raw = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
    ).scalar_one()
    paid_total = _as_decimal(paid_total_raw)
    price = _as_decimal(order.price)

    if new_price < paid_total:
        payments = db.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        ).scalars().all()
        client = db.execute(select(Client).where(Client.id == order.client_id)).scalar_one_or_none()
        balance = price - paid_total

        return templates.TemplateResponse(
            request,
            "order_detail.html",
            {
                "request": request,
                "order": order,
                "client": client,
                "payments": payments,
                "paid_total": paid_total,
                "balance": balance,
                "error": "New price cannot be below already paid total.",
            },
            status_code=409,
        )

    order.price = new_price
    db.commit()

    return RedirectResponse(url=f"/ui/orders/{order_id}", status_code=303)
    
    
