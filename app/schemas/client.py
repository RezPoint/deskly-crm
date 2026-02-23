from typing import Optional
from datetime import datetime
from pydantic import Field

from ..schemas.base import APIModel

class ClientCreate(APIModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None

class ClientOut(APIModel):
    id: int
    name: str
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
