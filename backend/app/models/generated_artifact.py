from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ArtifactScopeType, ArtifactType


class GeneratedArtifact(TimestampMixin, Base):
    __tablename__ = "generated_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(String(32), nullable=False, index=True)
    scope_type: Mapped[ArtifactScopeType] = mapped_column(String(32), nullable=False, index=True)
    note_ids_json: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    prompt_extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_note_id: Mapped[int | None] = mapped_column(ForeignKey("notes.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed", index=True)

    output_note: Mapped["Note | None"] = relationship()
