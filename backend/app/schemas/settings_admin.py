from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProviderType, UserRole


class SystemSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    allow_registration: bool
    workspace_root: str
    timezone: str
    review_retention_target: str

    @field_validator("review_retention_target", mode="before")
    @classmethod
    def serialize_retention(cls, value: object) -> str:
        return str(value)


class SystemSettingsUpdate(BaseModel):
    allow_registration: bool
    workspace_root: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    review_retention_target: str = Field(min_length=1)


class ProviderConfigPayload(BaseModel):
    provider_type: ProviderType
    base_url: str = ""
    api_key: str | None = None
    model_name: str = ""
    extra_json: str | dict | None = None
    is_enabled: bool = False

    @field_validator("extra_json", mode="before")
    @classmethod
    def normalize_extra_json(cls, value: object) -> dict:
        if value in (None, ""):
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                raise ValueError("extra_json must decode to an object")
            return parsed
        raise ValueError("extra_json must be a JSON object or JSON string")


class AISettingsPayload(BaseModel):
    providers: list[ProviderConfigPayload]


class AIProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_type: ProviderType
    base_url: str
    api_key: str = ""
    api_key_masked: str = ""
    has_api_key: bool = False
    model_name: str
    extra_json: dict
    is_enabled: bool


class ProviderTestRequest(BaseModel):
    provider_type: ProviderType
    base_url: str = Field(min_length=1)
    api_key: str | None = None
    model_name: str = Field(min_length=1)


class ProviderTestResult(BaseModel):
    status: str
    message: str


class ObsidianSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    vault_path: str
    vault_name: str
    vault_id: str
    obsidian_headless_path: str
    config_dir: str
    device_name: str
    sync_command: str | None = None


class ObsidianSettingsUpdate(BaseModel):
    enabled: bool = False
    vault_path: str = ""
    vault_name: str = ""
    vault_id: str = ""
    obsidian_headless_path: str = "obsidian-headless"
    config_dir: str = ""
    device_name: str = ""
    sync_command: str | None = None


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserActivityRead(BaseModel):
    id: int
    user_id: int
    username: str
    total_watch_seconds: int
    review_count: int
    page_view_count: int = 0
    note_view_count: int = 0
    review_watch_seconds: int = 0
    last_seen_at: datetime | None
    last_activity_at: datetime | None = None
    last_event_type: str | None = None


class LoginEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    event_type: str
    ip_address: str | None
    created_at: datetime


class DatabaseExportResult(BaseModel):
    status: str
    message: str
    path: str
    filename: str
    job_id: int


class DatabaseImportResult(BaseModel):
    status: str
    message: str
    imported: bool
    job_id: int
