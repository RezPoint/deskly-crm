from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import Client

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("")
def list_clients(db: Session = Depends(get_db)):
    clients = db.execute(select(Client).order_by(Client.id.desc())).scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "telegram": c.telegram,
            "notes": c.notes,
            "created_at": c.created_at,
        }
        for c in clients
    ]


@router.post("")
def create_client(payload: dict, db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    c = Client(
        name=name,
        phone=payload.get("phone"),
        telegram=payload.get("telegram"),
        notes=payload.get("notes"),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}