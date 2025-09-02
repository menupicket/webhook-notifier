# app/schemas.py (additional webhook schemas)
from uuid import UUID
from pydantic import BaseModel, HttpUrl, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("events")
    def validate_events(cls, v):
        if v is not None:
            valid_events = [
                "subscriber.created",
                "subscriber.updated",
                "subscriber.deleted",
                "subscriber.unsubscribed",
                "segment.subscriber_added",
                "segment.subscriber_removed",
            ]
            for event in v:
                if event not in valid_events:
                    raise ValueError(f"Invalid event: {event}")
        return v


class WebhookDeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class WebhookDeliveryResponse(BaseModel):
    id: UUID
    webhook_id: UUID
    event_type: str
    status: WebhookDeliveryStatus
    attempts: int
    last_attempt: Optional[datetime] = None
    next_attempt: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookTestResponse(BaseModel):
    success: bool
    message: str


class WebhookCreate(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None

    @field_validator("events")
    def validate_events(cls, v):
        valid_events = [
            "subscriber.created",
            "subscriber.updated",
            "subscriber.deleted",
        ]
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event: {event}")
        return v

    model_config = ConfigDict(from_attributes=True)


class WebhookResponse(BaseModel):
    id: UUID
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]


class WebhookDeliverySchema(BaseModel):
    webhook_id: UUID
    event_id: UUID
    payload: dict
    status: str
    attempts: int
    last_attempt: Optional[datetime]
    next_attempt: Optional[datetime]
    response_status: Optional[int]
    response_body: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookSchema(BaseModel):
    id: UUID
    url: str
    events: dict

    model_config = ConfigDict(from_attributes=True)
