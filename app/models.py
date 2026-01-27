from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone", name="uq_clients_phone_tenant"),
        UniqueConstraint("tenant_id", "telegram", name="uq_clients_telegram_tenant"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(50), nullable=True)
    telegram = Column(String(80), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    title = Column(String(200), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="new")  # new/in_progress/done/canceled
    comment = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    client = relationship("Client", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    order = relationship("Order", back_populates="payments")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_email_tenant"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    email = Column(String(200), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="owner")  # owner/admin/viewer
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(Integer, nullable=True)
    message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, default=1, index=True)
    title = Column(String(200), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="open")  # open/done
    entity_type = Column(String(30), nullable=True)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
