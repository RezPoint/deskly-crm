from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .models import ActivityLog


def log_activity(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
    )
    db.add(entry)
    db.commit()
