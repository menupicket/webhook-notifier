from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Any


from app.auth.deps import CurrentUser
from app.db.session import DbSession
from app.webhook.schema import (
    WebhookCreate,
    WebhookResponse,
    WebhookTestResponse,
)
from app.webhook.service import webhook_manager

router = APIRouter(prefix="/webhooks")


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: CurrentUser,
    db: DbSession,
    include_inactive: bool = Query(False),
):
    """List user's webhooks"""
    webhooks = await webhook_manager.list_webhooks(
        db, current_user.id, include_inactive=include_inactive
    )
    return webhooks


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    current_user: CurrentUser,
    db: DbSession,
    webhook: WebhookCreate,
):
    """Create a new webhook"""
    db_webhook = await webhook_manager.create_webhook(db, current_user.id, webhook)
    return db_webhook


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    db: DbSession,
    webhook_id: UUID,
):
    """Get a specific webhook"""
    webhook = await webhook_manager.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
        )
    return webhook


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook_public(
    webhook_id: UUID, db: DbSession, current_user: CurrentUser
):
    await webhook_manager.delete_webhook(db, webhook_id, current_user.id)
    return {"message": "Webhook deleted successfully"}


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    db: DbSession,
    webhook_id: UUID,
):
    """Send a test event to the webhook"""
    result = await webhook_manager.test_webhook(db, webhook_id)
    return result


@router.post("/test", response_model=Any)
async def test_webhook_provider(
    data: dict,
):
    """webhook test endpoint to verify setup"""
    return data
