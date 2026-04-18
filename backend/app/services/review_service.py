from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_entities import UserActivitySnapshot
from app.models.knowledge_point import KnowledgePoint
from app.models.note import Note
from app.models.review_card import ReviewCard
from app.models.review_log import ReviewLog
from app.models.user import User
from app.services.file_write_service import FileWriteService
from app.services.fsrs_scheduler_service import FsrsSchedulerService
from app.services.safe_file_service import SafeFileService


class ReviewService:
    @staticmethod
    async def bootstrap_cards(
        session: AsyncSession,
        note_ids: list[int],
        all_notes: bool = False,
    ) -> dict:
        stmt = select(Note).order_by(Note.id.asc())
        if not all_notes:
            stmt = stmt.where(Note.id.in_(note_ids))
        result = await session.execute(stmt)
        notes = list(result.scalars().all())

        created_knowledge_points = 0
        created_cards = 0
        selected_note_ids = [note.id for note in notes]

        for note in notes:
            existing_points_result = await session.execute(
                select(KnowledgePoint).where(KnowledgePoint.note_id == note.id)
            )
            knowledge_points = list(existing_points_result.scalars().all())
            if not knowledge_points:
                knowledge_points = await ReviewService._extract_knowledge_points(session, note)
                created_knowledge_points += len(knowledge_points)

            for point in knowledge_points:
                card_result = await session.execute(
                    select(ReviewCard).where(ReviewCard.knowledge_point_id == point.id)
                )
                card = card_result.scalar_one_or_none()
                if card is None:
                    card = ReviewCard(
                        knowledge_point_id=point.id,
                        state_json=FsrsSchedulerService.initial_state(),
                        due_at=FsrsSchedulerService.initial_due_at(),
                        last_reviewed_at=None,
                        suspended=False,
                    )
                    session.add(card)
                    created_cards += 1

        await session.commit()
        return {
            "created_knowledge_points": created_knowledge_points,
            "created_cards": created_cards,
            "note_ids": selected_note_ids,
        }

    @staticmethod
    async def _extract_knowledge_points(session: AsyncSession, note: Note) -> list[KnowledgePoint]:
        content = SafeFileService.read_text(note.relative_path)
        sections = ReviewService._split_into_sections(content)
        created: list[KnowledgePoint] = []
        seen_signatures: set[str] = set()
        for index, section in enumerate(sections, start=1):
            content_md = section["content"].strip()
            if not content_md:
                continue
            signature = ReviewService._normalize_signature(section["title"], content_md)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)

            title = section["title"] or f"{note.title} - Knowledge Point {index}"
            tags = ReviewService._extract_tags(title=title, content=content_md)
            point = KnowledgePoint(
                note_id=note.id,
                title=title[:255],
                content_md=content_md,
                embedding_vector=None,
                tags_json={
                    "source": "markdown_section",
                    "order": index,
                    "tags": tags,
                    "section_level": section.get("level"),
                    "source_kind": section.get("kind", "section"),
                    "line_span": section.get("line_span"),
                },
                summary_text=ReviewService._build_summary_text(content_md),
                source_anchor=section.get("anchor") or title[:255],
            )
            session.add(point)
            created.append(point)
        await session.flush()
        return created

    @staticmethod
    def _split_into_sections(content: str) -> list[dict[str, str | int]]:
        normalized = content.replace("\r\n", "\n")
        lines = normalized.split("\n")
        sections: list[dict[str, str | int]] = []
        current_title: str | None = None
        current_level: int | None = None
        current_lines: list[str] = []
        current_start_line = 1

        def flush(end_line: int) -> None:
            nonlocal current_title, current_level, current_lines, current_start_line
            body = "\n".join(current_lines).strip()
            if body:
                fragments = ReviewService._explode_section(current_title, body)
                for offset, fragment in enumerate(fragments, start=1):
                    title = fragment["title"] or current_title or "未命名知识点"
                    sections.append(
                        {
                            "title": title,
                            "content": fragment["content"],
                            "level": current_level or 1,
                            "kind": fragment["kind"],
                            "anchor": ReviewService._slugify_anchor(title),
                            "line_span": f"{current_start_line}-{end_line}",
                            "fragment_order": offset,
                        }
                    )
            current_title = None
            current_level = None
            current_lines = []
            current_start_line = end_line + 1

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                flush(line_number - 1)
                current_level = len(stripped) - len(stripped.lstrip("#"))
                current_title = stripped.lstrip("# ").strip() or None
                current_start_line = line_number
            else:
                current_lines.append(line)
        flush(len(lines))

        if not sections and normalized.strip():
            chunks = [chunk.strip() for chunk in normalized.split("\n\n") if chunk.strip()]
            for index, chunk in enumerate(chunks, start=1):
                sections.append(
                    {
                        "title": f"知识点 {index}",
                        "content": chunk,
                        "level": 1,
                        "kind": "paragraph",
                        "anchor": f"knowledge-point-{index}",
                        "line_span": "1-1",
                        "fragment_order": 1,
                    }
                )
        return sections

    @staticmethod
    def _explode_section(title: str | None, body: str) -> list[dict[str, str]]:
        paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", body) if chunk.strip()]
        fragments: list[dict[str, str]] = []
        for paragraph in paragraphs:
            lines = [line.strip() for line in paragraph.split("\n") if line.strip()]
            bullet_lines = [line for line in lines if re.match(r"^[-*+]\s+", line)]
            if len(bullet_lines) >= 2:
                for bullet in bullet_lines:
                    text = re.sub(r"^[-*+]\s+", "", bullet).strip()
                    if text:
                        fragments.append({"title": title or text[:60], "content": text, "kind": "bullet"})
                continue
            if len(paragraph) > 320 and len(lines) > 1:
                sentence_chunks = [item.strip() for item in re.split(r"(?<=[。！？.!?])\s+", paragraph) if item.strip()]
                if len(sentence_chunks) >= 2:
                    for chunk in sentence_chunks:
                        fragments.append({"title": title or chunk[:60], "content": chunk, "kind": "sentence"})
                    continue
            fragments.append({"title": title or lines[0][:60], "content": paragraph, "kind": "paragraph"})
        return fragments

    @staticmethod
    def _normalize_signature(title: str | None, content: str) -> str:
        normalized = re.sub(r"\s+", " ", f"{title or ''} {content}".strip().lower())
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_summary_text(content: str, limit: int = 180) -> str:
        compact = re.sub(r"\s+", " ", content).strip()
        if len(compact) <= limit:
            return compact
        return compact[: limit - 1].rstrip() + "…"

    @staticmethod
    def _extract_tags(*, title: str, content: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,8}", f"{title} {content}")
        stopwords = {"知识点", "内容", "以及", "进行", "可以", "需要", "用于", "一个", "一些", "这个", "我们", "你可以", "source", "markdown", "section"}
        tags: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip().lower()
            if normalized in stopwords or normalized.isdigit():
                continue
            if normalized not in tags:
                tags.append(normalized)
            if len(tags) >= 6:
                break
        return tags

    @staticmethod
    def _slugify_anchor(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower()).strip("-")
        return slug[:255] or "knowledge-point"

    @staticmethod
    async def get_overview(session: AsyncSession) -> dict:
        now = datetime.now(timezone.utc)
        day_end = now + timedelta(days=1)

        total_cards = await session.scalar(select(func.count()).select_from(ReviewCard))
        due_today_count = await session.scalar(
            select(func.count()).select_from(ReviewCard).where(ReviewCard.suspended.is_(False), ReviewCard.due_at <= day_end)
        )
        recent_logs = await session.execute(
            select(ReviewLog).where(ReviewLog.created_at >= now - timedelta(days=7))
        )
        logs = list(recent_logs.scalars().all())
        return {
            "due_today_count": int(total_cards and due_today_count or due_today_count or 0),
            "total_cards": int(total_cards or 0),
            "recent_review_count": len(logs),
            "recent_review_seconds": sum(log.duration_seconds for log in logs),
        }

    @staticmethod
    async def get_queue(session: AsyncSession, limit: int = 20, due_only: bool = True) -> list[ReviewCard]:
        stmt = (
            select(ReviewCard)
            .options(
                selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note),
            )
            .where(ReviewCard.suspended.is_(False))
            .order_by(ReviewCard.due_at.asc(), ReviewCard.id.asc())
            .limit(limit)
        )
        if due_only:
            stmt = stmt.where(ReviewCard.due_at <= datetime.now(timezone.utc))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def grade_card(
        session: AsyncSession,
        card_id: int,
        rating: int,
        duration_seconds: int,
        note: str | None,
        user: User,
    ) -> tuple[ReviewCard | None, ReviewLog | None]:
        result = await session.execute(select(ReviewCard).where(ReviewCard.id == card_id))
        card = result.scalar_one_or_none()
        if card is None:
            return None, None

        now = datetime.now(timezone.utc)
        next_state, due_at = FsrsSchedulerService.grade(card.state_json or {}, rating, now=now)
        card.state_json = next_state
        card.due_at = due_at
        card.last_reviewed_at = now
        session.add(card)

        review_log = ReviewLog(
            user_id=user.id,
            review_card_id=card.id,
            rating=rating,
            duration_seconds=duration_seconds,
            note=note,
        )
        session.add(review_log)
        await ReviewService.record_user_activity(
            session,
            user=user,
            event_type="review_grade",
            watch_seconds=duration_seconds,
            review_increment=1,
        )
        await session.commit()
        await session.refresh(card)
        await session.refresh(review_log)
        return card, review_log

    @staticmethod
    async def create_review_log(
        session: AsyncSession,
        review_card_id: int,
        rating: int,
        duration_seconds: int,
        note: str | None,
        user: User,
    ) -> ReviewLog:
        review_log = ReviewLog(
            user_id=user.id,
            review_card_id=review_card_id,
            rating=rating,
            duration_seconds=duration_seconds,
            note=note,
        )
        session.add(review_log)
        await ReviewService.record_user_activity(
            session,
            user=user,
            event_type="review_log",
            watch_seconds=duration_seconds,
            review_increment=1,
        )
        await session.commit()
        await session.refresh(review_log)
        return review_log

    @staticmethod
    async def list_review_logs(session: AsyncSession, limit: int = 50) -> list[ReviewLog]:
        result = await session.execute(
            select(ReviewLog).order_by(ReviewLog.created_at.desc(), ReviewLog.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def record_user_activity(
        session: AsyncSession,
        *,
        user: User,
        event_type: str,
        watch_seconds: int = 0,
        page_view_increment: int = 0,
        note_view_increment: int = 0,
        review_increment: int = 0,
        occurred_at: datetime | None = None,
    ) -> UserActivitySnapshot:
        result = await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == user.id))
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            snapshot = UserActivitySnapshot(user_id=user.id)

        effective_time = occurred_at or datetime.now(timezone.utc)
        watch_seconds = max(int(watch_seconds or 0), 0)
        page_view_increment = max(int(page_view_increment or 0), 0)
        note_view_increment = max(int(note_view_increment or 0), 0)
        review_increment = max(int(review_increment or 0), 0)

        snapshot.total_watch_seconds = int(snapshot.total_watch_seconds or 0) + watch_seconds
        snapshot.review_watch_seconds = int(snapshot.review_watch_seconds or 0) + watch_seconds
        snapshot.page_view_count = int(snapshot.page_view_count or 0) + page_view_increment
        snapshot.note_view_count = int(snapshot.note_view_count or 0) + note_view_increment
        snapshot.review_count = int(snapshot.review_count or 0) + review_increment
        snapshot.last_activity_at = effective_time
        snapshot.last_event_type = event_type
        session.add(snapshot)
        await session.flush()
        return snapshot

    @staticmethod
    def build_summary_markdown(note_title: str, content: str) -> str:
        return f"# {note_title}\n\n{content.strip()}\n"

    @staticmethod
    def hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def artifact_relative_path(kind: str, slug: str) -> str:
        return f"artifacts/{kind}/{slug}.md"

    @staticmethod
    def ensure_artifact_dir(kind: str) -> Path:
        return FileWriteService.ensure_directory(f"artifacts/{kind}")
