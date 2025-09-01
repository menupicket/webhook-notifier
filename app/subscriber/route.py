from fastapi import APIRouter, Query
from typing import Optional

from app.auth.deps import CurrentUser
from app.db.session import DbSession
from app.subscriber.service import create_new_subscriber, get_subscribers
from app.subscriber.schema import (
    PaginatedResponse,
    SubscriberCreate,
    SubscriberResponse,
    SubscriberStatus,
)


router = APIRouter()


@router.get("/subscribers", response_model=PaginatedResponse)
async def list_subscribers(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[SubscriberStatus] = None,
):
    """List subscribers with pagination and filtering"""
    return await get_subscribers(
        db=db,
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        search=search,
        status=status,
    )


@router.post("/subscribers", response_model=SubscriberResponse, status_code=201)
async def create_subscriber(
    db: DbSession,
    subscriber: SubscriberCreate,
):
    """Create a new subscriber"""
    return await create_new_subscriber(db, subscriber)
