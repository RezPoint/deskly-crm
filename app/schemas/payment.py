from datetime import datetime
from pydantic import Field

from ..schemas.base import APIModel, Money

class PaymentCreate(APIModel):
    order_id: int = Field(..., ge=1)
    amount: Money

class PaymentOut(APIModel):
    id: int
    order_id: int
    amount: Money
    created_at: datetime
