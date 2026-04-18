from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import get_settings


class SafeFileService:
    @staticmethod
    def get_workspace_root() -> Path:
        settings = get_settings()
        workspace_root = Path(settings.workspace_root).expanduser().resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root

    @staticmethod
    def resolve_workspace_path(relative_path: str | Path) -> Path:
        workspace_root = SafeFileService.get_workspace_root()
        candidate = (workspace_root / Path(relative_path)).resolve()
        if workspace_root != candidate and workspace_root not in candidate.parents:
            raise ValueError("Path escapes workspace root")
        return candidate

    @staticmethod
    def to_relative_path(absolute_path: Path) -> str:
        workspace_root = SafeFileService.get_workspace_root()
        resolved = absolute_path.resolve()
        if workspace_root != resolved and workspace_root not in resolved.parents:
            raise ValueError("Path escapes workspace root")
        return resolved.relative_to(workspace_root).as_posix()

    @staticmethod
    def read_text(relative_path: str | Path, encoding: str = "utf-8") -> str:
        path = SafeFileService.resolve_workspace_path(relative_path)
        return path.read_text(encoding=encoding, errors="ignore")

    @staticmethod
    def read_bytes(relative_path: str | Path) -> bytes:
        path = SafeFileService.resolve_workspace_path(relative_path)
        return path.read_bytes()

    @staticmethod
    def write_text(relative_path: str | Path, content: str, encoding: str = "utf-8") -> Path:
        path = SafeFileService.resolve_workspace_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path

    @staticmethod
    def sha256_for_path(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
