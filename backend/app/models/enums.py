from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    VIEWER = "viewer"


class ProviderType(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    STT = "stt"
    OCR = "ocr"


class SourceFileType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    OTHER = "other"


class NoteType(str, Enum):
    SOURCE_NOTE = "source_note"
    SUMMARY = "summary"
    MINDMAP = "mindmap"
    REVIEW_NOTE = "review_note"


class ArtifactType(str, Enum):
    SUMMARY = "summary"
    MINDMAP = "mindmap"


class ArtifactScopeType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class JobType(str, Enum):
    NOTE_GENERATION = "note_generation"
    SOURCE_SCAN = "source_scan"
    OBSIDIAN_SYNC = "obsidian_sync"
    DATABASE_EXPORT = "database_export"
    DATABASE_IMPORT = "database_import"
    SUMMARY_GENERATION = "summary_generation"
    MINDMAP_GENERATION = "mindmap_generation"
    REVIEW_CARD_GENERATION = "review_card_generation"
    SCHEDULED_REVIEW_MAINTENANCE = "scheduled_review_maintenance"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
