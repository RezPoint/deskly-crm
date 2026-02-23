from typing import Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from decimal import Decimal

from ..models import Client, Order, Payment, ActivityLog

class AnalyticsService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def get_dashboard_summary(self) -> Dict[str, Any]:
        # Clients count
        total_clients = self.db.execute(
            select(func.count(Client.id)).where(Client.tenant_id == self.tenant_id)
        ).scalar() or 0

        # Orders counts
        total_orders = self.db.execute(
            select(func.count(Order.id)).where(Order.tenant_id == self.tenant_id)
        ).scalar() or 0
        
        active_orders = self.db.execute(
            select(func.count(Order.id)).where(
                Order.tenant_id == self.tenant_id,
                Order.status.in_(["new", "in_progress"])
            )
        ).scalar() or 0

        # Revenue and Debt
        total_revenue = self.db.execute(
            select(func.sum(Order.price)).where(
                Order.tenant_id == self.tenant_id,
                Order.status != "canceled"
            )
        ).scalar() or Decimal("0.00")

        total_paid = self.db.execute(
            select(func.sum(Payment.amount)).where(Payment.tenant_id == self.tenant_id)
        ).scalar() or Decimal("0.00")

        total_debt = total_revenue - total_paid
        if total_debt < Decimal("0.00"):
            total_debt = Decimal("0.00")

        # Orders by status distribution
        status_counts = self.db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.tenant_id == self.tenant_id)
            .group_by(Order.status)
        ).all()
        
        orders_by_status = {status: count for status, count in status_counts}
        
        # Recent Activity (Last 5 actions)
        recent_logs = self.db.execute(
            select(ActivityLog.action, ActivityLog.message, ActivityLog.created_at)
            .where(ActivityLog.tenant_id == self.tenant_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(5)
        ).all()

        recent_activity: List[Dict[str, str]] = []
        for log in recent_logs:
            title = "Действие"
            if log.action == "client.created":
                title = "Добавлен клиент"
            elif log.action == "order.created":
                title = "Создан заказ"
            elif log.action == "payment.created":
                title = "Поступил платеж"
                
            recent_activity.append({
                "title": title,
                "message": log.message or "",
                "time": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else ""
            })

        return {
            "total_clients": total_clients,
            "total_orders": total_orders,
            "active_orders": active_orders,
            "total_revenue": total_revenue,
            "total_debt": total_debt,
            "orders_by_status": orders_by_status,
            "recent_activity": recent_activity
        }
