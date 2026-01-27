from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from ..db import get_db
from ..models import Client, Order, Payment, ActivityLog, Reminder
from ..activity import log_activity
from ..validators import validate_phone, validate_telegram

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


def format_dt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    try:
        return datetime.fromisoformat(str(v)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(v)


templates.env.filters["dt"] = format_dt


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


def _render_orders(
    request: Request,
    db: Session,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    create_client_id: Optional[int] = None,
    create_title: str = "",
    create_price: str = "0",
    create_status: str = "new",
    create_comment: str = "",
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

    start_dt = _parse_date(date_from, "date_from", is_end=False)
    end_dt = _parse_date(date_to, "date_to", is_end=True)
    if start_dt:
        stmt = stmt.where(Order.created_at >= start_dt)
    if end_dt:
        stmt = stmt.where(Order.created_at <= end_dt)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    page_size = max(1, min(page_size, 200))
    page = max(1, page)
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    orders = db.execute(stmt).scalars().all()
    client_map = {c.id: c for c in clients}
    total_pages = max(1, (total + page_size - 1) // page_size)

    order_ids = [o.id for o in orders]
    paid_map = {}
    totals = {"price": Decimal("0.00"), "paid": Decimal("0.00"), "balance": Decimal("0.00")}
    if order_ids:
        rows = db.execute(
            select(Payment.order_id, func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.order_id.in_(order_ids))
            .group_by(Payment.order_id)
        ).all()
        paid_map = {order_id: _as_decimal(paid) for order_id, paid in rows}

        for o in orders:
            price = _as_decimal(o.price)
            paid = paid_map.get(o.id, Decimal("0.00"))
            totals["price"] += price
            totals["paid"] += paid
            totals["balance"] += price - paid

    summary_params = {}
    if client_id:
        summary_params["client_id"] = client_id
    if status:
        summary_params["status"] = status
    if date_from:
        summary_params["date_from"] = date_from
    if date_to:
        summary_params["date_to"] = date_to
    summary_url = "/api/orders/summary/total"
    if summary_params:
        summary_url = f"{summary_url}?{urlencode(summary_params)}"

    return templates.TemplateResponse(
        request,
        "orders.html",
        {
            "request": request,
            "orders": orders,
            "clients": clients,
            "client_map": client_map,
            "paid_map": paid_map,
            "totals": totals,
            "filter_summary": {
                "price": totals["price"],
                "paid_total": totals["paid"],
                "balance": totals["balance"],
            },
            "summary_url": summary_url,
            "filter_client_id": client_id,
            "filter_status": status or "",
            "filter_q": q or "",
            "filter_sort": sort or "created_desc",
            "filter_date_from": date_from or "",
            "filter_date_to": date_to or "",
            "create_client_id": create_client_id,
            "create_title": create_title,
            "create_price": create_price,
            "create_status": create_status,
            "create_comment": create_comment,
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
            "form_name": "",
            "form_phone": "",
            "form_telegram": "",
            "form_notes": "",
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
                "form_name": name,
                "form_phone": phone or "",
                "form_telegram": telegram or "",
                "form_notes": notes or "",
                "error": "Name must not be empty",
            },
            status_code=422,
        )

    phone_clean = phone.strip() if phone else None
    telegram_clean = telegram.strip() if telegram else None
    notes_clean = notes.strip() if notes else None

    try:
        phone_clean = validate_phone(phone_clean)
        telegram_clean = validate_telegram(telegram_clean)
    except ValueError as exc:
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
                "form_name": name,
                "form_phone": phone or "",
                "form_telegram": telegram or "",
                "form_notes": notes or "",
                "error": str(exc),
            },
            status_code=422,
        )

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
                    "form_name": name,
                    "form_phone": phone or "",
                    "form_telegram": telegram or "",
                    "form_notes": notes or "",
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
                "form_name": name,
                "form_phone": phone or "",
                "form_telegram": telegram or "",
                "form_notes": notes or "",
                "error": "Client with same phone/telegram already exists",
            },
            status_code=409,
        )

    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "client.created", "client", c.id, c.name)
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
    name = client.name
    db.delete(client)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "client.deleted", "client", client_id, name)
    return RedirectResponse(url="/ui/clients", status_code=303)


@router.get("/orders")
def ui_orders(
    request: Request,
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
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
        date_from=date_from,
        date_to=date_to,
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
            create_client_id=client_id,
            create_title=title,
            create_price=price,
            create_status=status,
            create_comment=comment or "",
            error="Client not found",
            status_code=404,
        )

    title_clean = (title or "").strip()
    if not title_clean:
        return _render_orders(
            request,
            db,
            create_client_id=client_id,
            create_title=title,
            create_price=price,
            create_status=status,
            create_comment=comment or "",
            error="Title must not be empty",
            status_code=422,
        )

    price_dec = _to_decimal(price, "price")
    if price_dec < Decimal("0.00"):
        return _render_orders(
            request,
            db,
            create_client_id=client_id,
            create_title=title,
            create_price=price,
            create_status=status,
            create_comment=comment or "",
            error="Price must be >= 0",
            status_code=422,
        )

    allowed_statuses = {"new", "in_progress", "done", "canceled"}
    if status not in allowed_statuses:
        return _render_orders(
            request,
            db,
            create_client_id=client_id,
            create_title=title,
            create_price=price,
            create_status=status,
            create_comment=comment or "",
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
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.created", "order", o.id, o.title)

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
    title = order.title
    db.delete(order)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.deleted", "order", order_id, title)
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
            "payment_amount": "",
            "price_input": f"{price:.2f}",
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
        payments = db.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        ).scalars().all()
        client = db.execute(select(Client).where(Client.id == order.client_id)).scalar_one_or_none()
        paid_total_raw = db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
        ).scalar_one()
        paid_total = _as_decimal(paid_total_raw)
        price = _as_decimal(order.price)
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
                "payment_amount": amount,
                "price_input": f"{price:.2f}",
                "error": "Amount must be > 0",
            },
            status_code=422,
        )

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
                "payment_amount": amount,
                "price_input": f"{price:.2f}",
                "error": "Payment exceeds order price (overpay is not allowed).",
            },
            status_code=409,
        )

    p = Payment(order_id=order_id, amount=amount_dec)
    db.add(p)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "payment.created", "payment", p.id, str(p.amount))

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
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "payment.deleted", "payment", payment_id, str(payment.amount))
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
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.status_updated", "order", order_id, status)

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
        payments = db.execute(
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.id.desc())
        ).scalars().all()
        client = db.execute(select(Client).where(Client.id == order.client_id)).scalar_one_or_none()
        paid_total_raw = db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id)
        ).scalar_one()
        paid_total = _as_decimal(paid_total_raw)
        price = _as_decimal(order.price)
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
                "payment_amount": "",
                "price_input": price,
                "error": "Price must be >= 0",
            },
            status_code=422,
        )

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
                "payment_amount": "",
                "price_input": price,
                "error": "New price cannot be below already paid total.",
            },
            status_code=409,
        )

    order.price = new_price
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "order.price_updated", "order", order_id, str(new_price))

    return RedirectResponse(url=f"/ui/orders/{order_id}", status_code=303)


@router.get("/activity")
def ui_activity(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    logs = db.execute(
        select(ActivityLog).order_by(ActivityLog.id.desc()).limit(limit)
    ).scalars().all()
    return templates.TemplateResponse(
        request,
        "activity.html",
        {"request": request, "logs": logs},
    )


@router.get("/reminders")
def ui_reminders(
    request: Request,
    status: Optional[str] = Query(None),
    overdue: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Reminder).order_by(Reminder.due_at.asc())
    if status in {"open", "done"}:
        stmt = stmt.where(Reminder.status == status)
    if overdue == "1":
        stmt = stmt.where(Reminder.status == "open")
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    reminders = db.execute(stmt).scalars().all()
    return templates.TemplateResponse(
        request,
        "reminders.html",
        {"request": request, "reminders": reminders, "filter_status": status or "", "filter_overdue": overdue or ""},
    )
    
    
