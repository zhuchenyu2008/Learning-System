from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatResult(BaseModel):
    content: str
    raw_response: dict


class OpenAIEmbeddingResult(BaseModel):
    vectors: list[list[float]]
    model_name: str | None = None
    raw_response: dict | None = None
    usage: dict | None = None


class RetrievalMatch(BaseModel):
    note_id: int
    relative_path: str
    snippet: str
    score: float


class NoteRetrievalResult(BaseModel):
    query_text: str
    matched_note_ids: list[int]
    matched_paths: list[str]
    snippets: list[str]
    similarity_scores: list[float]
    provider_model: str | None = None
    retrieval_context: str
    matches: list[RetrievalMatch] = []


class GeneratedNoteResult(BaseModel):
    title: str
    subject: str
    markdown_body: str
    warnings: list[str] = Field(default_factory=list)
    confidence: float | None = None
    summary: str | None = None
    raw_text: str | None = None


class ProviderHealthResult(BaseModel):
    configured: bool
    provider_type: str
    model_name: str | None = None


class ProviderExtractionResult(BaseModel):
    text: str
    metadata: dict[str, Any]


class ObsidianSyncResult(BaseModel):
    executed: bool
    command: list[str] | None = None
    stdout: str | None = None
    stderr: str | None = None


class FileWriteResult(BaseModel):
    absolute_path: Path
    relative_path: str
    bytes_written: int
