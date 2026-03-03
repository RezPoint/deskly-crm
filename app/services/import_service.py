import csv
import re
from io import StringIO
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Client, Order
from .activity_service import ActivityService

# Quick validators to replace legacy module imports
def validate_phone(value):
    if not value or not str(value).strip(): return None
    return str(value).strip()

def validate_telegram(value):
    if not value or not str(value).strip(): return None
    return str(value).strip()


class ImportService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def process_clients(self, rows: list[dict], current_user_id: int) -> tuple[int, list[str]]:
        required = {"name"}
        errors: list[str] = []
        created = 0
        existing_rows = self.db.execute(
            select(Client.phone, Client.telegram).where(Client.tenant_id == self.tenant_id)
        ).all()
        existing_phones = {row[0] for row in existing_rows if row[0]}
        existing_telegrams = {row[1] for row in existing_rows if row[1]}
        seen_phones: set[str] = set()
        seen_telegrams: set[str] = set()
        
        for idx, row in enumerate(rows, start=2):
            missing = [k for k in required if not row.get(k)]
            if missing:
                errors.append(f"row {idx}: missing {', '.join(missing)}")
                continue
            name = row.get("name", "").strip()
            if not name:
                errors.append(f"row {idx}: name must not be empty")
                continue
                
            phone = validate_phone(row.get("phone"))
            telegram = validate_telegram(row.get("telegram"))
            notes = row.get("notes") or None

            if phone:
                if phone in seen_phones:
                    errors.append(f"row {idx}: duplicate phone in CSV")
                    continue
                if phone in existing_phones:
                    errors.append(f"row {idx}: phone already exists")
                    continue
            if telegram:
                if telegram in seen_telegrams:
                    errors.append(f"row {idx}: duplicate telegram in CSV")
                    continue
                if telegram in existing_telegrams:
                    errors.append(f"row {idx}: telegram already exists")
                    continue
                    
            if phone:
                seen_phones.add(phone)
            if telegram:
                seen_telegrams.add(telegram)
                
            self.db.add(
                Client(
                    tenant_id=self.tenant_id,
                    name=name,
                    phone=phone,
                    telegram=telegram,
                    notes=notes,
                )
            )
            created += 1

        if not errors and created > 0 and current_user_id:
            act_svc = ActivityService(self.db, self.tenant_id)
            for _ in range(created):
                act_svc.log_action(current_user_id, "client.created", "client", message="CSV import")

        return created, errors

    def process_orders(self, rows: list[dict], current_user_id: int) -> tuple[int, list[str]]:
        required = {"client_id", "title", "price"}
        allowed_statuses = {"new", "in_progress", "done", "canceled"}
        errors: list[str] = []
        created = 0

        client_ids = {int(r["client_id"]) for r in rows if (r.get("client_id") or "").isdigit()}
        if client_ids:
            existing = set(
                self.db.execute(
                    select(Client.id).where(
                        Client.id.in_(client_ids), Client.tenant_id == self.tenant_id
                    )
                ).scalars().all()
            )
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
                
            self.db.add(
                Order(
                    tenant_id=self.tenant_id,
                    client_id=client_id,
                    title=title,
                    price=price,
                    status=status,
                    comment=comment,
                )
            )
            created += 1

        if not errors and created > 0 and current_user_id:
            act_svc = ActivityService(self.db, self.tenant_id)
            for _ in range(created):
                act_svc.log_action(current_user_id, "order.created", "order", message="CSV import")

        return created, errors
