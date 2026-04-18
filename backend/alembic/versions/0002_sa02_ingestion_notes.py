"""sa02 ingestion and note generation

Revision ID: 0002_sa02_ingestion_notes
Revises: 0001_backend_foundation
Create Date: 2026-04-18 08:55:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_sa02_ingestion_notes"
down_revision: Union[str, None] = "0001_backend_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("file_path", sa.String(length=2048), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("file_path", "checksum", name="uq_source_assets_path_checksum"),
    )
    op.create_index("ix_source_assets_file_path", "source_assets", ["file_path"], unique=False)
    op.create_index("ix_source_assets_file_type", "source_assets", ["file_type"], unique=False)
    op.create_index("ix_source_assets_checksum", "source_assets", ["checksum"], unique=False)

    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("relative_path", sa.String(length=2048), nullable=False),
        sa.Column("note_type", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("source_asset_id", sa.Integer(), sa.ForeignKey("source_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("frontmatter_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notes_title", "notes", ["title"], unique=False)
    op.create_index("ix_notes_relative_path", "notes", ["relative_path"], unique=True)
    op.create_index("ix_notes_note_type", "notes", ["note_type"], unique=False)
    op.create_index("ix_notes_content_hash", "notes", ["content_hash"], unique=False)
    op.create_index("ix_notes_source_asset_id", "notes", ["source_asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notes_source_asset_id", table_name="notes")
    op.drop_index("ix_notes_content_hash", table_name="notes")
    op.drop_index("ix_notes_note_type", table_name="notes")
    op.drop_index("ix_notes_relative_path", table_name="notes")
    op.drop_index("ix_notes_title", table_name="notes")
    op.drop_table("notes")

    op.drop_index("ix_source_assets_checksum", table_name="source_assets")
    op.drop_index("ix_source_assets_file_type", table_name="source_assets")
    op.drop_index("ix_source_assets_file_path", table_name="source_assets")
    op.drop_table("source_assets")
