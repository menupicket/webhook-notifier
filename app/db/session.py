import logging
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import AsyncAdaptedQueuePool, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core import config

logger = logging.getLogger(__name__)


async_engine = create_async_engine(
    config.SQLALCHEMY_DATABASE_URI,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    echo=config.SQLALCHEMY_ECHO_SQL,
    pool_size=config.SQLALCHEMY_POOL_SIZE,
    pool_timeout=5,
    max_overflow=config.SQLALCHEMY_POOL_MAX_OVERFLOW,
    connect_args={"server_settings": {"application_name": config.APPLICATION_NAME}},
    # Use LIFO pooling reduces the number of connections used during non-peak periods of use.
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#using-fifo-vs-lifo
    pool_use_lifo=True,
    # Close idle connections after certain interval.
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#setting-pool-recycle
    pool_recycle=config.SQLALCHEMY_POOL_RECYCLE_INTERVAL,
)

# Fast API promotes managing a session using dependencies mechanism, see DbSession.
# However, it is not always practical because it means a connection will be returned to the connection pool
# when a request handling comes to an end.
# So it may be more practical to use the session maker directly without dependencies mechanism.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
)

engine = create_engine(config.SYNC_SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates a session, which uses "commit as you go" style:
    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#commit-as-you-go

    You have to call AsyncSession.commit() in the business logic, the context manager here won't do a commit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.exception(e)
            await session.rollback()
            raise e  # in order to be handled by app's exception handlers
        finally:
            # Close idle in transaction sessions. SQLAlchemy pool behavior: when connection is checked out it
            # issues begin statement. Some queries are executed and connection is kept in transaction until it gets
            # closed. This results in errors on server side:
            #   unexpected EOF on client connection with an open transaction
            #   could not receive data from client: Connection reset by peer
            # Following code will be closing active in transaction connections in the end of the session lifecycle.
            if session and session.is_active:
                await session.close()


DbSession = Annotated[AsyncSession, Depends(get_session)]
