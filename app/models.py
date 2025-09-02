from uuid import UUID
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_model import Base, PrimaryKeyUuidMixin


class User(Base, PrimaryKeyUuidMixin):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subscribers = relationship("Subscriber", back_populates="user")
    webhooks = relationship("Webhook", back_populates="user")


class Subscriber(Base, PrimaryKeyUuidMixin):
    __tablename__ = "subscribers"

    email = Column(String, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    status = Column(String, default="active")  # active, unsubscribed, bounced
    source = Column(String)  # shopify, woocommerce, manual, api
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="subscribers")


class Webhook(Base, PrimaryKeyUuidMixin):
    __tablename__ = "webhooks"

    url = Column(String, nullable=False)
    events = Column(JSON, default=list)  # ['subscriber.created', 'subscriber.updated']
    secret = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook")


class WebhookDelivery(Base, PrimaryKeyUuidMixin):
    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[UUID] = mapped_column(ForeignKey("webhooks.id"))
    event_id: Mapped[UUID]
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, delivered, failed
    attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime(timezone=True))
    next_attempt = Column(DateTime(timezone=True))
    response_status = Column(Integer)
    response_body = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    webhook = relationship("Webhook", back_populates="deliveries")


class WebhookEvent(Base, PrimaryKeyUuidMixin):
    __tablename__ = "webhook_events"

    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    data = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
