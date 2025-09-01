from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import structlog
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.webhook.webhook_notifier import WebhookNotifier
import app.auth.user.route as user_route
import app.auth.login.route as login_route
import app.subscriber.route as subscriber_route
import app.webhook.route as webhook_route

# Metrics
REQUEST_COUNT = Counter(
    "requests_total", "Total requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram("request_duration_seconds", "Request duration")

logger = structlog.get_logger()

app = FastAPI(
    title="Whookfirm Subscriber Management API",
    description="API for managing subscribers, integrations, and webhooks",
    version="1.0.0",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Initialize components
webhook_notifier = WebhookNotifier()

# Include routers
app.include_router(subscriber_route.router, prefix="/api/v1", tags=["subscriber"])
app.include_router(user_route.router, prefix="/api/v1", tags=["user"])
app.include_router(login_route.router, prefix="/api/v1", tags=["login"])
app.include_router(webhook_route.router, prefix="/api/v1", tags=["webhook"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
