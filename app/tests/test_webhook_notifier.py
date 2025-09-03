from unittest import mock
import uuid
from unittest.mock import MagicMock, patch
from app.webhook.webhook_notifier import WebhookNotifier


@patch("app.webhook.webhook_notifier.SessionLocal")
@patch("app.webhook.webhook_notifier.process_webhook_event")
@patch("app.webhook.webhook_notifier.process_webhook_event_high_priority")
def test_publish_event_low_priority(
    mock_high_priority_task, mock_low_priority_task, mock_session
):
    # Arrange
    notifier = WebhookNotifier()
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    notifier._get_subscriber_count = MagicMock(
        return_value=500000
    )  # High-subscriber account
    notifier._calculate_delay = MagicMock(return_value=10)

    event_type = "test_event"
    user_id = uuid.uuid4()
    data = {"key": "value"}

    with mock_session.return_value as _:
        notifier.publish_event(event_type, user_id, data)

    # Assert
    mock_low_priority_task.apply_async.assert_called_once_with(
        args=[mock.ANY, event_type, user_id, data],
        queue="webhooks",
        countdown=10,
    )
    mock_high_priority_task.apply_async.assert_not_called()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.webhook.webhook_notifier.SessionLocal")
@patch("app.webhook.webhook_notifier.process_webhook_event")
@patch("app.webhook.webhook_notifier.process_webhook_event_high_priority")
def test_publish_event_high_priority(
    mock_high_priority_task, mock_low_priority_task, mock_session
):
    # Arrange
    notifier = WebhookNotifier()
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    notifier._get_subscriber_count = MagicMock(
        return_value=5000
    )  # Low-subscriber account

    event_type = "test_event"
    user_id = uuid.uuid4()
    data = {"key": "value"}

    # Act
    notifier.publish_event(event_type, user_id, data)

    # Assert
    mock_high_priority_task.apply_async.assert_called_once_with(
        args=[mock.ANY, event_type, user_id, data],
        queue="webhooks_priority",
    )
    mock_low_priority_task.apply_async.assert_not_called()
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()
