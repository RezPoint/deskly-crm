from decimal import Decimal
from typing import Dict
from pydantic import BaseModel

class DashboardSummaryOut(BaseModel):
    total_clients: int
    total_orders: int
    active_orders: int
    total_revenue: Decimal
    total_debt: Decimal
    orders_by_status: Dict[str, int]
    recent_activity: list[Dict[str, str]]
