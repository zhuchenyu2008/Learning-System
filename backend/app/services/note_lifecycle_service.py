from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_artifact import GeneratedArtifact
from app.models.note import Note
from app.services.safe_file_service import SafeFileService


@dataclass
class NoteDeleteResult:
    deleted_note_id: int
    deleted_artifact_id: int | None
    deleted_relative_paths: list[str]


class NoteLifecycleService:
    @staticmethod
    async def delete_note(session: AsyncSession, note_id: int) -> NoteDeleteResult | None:
        note = await session.get(Note, note_id)
        if note is None:
            return None

        deleted_paths = [note.relative_path]
        artifact_result = await session.execute(select(GeneratedArtifact).where(GeneratedArtifact.output_note_id == note.id))
        artifact = artifact_result.scalar_one_or_none()
        deleted_artifact_id = artifact.id if artifact is not None else None

        if artifact is not None:
            await session.delete(artifact)
        await session.delete(note)
        await session.commit()

        for relative_path in deleted_paths:
            SafeFileService.delete_file(Path(relative_path))

        return NoteDeleteResult(
            deleted_note_id=note_id,
            deleted_artifact_id=deleted_artifact_id,
            deleted_relative_paths=deleted_paths,
        )
