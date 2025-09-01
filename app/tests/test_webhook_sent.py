# tests/test_webhook_integration.py
from unittest.mock import patch, Mock

from app.webhook.webhook_notifier import send_test_webhook
from app.models import Webhook


def test_webhook_sent_success():
    """Test successful webhook delivery"""
    webhook = Webhook(
        id=1,
        url="https://jsonplaceholder.typicode.com/posts",
        secret="test_secret",
        events=["subscriber.created"],
    )

    payload = {
        "event_id": "test_123",
        "event_type": "subscriber.created",
        "data": {"subscriber": {"id": 1, "email": "test@example.com"}},
    }

    success = send_test_webhook(webhook, payload)
    assert success


def test_webhook_sent_failure():
    """Test webhook delivery failure"""
    webhook = Webhook(
        id=1, url="https://httpbin.org/status/500", events=["subscriber.created"]
    )

    payload = {
        "event_id": "test_123",
        "event_type": "subscriber.created",
        "data": {"subscriber": {"id": 1, "email": "test@example.com"}},
    }

    with patch("httpx.Client") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.elapsed.total_seconds.return_value = 0.5

        mock_client.return_value.__aenter__.return_value.post.return_value = (
            mock_response
        )

        success = send_test_webhook(webhook, payload)
        assert not success
