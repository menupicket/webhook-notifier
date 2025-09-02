# app/webhook_notifier.py
import uuid
import httpx
import structlog
from typing import Dict, Any
from datetime import datetime
from celery import Celery  # type: ignore
from sqlalchemy import and_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from celery.exceptions import CeleryError  # type: ignore

from app.db.session import SessionLocal
from app.core import config
from sqlalchemy.orm import Session
from app.models import Subscriber, Webhook, WebhookDelivery, WebhookEvent

logger = structlog.get_logger()

# Celery configuration
celery_app = Celery(
    "webhook_notifier",
    broker=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0",
    backend=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_routes={
        "webhook_notifier.process_webhook_event": {"queue": "webhooks"},
        "webhook_notifier.process_webhook_event_high_priority": {
            "queue": "webhooks_priority"
        },
    },
)


class WebhookNotifier:
    def __init__(self):
        self.max_retries = 5
        self.retry_delays = [1, 5, 25, 125, 625]  # Exponential backoff in seconds

    def publish_event(self, event_type: str, user_id: uuid.UUID, data: Dict[str, Any]):
        """Publish webhook event to message queue"""
        event_id = str(uuid.uuid4())

        # Store event in database for tracking
        db = SessionLocal()
        try:
            webhook_event = WebhookEvent(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                data=data,
                processed=False,
            )
            db.add(webhook_event)
            db.commit()

            # Determine priority based on user's subscriber count
            subscriber_count = self._get_subscriber_count(db, user_id)

            if subscriber_count > 10000:  # Whale account
                # Use lower priority queue with rate limiting
                process_webhook_event.apply_async(
                    args=[event_id, event_type, user_id, data],
                    queue="webhooks",
                    countdown=self._calculate_delay(subscriber_count),
                )
            else:
                # Use high priority queue
                process_webhook_event_high_priority.apply_async(
                    args=[event_id, event_type, user_id, data],
                    queue="webhooks_priority",
                )

            logger.info(
                "Webhook event published",
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                subscriber_count=subscriber_count,
            )
            return {"status": "success", "message": "Event published successfully"}
        except SQLAlchemyError as db_error:
            logger.error(
                "Database error occurred while publishing webhook event",
                extra={"event_id": event_id, "error": str(db_error)},
            )
            db.rollback()
            return {
                "status": "error",
                "message": "Failed to store event in the database",
            }
        except CeleryError as queue_error:
            logger.error(
                "Queue error occurred while publishing webhook event",
                extra={"event_id": event_id, "error": str(queue_error)},
            )
            return {
                "status": "error",
                "message": "Failed to enqueue event for processing",
            }
        finally:
            db.close()

    def _get_subscriber_count(self, db: Session, user_id: uuid.UUID) -> int:
        return db.query(Subscriber).filter(Subscriber.user_id == user_id).count()

    def _calculate_delay(self, subscriber_count: int) -> int:
        """Calculate delay for webhook processing based on account size"""
        if subscriber_count > 100000:
            return 30  # 30 second delay for very large accounts
        elif subscriber_count > 50000:
            return 15  # 15 second delay for large accounts
        elif subscriber_count > 10000:
            return 5  # 5 second delay for medium accounts
        return 0


@celery_app.task(bind=True, max_retries=5)
def process_webhook_event(
    self, event_id: str, event_type: str, user_id: uuid.UUID, data: Dict[str, Any]
):
    """Process webhook event with retry mechanism"""
    return _process_webhook_event_impl(self, event_id, event_type, user_id, data)


@celery_app.task(bind=True, max_retries=5)
def process_webhook_event_high_priority(
    self, event_id: str, event_type: str, user_id: uuid.UUID, data: Dict[str, Any]
):
    """Process high priority webhook event"""
    return _process_webhook_event_impl(self, event_id, event_type, user_id, data)


def _process_webhook_event_impl(
    task, event_id: str, event_type: str, user_id: uuid.UUID, data: Dict[str, Any]
):
    """Implementation of webhook event processing"""
    db = SessionLocal()
    try:
        # Get all active webhooks for this user that listen to this event
        webhooks = (
            db.query(Webhook)
            .filter(
                and_(
                    Webhook.user_id == user_id,
                    Webhook.is_active,
                    text("webhooks.events::jsonb @> :event_type"),
                )
            )
            .params(event_type=f'["{event_type}"]')
            .all()
        )

        if not webhooks:
            logger.info(
                "No webhooks found for event",
                event_id=event_id,
                event_type=event_type,
                user_id=str(user_id),
            )
            return

        # Create payload
        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        # Send to each webhook
        for webhook in webhooks:
            try:
                # Ensure that the event processing is idempotent
                # so that retries do not result in duplicate webhook deliveries.
                # For the production system, we should check for the delivery
                # existence before creating a new one.
                # key(webhook.id, event_id)
                delivery = None
                existing_delivery = (
                    db.query(WebhookDelivery)
                    .filter(
                        WebhookDelivery.webhook_id == webhook.id,
                        WebhookDelivery.event_id == event_id,
                    )
                    .first()
                )
                if not existing_delivery:
                    delivery = WebhookDelivery(
                        webhook_id=webhook.id,
                        event_id=event_id,
                        payload=payload,
                        status="pending",
                        attempts=0,
                    )
                    db.add(delivery)
                    db.commit()
                else:
                    if existing_delivery.status == "delivered":
                        logger.info(
                            "Webhook already delivered",
                            webhook_id=webhook.id,
                            event_id=event_id,
                        )
                        continue
                    else:
                        delivery = existing_delivery
                if delivery:
                    # Send HTTP request
                    success = _send_webhook_request(webhook, payload, delivery, db)

                    if not success and task.request.retries < task.max_retries:
                        # Retry with exponential backoff
                        retry_delay = WebhookNotifier().retry_delays[
                            task.request.retries
                        ]
                        raise task.retry(countdown=retry_delay)

            except Exception as e:
                logger.error(
                    "Failed to process webhook delivery",
                    webhook_id=webhook.id,
                    event_id=event_id,
                    error=str(e),
                )
                continue

        # Mark event as processed
        webhook_event = (
            db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
        )
        if webhook_event:
            webhook_event.processed = True  # type: ignore
            db.commit()

    finally:
        db.close()


def _send_webhook_request(
    webhook: Webhook,
    payload: Dict[str, Any],
    delivery: WebhookDelivery,
    db: Session,
) -> bool:
    """Send HTTP POST request to webhook URL"""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Whookfirm-Webhooks/1.0",
        }

        with httpx.Client(timeout=30.0) as client:
            # URL: https://jsonplaceholder.typicode.com/posts
            # EVENT: subscriber.created
            response = client.post(
                webhook.url,  # type: ignore
                json=payload,
                headers=headers,
            )

            # Update delivery record
            delivery.attempts += 1  # type: ignore
            delivery.last_attempt = datetime.utcnow()  # type: ignore
            delivery.response_status = response.status_code  # type: ignore
            delivery.response_body = response.text[:1000]  # type: ignore

            if response.status_code < 400:
                delivery.status = "delivered"  # type: ignore
                logger.info(
                    "Webhook delivered successfully",
                    webhook_id=webhook.id,
                    status_code=response.status_code,
                )
                db.commit()
                return True
            else:
                delivery.status = "failed"  # type: ignore
                logger.warning(
                    "Webhook delivery failed",
                    webhook_id=webhook.id,
                    status_code=response.status_code,
                )
                db.commit()
                return False

    except Exception as e:
        delivery.attempts += 1  # type: ignore
        delivery.last_attempt = datetime.utcnow()  # type: ignore
        delivery.status = "failed"  # type: ignore
        delivery.response_body = str(e)[:1000]  # type: ignore
        db.commit()

        logger.error("Webhook request failed", webhook_id=webhook.id, error=str(e))
        return False


def send_test_webhook(webhook: Webhook, payload: Dict[str, Any]) -> bool:
    """Send a test webhook request"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook.url, json=payload)  # type: ignore

            logger.info(
                "Test webhook sent",
                webhook_id=webhook.id,
                status_code=response.status_code,
                response_time=response.elapsed.total_seconds(),
            )

            return response.status_code < 400

    except Exception as e:
        logger.error("Test webhook failed", webhook_id=webhook.id, error=str(e))
        return False
