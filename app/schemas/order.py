from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..schemas.base import APIModel, Money
from ..schemas.client import ClientOut
from ..schemas.payment import PaymentOut

class OrderStatus(str):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"

class OrderItemCreate(APIModel):
    title: str = Field(..., min_length=1, max_length=200)
    quantity: Money = Field("1")
    unit_price: Money = Field("0.00")

class OrderItemOut(APIModel):
    id: int
    order_id: int
    title: str
    quantity: Money
    unit_price: Money
    total_price: Money

class OrderCreate(APIModel):
    client_id: int
    title: str = Field(..., min_length=1, max_length=200)
    price: Money = Field("0.00")
    status: str = "new"
    comment: Optional[str] = None
    items: list[OrderItemCreate] = []

class OrderOut(APIModel):
    id: int
    client_id: int
    title: str
    price: Money
    status: str
    comment: Optional[str] = None
    created_at: datetime
    items: list[OrderItemOut] = []

class OrderStatusUpdate(APIModel):
    status: str

class OrderPriceUpdate(APIModel):
    price: Money

class OrderSummaryOut(APIModel):
    order: OrderOut
    client: ClientOut
    balance: Money
    payments: list[PaymentOut]
