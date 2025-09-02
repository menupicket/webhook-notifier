# Webhook delivery service

## Setup

### Prerequisites

      - python3
      - docker
      - docker-compose

### Create the virtual environment

      python3 -m venv .venv

### Activate the virtual environment
- On macOS/Linux:

      source .venv/bin/activate

- On Windows:

      .venv\Scripts\activate

### Setup development environment
- Install dependencies

      pip install -r requirements.txt --no-cache-dir

- Start database and Redis

      docker-compose up -d db redis

- Run database migrations

      alembic upgrade head

### Start the API server
- Open a new terminal 1

      uvicorn app.main:app --reload

### Start Celery workers
- Open a new terminal 2

      celery -A app.webhook.webhook_notifier.celery_app worker --loglevel=info --queues=webhooks_priority --concurrency=8

- Open a new terminal 3

      celery -A app.webhook.webhook_notifier.celery_app worker --loglevel=info --queues=webhooks --concurrency=4

### Run tests

    make test

## Testing

### 1. Access API documentation using Swagger UI
- Make sure that the API server was started as in [[1]](#start-the-api-server)
- Access API documentation endpoint: [http://localhost:8000/docs](http://localhost:8000/doc)

### 2. Create a user
- Expand POST [/api/v1/users/](http://localhost:8000/docs#/user/create_user_api_v1_users__post) to create a new user.
- Click `Try it out` and enter request data
- Sample data:

      {
            "email": "user@example.com",
            "is_active": true,
            "is_superuser": false,
            "full_name": "User",
            "password": "password"
      }

### 3. Sign in
- Click `Authorize` and enter the newly created username and password

### 4. Create a webhook
- Access POST [/api/v1/webhooks](http://localhost:8000/docs#/webhook/create_webhook_api_v1_webhooks_post) endpoint to create a new webhook.
- Sample data:

      {
            "url": "https://jsonplaceholder.typicode.com/posts",
            "events": [
                  "subscriber.created"
            ]
      }

### 5. Create a new subscriber
- Get a user id from GET [/api/v1/users](http://localhost:8000/docs#/user/read_users_api_v1_users__get) API, store user's id some where.
- Sample output:

      {
            "data": [
                  {
                        "email": "user@example.com",
                        "is_active": true,
                        "is_superuser": false,
                        "full_name": null,
                        "id": "483c3ea2-5790-4d7f-a0fc-ee6b289cc0de"
                  }
            ],
            "count": 1
      }
- Access POST [/api/v1/subscribers](http://localhost:8000/docs#/subscriber/create_subscriber_api_v1_subscribers_post) to create a new subscriber.
- Sample data:

      {
            "email": "user@example.com",
            "first_name": "User",
            "last_name": "Name",
            "tags": [],
            "custom_fields": {},
            "status": "active",
            "user_id": "483c3ea2-5790-4d7f-a0fc-ee6b289cc0de"
      }
- Note: user_id in subscriber request must match a created user's id

### 6. Check the app and worker consoles to confirm whether the webhook has been sent.
- The app's console:

      2025-09-02 09:15:57 [info     ] Webhook event published        event_id=eb764e16-1541-4963-8bb0-17d1c2db575e event_type=subscriber.created subscriber_count=1 user_id=UUID('483c3ea2-5790-4d7f-a0fc-ee6b289cc0de')
      
      INFO:     127.0.0.1:63774 - "POST /api/v1/subscribers HTTP/1.1" 201 Created

- The worker's console:

      [2025-09-02 09:18:39,838: INFO/MainProcess] Task app.webhook.webhook_notifier.process_webhook_event_high_priority[c96e666c-ff0a-4226-87f4-4f229d84f27c] received
      
      [2025-09-02 09:18:40,769: INFO/ForkPoolWorker-8] HTTP Request: POST https://jsonplaceholder.typicode.com/posts "HTTP/1.1 201 Created"
      
      [2025-09-02 09:18:40,771: WARNING/ForkPoolWorker-8] 2025-09-02 09:18:40 [info     ] Webhook delivered successfully status_code=201 webhook_id=UUID('b5a8e938-a5e8-4d96-afdc-bf9aac5a6fae')
      
      [2025-09-02 09:18:40,794: INFO/ForkPoolWorker-8] Task app.webhook.webhook_notifier.process_webhook_event_high_priority[c96e666c-ff0a-4226-87f4-4f229d84f27c] succeeded in 0.9531270409934223s: None

## Scalability
- To test, benchmark and prove the ability to scale in and out, the `app/tests/gen_subscribers.py` script can be used to generate multiple webhook events.
- Firstly, create multiple worker processes by opening multiple terminal and run high priority queue workers:

      celery -A app.webhook.webhook_notifier.celery_app worker --loglevel=info --queues=webhooks_priority --concurrency=8
- Secondly, modify `num_subscribers` and `user_id` in `gen_subscribers.py` script, for example:

      num_subscribers = 500
      user_id = "483c3ea2-5790-4d7f-a0fc-ee6b289cc0de" # should be the real user_id
- Finally, run the script and watch logs in app and worker consoles. Ideally, the load should be distributed evenly for all workers.

      python app/tests/gen_subscribers.py

## Documents
- Webhook Notifier System Design