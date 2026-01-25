from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal

Money = condecimal(max_digits=12, decimal_places=2)


class APIModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},  # Decimal -> number in JSON
    )


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


class OrderStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


class OrderCreate(APIModel):
    client_id: int
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


class OrderStatusUpdate(APIModel):
    status: OrderStatus


class OrderPriceUpdate(APIModel):
    price: Money = Field(..., ge=Decimal("0.00"))


class OrderSummaryOut(APIModel):
    order_id: int
    price: Money
    paid_total: Money
    balance: Money


class PaymentCreate(APIModel):
    order_id: int = Field(..., ge=1)
    amount: Money = Field(..., gt=Decimal("0.00"))


class PaymentOut(APIModel):
    id: int
    order_id: int
    amount: Money
    created_at: datetime