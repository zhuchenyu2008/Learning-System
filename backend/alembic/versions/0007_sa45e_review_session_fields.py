"""sa45e review session activity fields

Revision ID: 0007_sa45e_review_session_fields
Revises: 0006_sa12c_knowledgepoint_activity
Create Date: 2026-04-20 13:58:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_sa45e_review_session_fields"
down_revision = "0006_sa12c_knowledgepoint_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_activity_snapshots", sa.Column("active_review_card_id", sa.Integer(), nullable=True))
    op.add_column("user_activity_snapshots", sa.Column("active_review_session_seconds", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("user_activity_snapshots", sa.Column("review_session_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_activity_snapshots", sa.Column("review_session_last_heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_user_activity_snapshots_active_review_card_id"), "user_activity_snapshots", ["active_review_card_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_activity_snapshots_active_review_card_id"), table_name="user_activity_snapshots")
    op.drop_column("user_activity_snapshots", "review_session_last_heartbeat_at")
    op.drop_column("user_activity_snapshots", "review_session_started_at")
    op.drop_column("user_activity_snapshots", "active_review_session_seconds")
    op.drop_column("user_activity_snapshots", "active_review_card_id")
