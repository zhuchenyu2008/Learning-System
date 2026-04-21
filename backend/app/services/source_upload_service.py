from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_asset import SourceAsset
from app.schemas.ingestion import SourceAssetRead
from app.services.file_types import infer_source_file_type
from app.services.safe_file_service import SafeFileService


UPLOAD_CHUNK_SIZE = 1024 * 1024


class SourceUploadService:
    DEFAULT_UPLOAD_DIR = "uploads/sources"

    @staticmethod
    async def save_upload(session: AsyncSession, upload: UploadFile, upload_dir: str | None = None) -> SourceAsset:
        original_name = Path(upload.filename or "upload.bin").name or "upload.bin"
        relative_path = SourceUploadService._build_relative_path(original_name, upload_dir)

        try:
            absolute_path = SafeFileService.resolve_workspace_path(relative_path)
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            with absolute_path.open("wb") as file_obj:
                while True:
                    chunk = await upload.read(UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    file_obj.write(chunk)
        finally:
            await upload.close()

        checksum = SafeFileService.sha256_for_path(absolute_path)
        file_type = infer_source_file_type(absolute_path)
        metadata = {
            "size_bytes": absolute_path.stat().st_size,
            "suffix": absolute_path.suffix.lower(),
            "original_name": original_name,
            "upload_dir": (upload_dir or SourceUploadService.DEFAULT_UPLOAD_DIR).strip("/"),
        }

        result = await session.execute(select(SourceAsset).where(SourceAsset.file_path == relative_path))
        asset = result.scalar_one_or_none()
        if asset is None:
            asset = SourceAsset(
                file_path=relative_path,
                file_type=file_type.value,
                checksum=checksum,
                metadata_json=metadata,
            )
        else:
            asset.file_type = file_type.value
            asset.checksum = checksum
            asset.metadata_json = metadata

        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

    @staticmethod
    def build_response(asset: SourceAsset) -> SourceAssetRead:
        return SourceAssetRead.model_validate(asset)

    @staticmethod
    def _build_relative_path(original_name: str, upload_dir: str | None) -> str:
        target_dir = (upload_dir or SourceUploadService.DEFAULT_UPLOAD_DIR).strip("/") or SourceUploadService.DEFAULT_UPLOAD_DIR
        sanitized_name = Path(original_name).name.replace("/", "_").replace("\\", "_")
        stem = Path(sanitized_name).stem or "upload"
        suffix = Path(sanitized_name).suffix.lower()
        unique_name = f"{stem}-{uuid4().hex[:12]}{suffix}"
        return f"{target_dir}/{unique_name}"
