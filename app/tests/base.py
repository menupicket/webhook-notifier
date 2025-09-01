import json
import os
import uuid
from datetime import timedelta
from typing import Any, Dict, List
from unittest import IsolatedAsyncioTestCase

from httpx import ASGITransport, AsyncClient, Client
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.security import create_access_token
from app.db.cache import get_redis
from app.db.base_model import Base
from app.db.session import async_engine
from app.main import app


class BaseTest(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self._basepath = os.path.dirname(os.path.realpath(__file__))
        self.client = AsyncClient(app=app, base_url="http://test")
        await self.init_db()
        self.session = async_sessionmaker(async_engine)()
        return await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await self.drop_db()
        await async_engine.dispose()
        r_client = get_redis()
        await r_client.flushall()
        await r_client.aclose(close_connection_pool=True)
        return await super().asyncTearDown()

    async def init_db(self):
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db(self):
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def _create_record(self, model, **kwargs) -> Any:
        obj = model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.commit()
        self.session.expunge(obj)
        return obj

    async def _create_records(self, model, items: List[Dict[str, Any]]) -> List[Any]:
        objs = list(map(lambda x: model(**x), items))
        self.session.add_all(objs)
        await self.session.flush()
        await self.session.commit()
        self.session.expunge_all()
        return objs

    async def create_session(self, user_id: str | None = None) -> tuple[str, str]:
        """
        Create a session with a valid JWT token and store it in Redis.
        Returns the cookie name and session ID.
        """
        if user_id is None:
            user_id = str(uuid.uuid4())

        # Generate a valid JWT token for the user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(subject=user_id, expires_delta=access_token_expires)

        session_id = f"sid-{user_id}"
        value = json.dumps(
            {
                "user": {
                    "id": str(user_id),
                },
                "token": token,  # Include the token in the session data
            }
        )
        # Store the session in Redis
        await get_redis().set(f"sess:{session_id}", value)
        return "test.connect.sid", session_id


def new_async_client(cookies: list[tuple[str, str]] | None = None) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
        cookies=cookies,
    )


def new_client(cookies: list[tuple[str, str]] | None = None) -> Client:
    return Client(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
        cookies=cookies,
    )
