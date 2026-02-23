from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models import Reminder
from ..schemas.reminder import ReminderCreate, ReminderUpdate
from .activity_service import ActivityService

class ReminderService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.activity_svc = ActivityService(db, tenant_id)

    def list_reminders(
        self,
        status: Optional[str],
        overdue: Optional[bool],
        today: Optional[bool],
        entity_type: Optional[str],
        entity_id: Optional[int],
        limit: int,
        offset: int,
    ):
        stmt = (
            select(Reminder)
            .where(Reminder.tenant_id == self.tenant_id)
            .order_by(Reminder.due_at.asc())
        )
        if status in ("open", "done"):
            stmt = stmt.where(Reminder.status == status)
        if overdue:
            stmt = stmt.where(Reminder.status == "open")
            stmt = stmt.where(Reminder.due_at < datetime.utcnow())
        if today:
            now = datetime.utcnow()
            start = now.date()
            end = datetime.combine(start, datetime.max.time())
            stmt = stmt.where(Reminder.due_at >= datetime.combine(start, datetime.min.time()))
            stmt = stmt.where(Reminder.due_at <= end)
        if entity_type:
            stmt = stmt.where(Reminder.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(Reminder.entity_id == entity_id)
            
        return self.db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    def create_reminder(self, data: ReminderCreate, current_user_id: Optional[int]) -> Reminder:
        r = Reminder(
            tenant_id=self.tenant_id,
            title=data.title.strip(),
            due_at=data.due_at,
            status="open",
            entity_type=data.entity_type,
            entity_id=data.entity_id,
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        
        if current_user_id:
            self.activity_svc.log_action(
                user_id=current_user_id,
                action="reminder.created",
                entity_type="reminder",
                entity_id=r.id,
                message=r.title
            )
        return r

    def update_reminder(self, reminder_id: int, data: ReminderUpdate, current_user_id: Optional[int]) -> Reminder:
        r = self.db.execute(
            select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Reminder not found")
            
        r.status = data.status
        self.db.commit()
        self.db.refresh(r)
        
        if current_user_id:
            self.activity_svc.log_action(
                user_id=current_user_id,
                action="reminder.status_updated",
                entity_type="reminder",
                entity_id=r.id,
                message=r.status
            )
        return r

    def delete_reminder(self, reminder_id: int, current_user_id: Optional[int]):
        r = self.db.execute(
            select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Reminder not found")
            
        title = r.title
        self.db.delete(r)
        self.db.commit()
        
        if current_user_id:
            self.activity_svc.log_action(
                user_id=current_user_id,
                action="reminder.deleted",
                entity_type="reminder",
                entity_id=reminder_id,
                message=title
            )
