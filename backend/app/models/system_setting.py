from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SystemSetting(TimestampMixin, Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    allow_registration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    workspace_root: Mapped[str] = mapped_column(String(1024), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    review_retention_target: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
