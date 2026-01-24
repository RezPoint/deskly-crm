from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True