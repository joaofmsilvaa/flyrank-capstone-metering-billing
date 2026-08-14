import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base

class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"

class UsageType(str, enum.Enum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("Subscription", back_populates="tenant")
    usage_events = relationship("UsageEvent", back_populates="tenant")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True)
    name = Column(Enum(PlanType), nullable=False, unique=True)
    max_api_calls_per_month = Column(Integer, nullable=False)
    max_tokens_per_month = Column(Integer, nullable=False)

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")

    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("Plan")

class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    usage_type = Column(Enum(UsageType), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    idempotency_key = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    tenant = relationship("Tenant", back_populates="usage_events")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'idempotency_key', name='uq_tenant_idempotency_key'),
    )

class ProcessedWebhook(Base):
    __tablename__ = "processed_webhooks"

    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))