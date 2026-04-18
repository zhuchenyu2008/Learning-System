from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SourceFileType
from app.models.source_asset import SourceAsset
from app.services.file_types import infer_source_file_type
from app.services.safe_file_service import SafeFileService


class SourceScanService:
    @staticmethod
    async def scan_workspace(
        session: AsyncSession,
        root_path: str | None = None,
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> dict:
        scan_root = SafeFileService.resolve_workspace_path(root_path or ".")
        iterator = scan_root.rglob("*") if recursive else scan_root.glob("*")

        scanned_files = 0
        created = 0
        updated = 0
        assets: list[SourceAsset] = []

        for path in iterator:
            if not path.is_file():
                continue
            relative_path = SafeFileService.to_relative_path(path)
            if not include_hidden and any(part.startswith(".") for part in Path(relative_path).parts):
                continue

            scanned_files += 1
            checksum = SafeFileService.sha256_for_path(path)
            file_type = infer_source_file_type(path)
            stat = path.stat()
            metadata = {
                "size_bytes": stat.st_size,
                "suffix": path.suffix.lower(),
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
                session.add(asset)
                created += 1
            else:
                asset.file_type = file_type.value
                asset.checksum = checksum
                asset.metadata_json = metadata
                session.add(asset)
                updated += 1
            assets.append(asset)

        await session.commit()
        for asset in assets:
            await session.refresh(asset)

        return {
            "created": created,
            "updated": updated,
            "scanned_files": scanned_files,
            "assets": assets,
        }
