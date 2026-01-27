import csv
from io import StringIO
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Client, Order
from ..validators import validate_phone, validate_telegram
from ..activity import log_activity

router = APIRouter(prefix="/api/import", tags=["import"])


def _read_csv(upload: UploadFile) -> list[dict]:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="file must be .csv")
    data = upload.file.read()
    try:
        text = data.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=422, detail="file must be UTF-8 CSV")
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=422, detail="missing CSV header")
    rows = []
    for row in reader:
        if any((v or "").strip() for v in row.values()):
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def _process_clients(rows: list[dict], db: Session) -> tuple[int, list[str]]:
    required = {"name"}
    errors: list[str] = []
    created = 0
    for idx, row in enumerate(rows, start=2):  # header is row 1
        missing = [k for k in required if not row.get(k)]
        if missing:
            errors.append(f"row {idx}: missing {', '.join(missing)}")
            continue
        name = row.get("name", "").strip()
        if not name:
            errors.append(f"row {idx}: name must not be empty")
            continue
        phone = row.get("phone") or None
        telegram = row.get("telegram") or None
        notes = row.get("notes") or None
        try:
            phone = validate_phone(phone)
            telegram = validate_telegram(telegram)
        except ValueError:
            field_errors = []
            if row.get("phone"):
                field_errors.append("invalid phone")
            if row.get("telegram"):
                field_errors.append("invalid telegram")
            message = ", ".join(field_errors) if field_errors else "invalid contact data"
            errors.append(f"row {idx}: {message}")
            continue
        db.add(Client(name=name, phone=phone, telegram=telegram, notes=notes))
        created += 1
    return created, errors


def _process_orders(rows: list[dict], db: Session) -> tuple[int, list[str]]:
    required = {"client_id", "title", "price"}
    allowed_statuses = {"new", "in_progress", "done", "canceled"}
    errors: list[str] = []
    created = 0

    client_ids = {int(r["client_id"]) for r in rows if (r.get("client_id") or "").isdigit()}
    if client_ids:
        existing = set(db.execute(select(Client.id).where(Client.id.in_(client_ids))).scalars().all())
    else:
        existing = set()

    for idx, row in enumerate(rows, start=2):
        missing = [k for k in required if not row.get(k)]
        if missing:
            errors.append(f"row {idx}: missing {', '.join(missing)}")
            continue
        if not row["client_id"].isdigit():
            errors.append(f"row {idx}: client_id must be integer")
            continue
        client_id = int(row["client_id"])
        if client_id not in existing:
            errors.append(f"row {idx}: client_id not found")
            continue
        title = row.get("title", "").strip()
        if not title:
            errors.append(f"row {idx}: title must not be empty")
            continue
        status = (row.get("status") or "new").strip() or "new"
        if status not in allowed_statuses:
            errors.append(f"row {idx}: invalid status")
            continue
        comment = row.get("comment") or None
        try:
            price = Decimal(row.get("price", "0").replace(",", "."))
        except (InvalidOperation, AttributeError):
            errors.append(f"row {idx}: price must be a number")
            continue
        if price < Decimal("0.00"):
            errors.append(f"row {idx}: price must be >= 0")
            continue
        db.add(Order(client_id=client_id, title=title, price=price, status=status, comment=comment))
        created += 1
    return created, errors


@router.post("/clients")
def import_clients(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = _read_csv(file)
    if not rows:
        return {"created": 0}

    created, errors = _process_clients(rows, db)

    if errors:
        db.rollback()
        raise HTTPException(status_code=422, detail=errors)

    if dry_run:
        db.rollback()
        return {"created": created, "dry_run": True}

    db.commit()
    user = getattr(request.state, "user", None)
    if user:
        for _ in range(created):
            log_activity(db, getattr(user, "id", None), "client.created", "client", None, "CSV import")
    return {"created": created}


@router.post("/orders")
def import_orders(
    request: Request,
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
):
    rows = _read_csv(file)
    if not rows:
        return {"created": 0}

    created, errors = _process_orders(rows, db)

    if errors:
        db.rollback()
        raise HTTPException(status_code=422, detail=errors)

    if dry_run:
        db.rollback()
        return {"created": created, "dry_run": True}

    db.commit()
    user = getattr(request.state, "user", None)
    if user:
        for _ in range(created):
            log_activity(db, getattr(user, "id", None), "order.created", "order", None, "CSV import")
    return {"created": created}
