from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ArtifactScopeType, ArtifactType


class KnowledgePointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_id: int
    title: str
    content_md: str
    embedding_vector: list[float] | None
    tags_json: dict
    summary_text: str | None = None
    source_anchor: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    knowledge_point_id: int
    state_json: dict
    due_at: datetime
    last_reviewed_at: datetime | None
    suspended: bool
    created_at: datetime
    updated_at: datetime


class ReviewQueueItem(BaseModel):
    card_id: int
    due_at: datetime
    suspended: bool
    knowledge_point: KnowledgePointRead
    note: dict


class ReviewOverview(BaseModel):
    due_today_count: int
    total_cards: int
    recent_review_count: int
    recent_review_seconds: int


class ReviewBootstrapRequest(BaseModel):
    note_ids: list[int] = Field(default_factory=list)
    all_notes: bool = False

    @field_validator("note_ids")
    @classmethod
    def validate_scope(cls, value: list[int]) -> list[int]:
        if any(item <= 0 for item in value):
            raise ValueError("note_ids must contain positive integers")
        return value


class ReviewBootstrapResponse(BaseModel):
    created_knowledge_points: int
    created_cards: int
    note_ids: list[int]


class ReviewGradeRequest(BaseModel):
    rating: int = Field(ge=1, le=4)
    duration_seconds: int = Field(default=0, ge=0)
    note: str | None = None


class ReviewLogCreateRequest(BaseModel):
    review_card_id: int
    rating: int = Field(ge=1, le=4)
    duration_seconds: int = Field(default=0, ge=0)
    note: str | None = None


class ReviewLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    review_card_id: int
    rating: int
    duration_seconds: int
    note: str | None
    created_at: datetime
    updated_at: datetime


class ArtifactGenerateRequest(BaseModel):
    scope: ArtifactScopeType
    note_ids: list[int] = Field(default_factory=list)
    prompt_extra: str | None = None


class ArtifactListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artifact_type: ArtifactType
    scope_type: ArtifactScopeType
    note_ids_json: list[int]
    prompt_extra: str | None
    output_note_id: int | None
    status: str
    created_at: datetime
    updated_at: datetime


class ArtifactGenerateResponse(BaseModel):
    job_id: int
    artifact_id: int
    output_note_id: int
    relative_path: str
    status: str
    celery_task_id: str | None = None
