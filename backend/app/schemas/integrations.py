from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatResult(BaseModel):
    content: str
    raw_response: dict


class ProviderHealthResult(BaseModel):
    configured: bool
    provider_type: str
    model_name: str | None = None


class ProviderExtractionResult(BaseModel):
    text: str
    metadata: dict


class ObsidianSyncResult(BaseModel):
    executed: bool
    command: list[str] | None = None
    stdout: str | None = None
    stderr: str | None = None


class FileWriteResult(BaseModel):
    absolute_path: Path
    relative_path: str
    bytes_written: int
