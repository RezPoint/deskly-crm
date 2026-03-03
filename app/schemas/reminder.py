from typing import Optional
from datetime import datetime
from pydantic import Field

from ..schemas.base import APIModel

class ReminderStatus(str):
    open = "open"
    done = "done"

class ReminderCreate(APIModel):
    title: str = Field(..., min_length=1, max_length=200)
    due_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class ReminderUpdate(APIModel):
    status: str

class ReminderOut(APIModel):
    id: int
    title: str
    due_at: datetime
    status: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
