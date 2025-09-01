from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Sequence
from datetime import datetime
from enum import Enum


class SubscriberStatus(str, Enum):
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"


class SubscriberBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    status: SubscriberStatus = SubscriberStatus.ACTIVE


class SubscriberCreate(SubscriberBase):
    user_id: UUID


class SubscriberUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    status: Optional[SubscriberStatus] = None


class SubscriberResponse(SubscriberBase):
    id: UUID
    user_id: UUID
    source: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: List[Any] | Sequence[Any]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
