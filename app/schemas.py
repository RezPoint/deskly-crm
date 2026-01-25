from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal

Money = condecimal(max_digits=12, decimal_places=2)


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClientCreate(BaseModel):
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


class OrderStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


class OrderCreate(BaseModel):
    client_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    price: Money = Field(Decimal("0.00"))
    status: OrderStatus = OrderStatus.new
    comment: Optional[str] = None


class OrderOut(APIModel):
    id: int
    client_id: int
    title: str
    price: Money
    status: OrderStatus
    comment: Optional[str] = None
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderPriceUpdate(BaseModel):
    price: Money = Field(..., ge=Decimal("0.00"))


class PaymentCreate(BaseModel):
    order_id: int = Field(..., ge=1)
    amount: Money = Field(..., gt=Decimal("0.00"))


class PaymentOut(APIModel):
    id: int
    order_id: int
    amount: Money
    created_at: datetime


class OrderExtraCreate(BaseModel):
    amount: Money = Field(..., gt=Decimal("0.00"))
    reason: Optional[str] = Field(None, max_length=300)


class OrderExtraOut(APIModel):
    id: int
    order_id: int
    amount: Money
    reason: Optional[str] = None
    created_at: datetime


class OrderSummaryOut(APIModel):
    order_id: int
    base_price: Money
    extras_total: Money
    total_price: Money
    paid_total: Money
    balance: Money