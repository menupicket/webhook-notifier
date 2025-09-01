from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP


def now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def mark_updated(self):
        self.updated_at = now()


class PrimaryKeyUuidMixin:
    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
    }

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if isinstance(self, TimestampMixin):
            self.mark_updated()
