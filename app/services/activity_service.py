from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import ActivityLog

class ActivityService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_activity(
        self,
        limit: int,
        offset: int,
        user_id: Optional[int],
        entity_type: Optional[str],
        action: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
    ):
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.tenant_id == self.tenant_id)
            .order_by(ActivityLog.id.desc())
        )
        if user_id is not None:
            stmt = stmt.where(ActivityLog.user_id == user_id)
        if entity_type:
            stmt = stmt.where(ActivityLog.entity_type == entity_type)
        if action:
            stmt = stmt.where(ActivityLog.action == action)
        if date_from:
            stmt = stmt.where(ActivityLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(ActivityLog.created_at <= date_to)
            
        return self.db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    def log_action(self, user_id: int, action: str, entity_type: str, entity_id: Optional[int] = None, message: Optional[str] = None):
        """Helper to create an activity record"""
        log = ActivityLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message
        )
        self.db.add(log)
        self.db.commit()
