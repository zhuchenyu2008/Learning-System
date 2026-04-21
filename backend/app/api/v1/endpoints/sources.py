from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin
from app.models.source_asset import SourceAsset
from app.models.user import User
from app.schemas.ingestion import SourceAssetRead, SourceScanRequest, SourceScanResult
from app.services.safe_file_service import SafeFileService
from app.services.source_scan_service import SourceScanService
from app.services.source_upload_service import SourceUploadService

router = APIRouter()


@router.post("/upload")
async def upload_source(
    file: Annotated[UploadFile, File(...)],
    upload_dir: Annotated[str | None, Form()] = None,
    _: Annotated[User, Depends(require_admin)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> dict:
    asset = await SourceUploadService.save_upload(session, file, upload_dir=upload_dir)
    return success_response(SourceAssetRead.model_validate(asset).model_dump())


@router.post("/scan")
async def scan_sources(
    payload: SourceScanRequest,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await SourceScanService.scan_workspace(
        session,
        root_path=payload.root_path,
        recursive=payload.recursive,
        include_hidden=payload.include_hidden,
    )
    response = SourceScanResult(
        created=result["created"],
        updated=result["updated"],
        scanned_files=result["scanned_files"],
        assets=[SourceAssetRead.model_validate(asset) for asset in result["assets"]],
    )
    return success_response(response.model_dump())


@router.get("")
async def list_sources(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await session.execute(select(SourceAsset).order_by(SourceAsset.created_at.desc(), SourceAsset.id.desc()))
    assets = [SourceAssetRead.model_validate(asset).model_dump() for asset in result.scalars().all()]
    return success_response(assets)


@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await session.execute(select(SourceAsset).where(SourceAsset.id == source_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Source asset not found")

    file_path = asset.file_path
    await session.delete(asset)
    await session.commit()
    SafeFileService.delete_file(file_path)
    return success_response({"id": source_id})
