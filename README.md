# Webhook delivery service

## Setup
### Setup development environment
- Install dependencies

      pip install -r requirements.txt

- Start database and Redis

      docker-compose up -d db redis

- Run database migrations

      alembic upgrade head

### Start the API server
- Open a new terminal (1)

      uvicorn app.main:app --reload

### Start Celery workers
- Open a new terminal (2)

      celery -A app.webhook.webhook_notifier.celery_app worker --loglevel=info --queues=webhooks_priority --concurrency=8

- Open a new terminal (3)

      celery -A app.webhook.webhook_notifier.celery_app worker --loglevel=info --queues=webhooks --concurrency=4

### Run tests

    make test

## Testing
