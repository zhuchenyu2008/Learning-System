from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ObsidianSetting(TimestampMixin, Base):
    __tablename__ = "obsidian_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    vault_path: Mapped[str] = mapped_column(nullable=False, default="")
    vault_name: Mapped[str] = mapped_column(nullable=False, default="")
    vault_id: Mapped[str] = mapped_column(nullable=False, default="")
    obsidian_headless_path: Mapped[str] = mapped_column(nullable=False, default="obsidian-headless")
    config_dir: Mapped[str] = mapped_column(nullable=False, default="")
    device_name: Mapped[str] = mapped_column(nullable=False, default="")
    sync_command: Mapped[str | None] = mapped_column(nullable=True)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class UserActivitySnapshot(TimestampMixin, Base):
    __tablename__ = "user_activity_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    total_watch_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page_view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    note_view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_watch_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_review_card_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    active_review_session_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_session_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_session_last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship()
