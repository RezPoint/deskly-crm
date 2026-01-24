from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


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


class OrderStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


class OrderCreate(BaseModel):
    client_id: int
    title: str = Field(..., min_length=1, max_length=200)
    price: float = Field(0, ge=0)
    status: OrderStatus = OrderStatus.new
    comment: Optional[str] = None


class OrderOut(BaseModel):
    id: int
    client_id: int
    title: str
    price: float
    status: OrderStatus
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus