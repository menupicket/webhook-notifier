from datetime import datetime
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession as DbSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from typing import Optional

from app.models import Subscriber
from app.subscriber.schema import (
    SubscriberCreate,
    SubscriberStatus,
    SubscriberResponse,
    PaginatedResponse,
)
from app.webhook.webhook_notifier import WebhookNotifier


webhook_notifier = WebhookNotifier()


async def get_subscribers(
    db: DbSession,
    user_id: UUID,
    page: int,
    per_page: int,
    search: Optional[str] = None,
    status: Optional[SubscriberStatus] = None,
) -> PaginatedResponse:
    """
    Fetch subscribers with pagination and filtering.
    """
    # Base query
    query = select(Subscriber).where(Subscriber.user_id == user_id)

    # Apply search filter if provided
    if search:
        query = query.where(Subscriber.email.ilike(f"%{search}%"))

    # Apply status filter if provided
    if status:
        query = query.where(Subscriber.status == status)

    # Count total subscribers
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch paginated subscribers
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    subscribers = result.scalars().all()

    # Convert SQLAlchemy models to Pydantic models
    subscribers_response = [
        SubscriberResponse.from_orm(subscriber) for subscriber in subscribers
    ]

    return PaginatedResponse(
        items=subscribers_response,
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
        has_prev=page > 1,
    )


async def create_new_subscriber(
    db: DbSession, subscriber: SubscriberCreate
) -> Subscriber:
    """
    Create a new subscriber.
    """
    # Check if subscriber already exists
    existing_query = select(Subscriber).where(
        Subscriber.email == subscriber.email, Subscriber.user_id == subscriber.user_id
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscriber with this email already exists",
        )

    # Create new subscriber
    db_subscriber = Subscriber(**subscriber.model_dump(), source="manual")
    db.add(db_subscriber)
    await db.commit()
    await db.refresh(db_subscriber)

    # Trigger webhook event
    webhook_notifier.publish_event(
        "subscriber.created",
        db_subscriber.user_id,
        {
            "subscriber": {
                "id": str(db_subscriber.id),
                "email": db_subscriber.email,
                "first_name": db_subscriber.first_name,
                "last_name": db_subscriber.last_name,
                "status": db_subscriber.status,
                "created_at": db_subscriber.created_at.isoformat()
                if isinstance(db_subscriber.created_at, datetime)
                else None,
            }
        },
    )

    return db_subscriber
