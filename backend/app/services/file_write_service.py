from __future__ import annotations

from pathlib import Path

from app.schemas.integrations import FileWriteResult
from app.services.safe_file_service import SafeFileService


class FileWriteService:
    @staticmethod
    def write_markdown(relative_path: str, content: str) -> FileWriteResult:
        path = SafeFileService.write_text(relative_path, content)
        return FileWriteResult(
            absolute_path=path,
            relative_path=SafeFileService.to_relative_path(path),
            bytes_written=len(content.encode("utf-8")),
        )

    @staticmethod
    def ensure_directory(relative_path: str) -> Path:
        path = SafeFileService.resolve_workspace_path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
