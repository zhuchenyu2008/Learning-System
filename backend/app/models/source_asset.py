from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import SourceFileType


class SourceAsset(TimestampMixin, Base):
    __tablename__ = "source_assets"
    __table_args__ = (UniqueConstraint("file_path", "checksum", name="uq_source_assets_path_checksum"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    file_type: Mapped[SourceFileType] = mapped_column(String(32), nullable=False, index=True)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    notes: Mapped[list["Note"]] = relationship(back_populates="source_asset")
