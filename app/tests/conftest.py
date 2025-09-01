from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]
from testcontainers.redis import RedisContainer  # type: ignore[import-untyped]

from app.core import config
from app.tests.utils import table_metadata

redis = RedisContainer().with_bind_ports(6379, config.REDIS_PORT)
postgres = PostgresContainer(
    image="postgis/postgis:16-3.4-alpine",
    username=config.POSTGRES_USER,
    password=config.POSTGRES_PASSWORD,
    dbname=config.POSTGRES_DB,
).with_bind_ports(5432, config.POSTGRES_PORT)


def pytest_configure():
    # todo: keep containers alive, so we don't wait extra time when running a small amount of tests locally.
    #  see https://github.com/testcontainers/testcontainers-python/issues/109
    redis.start()
    postgres.start()

    engine = create_engine(
        postgres.get_connection_url(), echo=config.SQLALCHEMY_ECHO_SQL
    )
    table_metadata().create_all(engine)


def pytest_unconfigure():
    redis.stop()
    postgres.stop()
