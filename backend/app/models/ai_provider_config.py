from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ProviderType


class AIProviderConfig(TimestampMixin, Base):
    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider_type: Mapped[ProviderType] = mapped_column(String(32), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String(2048), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extra_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
