import re
from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import Client
from ..schemas.client import ClientCreate
from .activity_service import ActivityService

def validate_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    cleaned = re.sub(r"\s+", " ", phone).strip()
    if not re.match(r"^[+\d\s()\-]{3,25}$", cleaned):
        raise ValueError("Phone can only contain digits, spaces, hyphens, and parentheses, length 3-25")
    return cleaned

def validate_telegram(telegram: Optional[str]) -> Optional[str]:
    if not telegram:
        return None
    cleaned = telegram.strip()
    if not cleaned.startswith("@"):
        cleaned = "@" + cleaned
    if not re.match(r"^@[A-Za-z0-9_]{5,32}$", cleaned):
        raise ValueError("Telegram username must be 5-32 characters long and contain only letters, numbers, and underscores")
    return cleaned

class ClientService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_clients(self, q: Optional[str], limit: int, offset: int, sort: str):
        stmt = select(Client).where(Client.tenant_id == self.tenant_id)
        
        if q:
            s = f"%{q.strip()}%"
            stmt = stmt.where(or_(Client.name.like(s), Client.phone.like(s), Client.telegram.like(s)))

        if sort == "created_asc":
            stmt = stmt.order_by(Client.id.asc())
        elif sort == "name_asc":
            stmt = stmt.order_by(Client.name.asc())
        elif sort == "name_desc":
            stmt = stmt.order_by(Client.name.desc())
        else:
            stmt = stmt.order_by(Client.id.desc())

        return self.db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    def get_client(self, client_id: int):
        client = self.db.execute(
            select(Client).where(Client.id == client_id, Client.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    def create_client(self, data: ClientCreate, current_user_id: Optional[int] = None) -> Client:
        try:
            phone = validate_phone(data.phone)
            telegram = validate_telegram(data.telegram)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        conditions = []
        if phone:
            conditions.append(Client.phone == phone)
        if telegram:
            conditions.append(Client.telegram == telegram)

        if conditions:
            exists = self.db.execute(
                select(Client.id).where(Client.tenant_id == self.tenant_id, or_(*conditions))
            ).scalar_one_or_none()
            if exists:
                raise HTTPException(status_code=409, detail="Client with same phone/telegram already exists")

        c = Client(
            tenant_id=self.tenant_id,
            name=data.name.strip(),
            phone=phone,
            telegram=telegram,
            notes=data.notes.strip() if data.notes else None,
        )
        self.db.add(c)
        try:
            self.db.commit()
            self.db.refresh(c)
            if current_user_id:
                act = ActivityService(self.db, self.tenant_id)
                act.log_action(current_user_id, "client.created", "client", c.id, c.name)
            return c
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Client with same phone/telegram already exists")

    def delete_client(self, client_id: int, current_user_id: Optional[int] = None):
        client = self.get_client(client_id)
        name = client.name
        self.db.delete(client)
        self.db.commit()
        if current_user_id:
            act = ActivityService(self.db, self.tenant_id)
            act.log_action(current_user_id, "client.deleted", "client", client_id, name)
