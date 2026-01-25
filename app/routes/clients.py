from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Client
from ..schemas import ClientCreate, ClientOut

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return db.execute(select(Client).order_by(Client.id.desc())).scalars().all()


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.execute(select(Client).where(Client.id == client_id)).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="client not found")
    return c


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name must not be empty")

    phone = payload.phone.strip() if payload.phone else None
    telegram = payload.telegram.strip() if payload.telegram else None
    notes = payload.notes.strip() if payload.notes else None

    c = Client(
        name=name,
        phone=phone,
        telegram=telegram,
        notes=notes,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c