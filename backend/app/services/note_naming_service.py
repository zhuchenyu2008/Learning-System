from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.services.safe_file_service import SafeFileService


@dataclass(frozen=True)
class ResolvedNoteNaming:
    subject: str
    subject_slug: str
    base_title: str
    final_title: str
    relative_path: str


class NoteNamingService:
    DEFAULT_SUBJECT = "未分类"
    DEFAULT_BASE_DIR = "notes/subjects"
    MAX_TITLE_LENGTH = 80
    SUBJECT_ALIASES: dict[str, tuple[str, ...]] = {
        "语文": ("语文", "中文", "汉语", "语文学习"),
        "数学": ("数学", "高中数学", "初中数学", "高等数学", "线性代数", "概率论", "微积分", "mathematics", "math"),
        "英语": ("英语", "英文", "english"),
        "物理": ("物理", "高中物理", "大学物理", "physics"),
        "化学": ("化学", "高中化学", "chemistry"),
        "生物": ("生物", "高中生物", "biology"),
        "历史": ("历史", "history"),
        "地理": ("地理", "geography"),
        "政治": ("政治", "思想政治", "道德与法治", "politics"),
        "计算机": (
            "计算机",
            "编程",
            "程序设计",
            "软件工程",
            "计算机科学",
            "人工智能",
            "机器学习",
            "深度学习",
            "cs",
            "computer science",
            "programming",
        ),
        "通识": ("通识", "综合", "general", "general knowledge"),
        "未分类": ("未分类", "其它", "其他", "未知", "unknown", "misc", "miscellaneous", "uncategorized"),
    }
    SUBJECT_SLUGS: dict[str, str] = {
        "语文": "chinese",
        "数学": "math",
        "英语": "english",
        "物理": "physics",
        "化学": "chemistry",
        "生物": "biology",
        "历史": "history",
        "地理": "geography",
        "政治": "politics",
        "计算机": "computer-science",
        "通识": "general",
        "未分类": "uncategorized",
    }

    @classmethod
    def normalize_subject(cls, raw_subject: str | None) -> tuple[str, str]:
        text = cls._normalize_lookup_text(raw_subject)
        if not text:
            return cls.DEFAULT_SUBJECT, cls.SUBJECT_SLUGS[cls.DEFAULT_SUBJECT]

        for canonical, aliases in cls.SUBJECT_ALIASES.items():
            normalized_aliases = {cls._normalize_lookup_text(alias) for alias in aliases}
            if text in normalized_aliases:
                return canonical, cls.SUBJECT_SLUGS[canonical]

        for canonical, aliases in cls.SUBJECT_ALIASES.items():
            normalized_aliases = [cls._normalize_lookup_text(alias) for alias in aliases]
            if any(alias and alias in text for alias in normalized_aliases):
                return canonical, cls.SUBJECT_SLUGS[canonical]

        return cls.DEFAULT_SUBJECT, cls.SUBJECT_SLUGS[cls.DEFAULT_SUBJECT]

    @classmethod
    def sanitize_title_base(cls, raw_title: str | None, fallback: str = "未命名笔记") -> str:
        title = (raw_title or "").strip()
        if not title:
            title = fallback
        title = title.replace("\n", " ").replace("\r", " ")
        title = re.sub(r"[\\/:*?\"<>|#\[\]{}]+", "-", title)
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r"-+", "-", title)
        title = title.strip(" .-_，。；：、")
        if not title:
            title = fallback
        return title[: cls.MAX_TITLE_LENGTH].rstrip(" .-_") or fallback

    @classmethod
    async def resolve_note_naming(
        cls,
        session: AsyncSession,
        *,
        raw_subject: str | None,
        raw_title: str | None,
        generated_at: datetime | None = None,
        note_directory: str | None = None,
    ) -> ResolvedNoteNaming:
        canonical_subject, subject_slug = cls.normalize_subject(raw_subject)
        base_title = cls.sanitize_title_base(raw_title)
        timestamp = cls._format_timestamp(generated_at)
        final_title_base = f"{base_title}-{timestamp}"
        base_dir = cls._sanitize_relative_directory(note_directory or cls.DEFAULT_BASE_DIR)
        subject_dir = cls._sanitize_path_segment(canonical_subject, fallback=cls.DEFAULT_SUBJECT)
        relative_path = await cls._dedupe_relative_path(
            session,
            base_dir=base_dir,
            subject_dir=subject_dir,
            final_title_base=final_title_base,
        )
        final_title = Path(relative_path).stem
        return ResolvedNoteNaming(
            subject=canonical_subject,
            subject_slug=subject_slug,
            base_title=base_title,
            final_title=final_title,
            relative_path=relative_path,
        )

    @classmethod
    async def _dedupe_relative_path(
        cls,
        session: AsyncSession,
        *,
        base_dir: str,
        subject_dir: str,
        final_title_base: str,
    ) -> str:
        candidate_index = 1
        while True:
            suffix = "" if candidate_index == 1 else f"-{candidate_index}"
            file_stem = f"{final_title_base}{suffix}"
            relative_path = f"{base_dir}/{subject_dir}/{file_stem}.md"
            if not await cls._path_exists(session, relative_path):
                return relative_path
            candidate_index += 1

    @staticmethod
    async def _path_exists(session: AsyncSession, relative_path: str) -> bool:
        db_existing = await session.execute(select(Note.id).where(Note.relative_path == relative_path))
        if db_existing.scalar_one_or_none() is not None:
            return True
        absolute_path = SafeFileService.resolve_workspace_path(relative_path)
        return absolute_path.exists()

    @staticmethod
    def _format_timestamp(generated_at: datetime | None) -> str:
        effective = generated_at or datetime.now(timezone.utc)
        if effective.tzinfo is None:
            effective = effective.replace(tzinfo=timezone.utc)
        else:
            effective = effective.astimezone(timezone.utc)
        return effective.strftime("%Y-%m-%d-%H%M")

    @classmethod
    def _sanitize_relative_directory(cls, raw_directory: str) -> str:
        parts = [cls._sanitize_path_segment(part, fallback="notes") for part in Path(raw_directory).parts if part not in {"", ".", "/"}]
        sanitized = "/".join(parts).strip("/")
        return sanitized or cls.DEFAULT_BASE_DIR

    @staticmethod
    def _normalize_lookup_text(value: str | None) -> str:
        text = unicodedata.normalize("NFKC", (value or "")).strip().lower()
        text = re.sub(r"\s+", "", text)
        return text

    @classmethod
    def _sanitize_path_segment(cls, value: str | None, fallback: str) -> str:
        text = unicodedata.normalize("NFKC", (value or "")).strip()
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"[\\/:*?\"<>|#\[\]{}]+", "-", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"-+", "-", text)
        text = text.strip(" .-_/\\")
        return text or fallback
