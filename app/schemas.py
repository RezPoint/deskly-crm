from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, condecimal

Money = condecimal(max_digits=12, decimal_places=2)


# Базовая конфигурация: ORM + Decimal -> number в JSON
class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: float(v)},
    )


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None


class ClientOut(ORMModel):
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
    price: Money = Field(Decimal("0.00"), ge=Decimal("0.00"))
    status: OrderStatus = OrderStatus.new
    comment: Optional[str] = None


class OrderOut(ORMModel):
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


class OrderSummaryOut(ORMModel):
    order_id: int
    price: Money
    paid_total: Money
    balance: Money


class PaymentCreate(BaseModel):
    order_id: int = Field(..., ge=1)
    amount: Money = Field(..., gt=Decimal("0.00"))


class PaymentOut(ORMModel):
    id: int
    order_id: int
    amount: Money
    created_at: datetime