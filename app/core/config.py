import os
import secrets
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

API_V1_STR = "/api/v1"
APPLICATION_NAME = "webhook-service"


POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
SQLALCHEMY_DATABASE_URI = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
SYNC_SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

SQLALCHEMY_ECHO_SQL = False
SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE") or 50)
SQLALCHEMY_POOL_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_POOL_MAX_OVERFLOW") or 10)
# Recycle a connection from the pool after 1 hour.
SQLALCHEMY_POOL_RECYCLE_INTERVAL = 3600

REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = os.getenv("REDIS_PORT", "")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"


SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 8 days
