# app/webhooks.py
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import List, Optional, Sequence
import secrets
import string
import structlog

from app.models import Webhook
from app.webhook.schema import WebhookCreate
from app.webhook.webhook_notifier import send_test_webhook

logger = structlog.get_logger()


class WebhookManager:
    def __init__(self):
        self.supported_events = [
            "subscriber.created",
            "subscriber.updated",
            "subscriber.deleted",
            "subscriber.unsubscribed",
            "segment.subscriber_added",
            "segment.subscriber_removed",
        ]
        self.max_webhooks_per_user = 10

    def generate_webhook_secret(self, length: int = 32) -> str:
        """Generate a secure webhook secret"""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def validate_webhook_url(self, url: str) -> bool:
        """Validate webhook URL format and accessibility"""
        import re
        from urllib.parse import urlparse

        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(url):
            return False

        parsed = urlparse(url)
        # Ensure HTTPS for production (allow HTTP for localhost/development)
        if (
            parsed.hostname not in ["localhost", "127.0.0.1"]
            and parsed.scheme != "https"
        ):
            return False

        return True

    def validate_events(self, events: List[str]) -> bool:
        """Validate that all events are supported"""
        return all(event in self.supported_events for event in events)

    async def create_webhook(
        self, db: AsyncSession, user_id: UUID, webhook_data: WebhookCreate
    ) -> Webhook:
        """Create a new webhook"""
        # Check webhook limit
        existing_count_query = await db.execute(
            select(Webhook).filter(Webhook.user_id == user_id, Webhook.is_active)
        )
        existing_count = len(existing_count_query.scalars().all())

        if existing_count >= self.max_webhooks_per_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of webhooks ({self.max_webhooks_per_user}) reached",
            )

        # Validate URL
        if not self.validate_webhook_url(webhook_data.url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook URL format or insecure protocol",
            )

        # Validate events
        if not self.validate_events(webhook_data.events):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid events. Supported events: {', '.join(self.supported_events)}",
            )

        # Check for duplicate URL
        existing_webhook_query = await db.execute(
            select(Webhook).filter(
                and_(
                    Webhook.user_id == user_id,
                    Webhook.url == webhook_data.url,
                    Webhook.is_active,
                )
            )
        )
        existing_webhook = existing_webhook_query.scalars().first()

        if existing_webhook:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A webhook with the same URL already exists",
            )

        # Create and save the new webhook
        new_webhook = Webhook(
            user_id=user_id,
            url=webhook_data.url,
            events=webhook_data.events,
            secret=webhook_data.secret,
            is_active=True,
        )
        db.add(new_webhook)
        await db.commit()
        await db.refresh(new_webhook)

        return new_webhook

    async def get_webhook(
        self, db: AsyncSession, webhook_id: UUID
    ) -> Optional[Webhook]:
        """Get a webhook by ID for a specific user"""
        query = select(Webhook).filter(
            and_(Webhook.id == webhook_id, Webhook.is_active)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def list_webhooks(
        self, db: AsyncSession, user_id: UUID, include_inactive: bool = False
    ) -> Sequence[Webhook]:
        """List all webhooks for a user"""
        query = select(Webhook).filter(Webhook.user_id == user_id)

        if not include_inactive:
            query = query.filter(Webhook.is_active)

        result = await db.execute(query.order_by(Webhook.created_at.desc()))
        return result.scalars().all()

    async def test_webhook(self, db: AsyncSession, webhook_id: UUID) -> dict:
        """Send a test event to the webhook"""

        webhook = await self.get_webhook(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
            )

        # Create test payload
        test_payload = {
            "event_id": f"test_{secrets.token_hex(8)}",
            "event_type": "webhook.test",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "message": "This is a test webhook delivery",
                "webhook_id": str(webhook_id),
            },
        }

        success = send_test_webhook(webhook, test_payload)

        return {
            "success": success,
            "message": "Test webhook sent successfully"
            if success
            else "Test webhook failed",
        }

    async def delete_webhook(
        self, db: AsyncSession, webhook_id: UUID, user_id: UUID
    ) -> bool:
        """Delete (deactivate) a webhook"""
        webhook = await self.get_webhook(db, webhook_id)

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found"
            )

        # Soft delete - mark as inactive
        webhook.is_active = False  # type: ignore
        await db.commit()

        logger.info("Webhook deleted", webhook_id=webhook_id, user_id=user_id)

        return True


webhook_manager = WebhookManager()
