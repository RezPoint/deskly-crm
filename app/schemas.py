from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal, field_serializer

Money = condecimal(max_digits=12, decimal_places=2)


class APIModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_decimal(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value


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
    note: Optional[str] = Field(None, max_length=500)


class PaymentOut(APIModel):
    id: int
    order_id: int
    amount: Money
    note: Optional[str]
    created_at: datetime


class UserRole(str, Enum):
    owner = "owner"
    admin = "admin"
    viewer = "viewer"


class UserOut(APIModel):
    id: int
    email: str
    role: UserRole
    created_at: datetime


class TenantOut(APIModel):
    id: int
    name: str
    slug: str
    created_at: datetime


class InviteCreate(APIModel):
    email: str
    role: UserRole = UserRole.viewer
    expires_in_days: int = Field(7, ge=1, le=30)


class InviteAccept(APIModel):
    token: str
    password: str


class InviteOut(APIModel):
    id: int
    email: str
    role: UserRole
    token: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
class LoginIn(APIModel):
    email: str
    password: str


class ActivityLogOut(APIModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime


class ReminderStatus(str, Enum):
    open = "open"
    done = "done"


class ReminderCreate(APIModel):
    title: str = Field(..., min_length=1, max_length=200)
    due_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class ReminderUpdate(APIModel):
    status: ReminderStatus


class ReminderOut(APIModel):
    id: int
    title: str
    due_at: datetime
    status: ReminderStatus
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
