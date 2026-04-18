from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import NoteType


class Note(TimestampMixin, Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    relative_path: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    note_type: Mapped[NoteType] = mapped_column(String(32), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_asset_id: Mapped[int | None] = mapped_column(ForeignKey("source_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    frontmatter_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source_asset: Mapped["SourceAsset | None"] = relationship(back_populates="notes")
    knowledge_points: Mapped[list["KnowledgePoint"]] = relationship(back_populates="note", cascade="all, delete-orphan")
