from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from ..schemas.base import APIModel, Money

class ProductCreate(APIModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Money = Field("0.00")
    is_active: bool = True

class ProductUpdate(APIModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Money] = None
    is_active: Optional[bool] = None

class ProductOut(APIModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Money
    is_active: bool
    created_at: datetime
