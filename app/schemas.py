from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal


Money = condecimal(max_digits=12, decimal_places=2)  # тип для денег


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
    price: Money = Field(Decimal("0.00"))
    status: OrderStatus = OrderStatus.new
    comment: Optional[str] = None


class OrderOut(BaseModel):
    id: int
    client_id: int
    title: str
    price: Money
    status: OrderStatus
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderPriceUpdate(BaseModel):
    price: Money = Field(..., ge=Decimal("0.00"))


class OrderSummaryOut(BaseModel):
    order_id: int
    price: Money
    paid_total: Money
    balance: Money


class PaymentCreate(BaseModel):
    order_id: int = Field(..., ge=1)
    amount: Money = Field(..., gt=Decimal("0.00"))


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: Money
    created_at: datetime

    class Config:
        from_attributes = True