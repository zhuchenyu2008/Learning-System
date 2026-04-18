from sqlalchemy import Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ReviewCard(TimestampMixin, Base):
    __tablename__ = "review_cards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    knowledge_point_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    state_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    due_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    knowledge_point: Mapped["KnowledgePoint"] = relationship(back_populates="review_cards")
    review_logs: Mapped[list["ReviewLog"]] = relationship(back_populates="review_card", cascade="all, delete-orphan")
