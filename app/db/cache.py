from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core import config


def _create_connection_pool():
    return redis.BlockingConnectionPool.from_url(
        config.REDIS_URL, max_connections=70, timeout=10
    )


_connection_pool = _create_connection_pool()


def get_redis():
    return redis.Redis(connection_pool=_connection_pool)


Cache = Annotated[redis.Redis, Depends(get_redis)]
