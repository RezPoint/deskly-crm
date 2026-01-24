from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Client

from ..schemas import ClientCreate, ClientOut

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    clients = db.execute(select(Client).order_by(Client.id.desc())).scalars().all()
    return clients


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    c = Client(
        name=payload.name.strip(),
        phone=payload.phone,
        telegram=payload.telegram,
        notes=payload.notes,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c