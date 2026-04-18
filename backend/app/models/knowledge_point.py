from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class KnowledgePoint(TimestampMixin, Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_vector: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    tags_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_anchor: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    note: Mapped["Note"] = relationship(back_populates="knowledge_points")
    review_cards: Mapped[list["ReviewCard"]] = relationship(back_populates="knowledge_point", cascade="all, delete-orphan")
