"""sa10 settings and admin module

Revision ID: 0004_sa10_settings_admin
Revises: 0003_sa03_review_artifacts
Create Date: 2026-04-18 09:55:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_sa10_settings_admin"
down_revision: Union[str, None] = "0003_sa03_review_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "obsidian_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vault_path", sa.String(), nullable=False, server_default=""),
        sa.Column("vault_name", sa.String(), nullable=False, server_default=""),
        sa.Column("vault_id", sa.String(), nullable=False, server_default=""),
        sa.Column("obsidian_headless_path", sa.String(), nullable=False, server_default="obsidian-headless"),
        sa.Column("config_dir", sa.String(), nullable=False, server_default=""),
        sa.Column("device_name", sa.String(), nullable=False, server_default=""),
        sa.Column("sync_command", sa.String(), nullable=True),
        sa.Column("extra_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_activity_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total_watch_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_activity_snapshots_user_id", "user_activity_snapshots", ["user_id"], unique=True)

    op.create_table(
        "login_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default="login"),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_login_events_user_id", "login_events", ["user_id"], unique=False)
    op.create_index("ix_login_events_username", "login_events", ["username"], unique=False)
    op.create_index("ix_login_events_created_at", "login_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_login_events_created_at", table_name="login_events")
    op.drop_index("ix_login_events_username", table_name="login_events")
    op.drop_index("ix_login_events_user_id", table_name="login_events")
    op.drop_table("login_events")

    op.drop_index("ix_user_activity_snapshots_user_id", table_name="user_activity_snapshots")
    op.drop_table("user_activity_snapshots")

    op.drop_table("obsidian_settings")
