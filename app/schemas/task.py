from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from ..schemas.base import APIModel


class TaskCreate(APIModel):
    order_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field("new", pattern="^(new|in_progress|done)$")
    due_date: Optional[datetime] = None


class TaskUpdate(APIModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(new|in_progress|done)$")
    due_date: Optional[datetime] = None
    order_id: Optional[int] = None


class TaskOut(APIModel):
    id: int
    order_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime
    order_title: Optional[str] = None
