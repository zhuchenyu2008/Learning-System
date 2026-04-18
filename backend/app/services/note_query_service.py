from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note


class NoteQueryService:
    @staticmethod
    async def list_notes(session: AsyncSession) -> list[Note]:
        result = await session.execute(select(Note).order_by(Note.updated_at.desc(), Note.id.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_note(session: AsyncSession, note_id: int) -> Note | None:
        result = await session.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    @staticmethod
    def build_tree(notes: list[Note]) -> list[dict]:
        root: dict[str, dict] = {}

        for note in notes:
            parts = Path(note.relative_path).parts
            cursor = root
            current_path_parts: list[str] = []
            for index, part in enumerate(parts):
                current_path_parts.append(part)
                is_leaf = index == len(parts) - 1
                node = cursor.setdefault(
                    part,
                    {
                        "name": part,
                        "path": "/".join(current_path_parts),
                        "is_dir": not is_leaf,
                        "children": {},
                        "note_id": note.id if is_leaf else None,
                    },
                )
                if is_leaf:
                    node["is_dir"] = False
                    node["note_id"] = note.id
                cursor = node["children"]

        def serialize(node_map: dict[str, dict]) -> list[dict]:
            serialized = []
            for key in sorted(node_map.keys()):
                node = node_map[key]
                serialized.append(
                    {
                        "name": node["name"],
                        "path": node["path"],
                        "is_dir": node["is_dir"],
                        "note_id": node["note_id"],
                        "children": serialize(node["children"]),
                    }
                )
            return serialized

        return serialize(root)
