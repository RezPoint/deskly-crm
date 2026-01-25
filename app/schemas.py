from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, condecimal, ConfigDict
from decimal import Decimal


# Тип для входящих "денег" (строго 2 знака после запятой)
MoneyIn = condecimal(max_digits=12, decimal_places=2)


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = None
    telegram: Optional[str] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    price: MoneyIn = Field(Decimal("0.00"), ge=Decimal("0.00"))
    status: OrderStatus = OrderStatus.new
    comment: Optional[str] = None


class OrderOut(BaseModel):
    """
    ВАЖНО:
    price отдаём как float, чтобы в JSON было число, а не строка.
    В базе всё равно Decimal.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    title: str
    price: float
    status: OrderStatus
    comment: Optional[str] = None
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderPriceUpdate(BaseModel):
    price: MoneyIn = Field(..., ge=Decimal("0.00"))


class OrderSummaryOut(BaseModel):
    # Тесты ожидают ключи price/paid_total/balance + числа
    order_id: int
    price: float
    paid_total: float
    balance: float


class PaymentCreate(BaseModel):
    order_id: int = Field(..., ge=1)
    amount: MoneyIn = Field(..., gt=Decimal("0.00"))


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: float
    created_at: datetime