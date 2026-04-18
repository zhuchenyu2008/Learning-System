from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import JobStatus, JobType, NoteType, SourceFileType


class SourceAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_type: SourceFileType
    checksum: str
    imported_at: datetime = Field(validation_alias="created_at")
    metadata_json: dict


class SourceScanRequest(BaseModel):
    root_path: str | None = None
    recursive: bool = True
    include_hidden: bool = False


class SourceScanResult(BaseModel):
    created: int
    updated: int
    scanned_files: int
    assets: list[SourceAssetRead]


class NoteGenerateRequest(BaseModel):
    source_asset_ids: list[int] = Field(min_length=1)
    note_directory: str | None = None
    force_regenerate: bool = False
    sync_to_obsidian: bool = False


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    relative_path: str
    note_type: NoteType
    content_hash: str
    source_asset_id: int | None
    frontmatter_json: dict
    created_at: datetime
    updated_at: datetime


class NoteDetail(NoteRead):
    content: str


class NoteTreeNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    children: list["NoteTreeNode"] = Field(default_factory=list)
    note_id: int | None = None


class JobLogEntry(BaseModel):
    timestamp: datetime | str
    level: str
    message: str
    celery_task_id: str | None = None
    status: str | None = None
    error_message: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: JobType
    status: JobStatus
    payload_json: dict
    result_json: dict
    logs_json: list[dict[str, Any]]
    celery_task_id: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


NoteTreeNode.model_rebuild()
