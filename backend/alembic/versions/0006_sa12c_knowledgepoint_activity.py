"""sa12c knowledgepoint metadata and activity snapshot enrichment

Revision ID: 0006_sa12c_knowledgepoint_activity
Revises: 0005_sa12a_job_runtime_visibility
Create Date: 2026-04-18 11:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_sa12c_knowledgepoint_activity"
down_revision: Union[str, None] = "0005_sa12a_job_runtime_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_points", sa.Column("summary_text", sa.Text(), nullable=True))
    op.add_column("knowledge_points", sa.Column("source_anchor", sa.String(length=255), nullable=True))
    op.create_index("ix_knowledge_points_source_anchor", "knowledge_points", ["source_anchor"], unique=False)

    op.add_column("user_activity_snapshots", sa.Column("page_view_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_activity_snapshots", sa.Column("note_view_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_activity_snapshots", sa.Column("review_watch_seconds", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_activity_snapshots", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_activity_snapshots", sa.Column("last_event_type", sa.String(length=64), nullable=True))
    op.create_index("ix_user_activity_snapshots_last_activity_at", "user_activity_snapshots", ["last_activity_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_activity_snapshots_last_activity_at", table_name="user_activity_snapshots")
    op.drop_column("user_activity_snapshots", "last_event_type")
    op.drop_column("user_activity_snapshots", "last_activity_at")
    op.drop_column("user_activity_snapshots", "review_watch_seconds")
    op.drop_column("user_activity_snapshots", "note_view_count")
    op.drop_column("user_activity_snapshots", "page_view_count")

    op.drop_index("ix_knowledge_points_source_anchor", table_name="knowledge_points")
    op.drop_column("knowledge_points", "source_anchor")
    op.drop_column("knowledge_points", "summary_text")
