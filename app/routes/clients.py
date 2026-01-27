from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_

from ..db import get_db
from ..models import Client
from ..schemas import ClientCreate, ClientOut
from ..validators import validate_phone, validate_telegram
from ..activity import log_activity

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientOut])
def list_clients(
    request: Request,
    q: Optional[str] = Query(
        None,
        min_length=1,
        max_length=120,
        description="Search by name/phone/telegram",
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_desc", pattern="^(created_desc|created_asc|name_asc|name_desc)$"),
    db: Session = Depends(get_db),
):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)

    if sort == "created_asc":
        stmt = select(Client).order_by(Client.id.asc())
    elif sort == "name_asc":
        stmt = select(Client).order_by(Client.name.asc())
    elif sort == "name_desc":
        stmt = select(Client).order_by(Client.name.desc())
    else:
        stmt = select(Client).order_by(Client.id.desc())

    stmt = stmt.where(Client.tenant_id == tenant_id)
    if q:
        s = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Client.name.like(s),
                Client.phone.like(s),
                Client.telegram.like(s),
            )
        )

    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/{client_id}", response_model=ClientOut)
def get_client(request: Request, client_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    c = db.execute(
        select(Client).where(Client.id == client_id, Client.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="client not found")
    return c


@router.delete("/{client_id}", status_code=204)
def delete_client(request: Request, client_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    c = db.execute(
        select(Client).where(Client.id == client_id, Client.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="client not found")
    name = c.name
    db.delete(c)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "client.deleted",
        "client",
        client_id,
        name,
        tenant_id=tenant_id,
    )


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(getattr(request, "state", None), "user", None)
    tenant_id = getattr(tenant_id, "tenant_id", 1)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name must not be empty")

    phone = payload.phone.strip() if payload.phone else None
    telegram = payload.telegram.strip() if payload.telegram else None
    notes = payload.notes.strip() if payload.notes else None

    try:
        phone = validate_phone(phone)
        telegram = validate_telegram(telegram)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # простая защита от дублей:
    # если совпадает phone или telegram -- считаем, что это уже существующий клиент
    conditions = []
    if phone:
        conditions.append(Client.phone == phone)
    if telegram:
        conditions.append(Client.telegram == telegram)

    if conditions:
        exists = db.execute(
            select(Client.id).where(Client.tenant_id == tenant_id, or_(*conditions))
        ).scalar_one_or_none()
        if exists is not None:
            raise HTTPException(
                status_code=409,
                detail="client with same phone/telegram already exists",
            )

    c = Client(
        tenant_id=tenant_id,
        name=name,
        phone=phone,
        telegram=telegram,
        notes=notes,
    )
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="client with same phone/telegram already exists",
        )
    db.refresh(c)
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "client.created",
        "client",
        c.id,
        f"{c.name}",
        tenant_id=tenant_id,
    )
    return c
