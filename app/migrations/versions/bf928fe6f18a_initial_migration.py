"""Initial migration

Revision ID: bf928fe6f18a
Revises:
Create Date: 2025-08-29 14:14:10.441873

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = "bf928fe6f18a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            pg.UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String, unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String, index=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # Create subscribers table
    op.create_table(
        "subscribers",
        sa.Column(
            "id",
            pg.UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String, index=True, nullable=False),
        sa.Column("first_name", sa.String),
        sa.Column("last_name", sa.String),
        sa.Column("tags", JSON, default=list),
        sa.Column("custom_fields", JSON, default=dict),
        sa.Column("status", sa.String, default="active"),
        sa.Column("source", sa.String),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("user_id", pg.UUID, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Create webhooks table
    op.create_table(
        "webhooks",
        sa.Column(
            "id",
            pg.UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("events", JSON, default=list),
        sa.Column("secret", sa.String),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("user_id", pg.UUID, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Create webhook_deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column(
            "id",
            pg.UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("status", sa.String, default="pending"),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("last_attempt", sa.DateTime(timezone=True)),
        sa.Column("next_attempt", sa.DateTime(timezone=True)),
        sa.Column("response_status", sa.Integer),
        sa.Column("response_body", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("webhook_id", pg.UUID, nullable=False),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"]),
    )

    # Create webhook_events table
    op.create_table(
        "webhook_events",
        sa.Column(
            "id",
            pg.UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("event_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("data", JSON, nullable=False),
        sa.Column("processed", sa.Boolean, default=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("user_id", pg.UUID, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade():
    # Drop webhook_events table
    op.drop_table("webhook_events")

    # Drop webhook_deliveries table
    op.drop_table("webhook_deliveries")

    # Drop webhooks table
    op.drop_table("webhooks")

    # Drop subscribers table
    op.drop_table("subscribers")

    # Drop users table
    op.drop_table("users")
