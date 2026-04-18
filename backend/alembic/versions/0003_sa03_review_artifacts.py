"""sa03 review, artifacts, and scheduler placeholders

Revision ID: 0003_sa03_review_artifacts
Revises: 0002_sa02_ingestion_notes
Create Date: 2026-04-18 09:25:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_sa03_review_artifacts"
down_revision: Union[str, None] = "0002_sa02_ingestion_notes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("note_id", sa.Integer(), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("embedding_vector", sa.JSON(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_points_note_id", "knowledge_points", ["note_id"], unique=False)
    op.create_index("ix_knowledge_points_title", "knowledge_points", ["title"], unique=False)

    op.create_table(
        "review_cards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("knowledge_point_id", sa.Integer(), sa.ForeignKey("knowledge_points.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("knowledge_point_id", name="uq_review_cards_knowledge_point_id"),
    )
    op.create_index("ix_review_cards_knowledge_point_id", "review_cards", ["knowledge_point_id"], unique=True)
    op.create_index("ix_review_cards_due_at", "review_cards", ["due_at"], unique=False)
    op.create_index("ix_review_cards_last_reviewed_at", "review_cards", ["last_reviewed_at"], unique=False)
    op.create_index("ix_review_cards_suspended", "review_cards", ["suspended"], unique=False)

    op.create_table(
        "review_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("review_card_id", sa.Integer(), sa.ForeignKey("review_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_logs_user_id", "review_logs", ["user_id"], unique=False)
    op.create_index("ix_review_logs_review_card_id", "review_logs", ["review_card_id"], unique=False)
    op.create_index("ix_review_logs_rating", "review_logs", ["rating"], unique=False)

    op.create_table(
        "generated_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("note_ids_json", sa.JSON(), nullable=False),
        sa.Column("prompt_extra", sa.Text(), nullable=True),
        sa.Column("output_note_id", sa.Integer(), sa.ForeignKey("notes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_generated_artifacts_artifact_type", "generated_artifacts", ["artifact_type"], unique=False)
    op.create_index("ix_generated_artifacts_scope_type", "generated_artifacts", ["scope_type"], unique=False)
    op.create_index("ix_generated_artifacts_output_note_id", "generated_artifacts", ["output_note_id"], unique=False)
    op.create_index("ix_generated_artifacts_status", "generated_artifacts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generated_artifacts_status", table_name="generated_artifacts")
    op.drop_index("ix_generated_artifacts_output_note_id", table_name="generated_artifacts")
    op.drop_index("ix_generated_artifacts_scope_type", table_name="generated_artifacts")
    op.drop_index("ix_generated_artifacts_artifact_type", table_name="generated_artifacts")
    op.drop_table("generated_artifacts")

    op.drop_index("ix_review_logs_rating", table_name="review_logs")
    op.drop_index("ix_review_logs_review_card_id", table_name="review_logs")
    op.drop_index("ix_review_logs_user_id", table_name="review_logs")
    op.drop_table("review_logs")

    op.drop_index("ix_review_cards_suspended", table_name="review_cards")
    op.drop_index("ix_review_cards_last_reviewed_at", table_name="review_cards")
    op.drop_index("ix_review_cards_due_at", table_name="review_cards")
    op.drop_index("ix_review_cards_knowledge_point_id", table_name="review_cards")
    op.drop_table("review_cards")

    op.drop_index("ix_knowledge_points_title", table_name="knowledge_points")
    op.drop_index("ix_knowledge_points_note_id", table_name="knowledge_points")
    op.drop_table("knowledge_points")
