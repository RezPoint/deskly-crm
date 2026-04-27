from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship, declared_attr
from ..core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Миксин для добавления времени создания записи."""
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class TenantMixin:
    """Миксин для поддержки Multi-tenancy."""
    @declared_attr
    def tenant_id(cls):
        return Column(Integer, ForeignKey("tenants.id"), nullable=False, default=1, index=True)

class BaseEntity(Base, TimestampMixin, TenantMixin):
    """Базовый класс для всех сущностей CRM."""
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=False, unique=True)
    
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    invites = relationship("Invite", back_populates="tenant", cascade="all, delete-orphan")

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_email_tenant"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, default=1, index=True)
    email = Column(String(200), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="owner")  # владелец/админ/наблюдатель

    tenant = relationship("Tenant", back_populates="users")

class Client(BaseEntity):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone", name="uq_clients_phone_tenant"),
        UniqueConstraint("tenant_id", "telegram", name="uq_clients_telegram_tenant"),
    )

    name = Column(String(120), nullable=False)
    phone = Column(String(50), nullable=True, index=True)
    telegram = Column(String(80), nullable=True, index=True)
    notes = Column(String(1000), nullable=True)

    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")

class Order(BaseEntity):
    __tablename__ = "orders"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(200), nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="new")  # новый/в работе/выполнен/отменен
    comment = Column(String(1000), nullable=True)

    client = relationship("Client", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan")

class OrderItem(BaseEntity):
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    total_price = Column(Numeric(12, 2), nullable=False, default=0)

    order = relationship("Order", back_populates="items")

class Payment(BaseEntity):
    __tablename__ = "payments"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)

    order = relationship("Order", back_populates="payments")

class ActivityLog(BaseEntity):
    __tablename__ = "activity_log"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(Integer, nullable=True)
    message = Column(String(500), nullable=True)

class Reminder(BaseEntity):
    __tablename__ = "reminders"
    __table_args__ = (UniqueConstraint("tenant_id", "entity_type", "entity_id", "due_at", name="uq_reminders_tenant_entity"),)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(30), nullable=True)
    entity_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="pending")  # pending/done/expired

class Invite(Base, TimestampMixin):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(200), nullable=False)
    role = Column(String(30), nullable=False, default="manager")
    token = Column(String(120), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="invites")

class Product(BaseEntity):
    __tablename__ = "products"

    name = Column(String(200), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    is_active = Column(Integer, default=1, nullable=False)  # 1 - active, 0 - inactive (archived)

class Task(BaseEntity):
    __tablename__ = "tasks"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(String(2000), nullable=True)
    status = Column(String(30), nullable=False, default="new")  # new / in_progress / done
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)

    order = relationship("Order", back_populates="tasks")
