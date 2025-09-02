from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.dialects import postgresql

from app.core.config import (
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_SERVER,
    POSTGRES_USER,
)


def compile_pg_statement(statement):
    return str(
        statement.compile(
            compile_kwargs={"literal_binds": True}, dialect=postgresql.dialect()
        )
    )


def table_metadata() -> MetaData:
    from app.db.base_model import Base
    from app.main import app  # noqa: F401 – make sure sqlalchemy models are loaded

    return Base.metadata


def engine_sync() -> Engine:
    return create_engine(
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
