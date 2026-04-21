from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.openai_compatible import OpenAICompatibleProviderAdapter
from app.models.admin_entities import UserActivitySnapshot
from app.models.enums import JobType, ProviderType
from app.models.job import Job
from app.models.knowledge_point import KnowledgePoint
from app.models.note import Note
from app.models.review_card import ReviewCard
from app.models.review_log import ReviewLog
from app.models.user import User
from app.schemas.integrations import OpenAIMessage
from app.services.file_write_service import FileWriteService
from app.services.fsrs_scheduler_service import FsrsSchedulerService
from app.services.job_service import JobService
from app.services.safe_file_service import SafeFileService


class ReviewService:
    REVIEW_HEARTBEAT_MAX_STEP_SECONDS = 30

    @staticmethod
    def _extract_subject_from_note(note: Note | None) -> str | None:
        if note is None:
            return None
        frontmatter = note.frontmatter_json or {}
        subject = str(frontmatter.get("subject") or "").strip()
        return subject or None

    @staticmethod
    def _normalize_subject(subject: str | None) -> str | None:
        value = str(subject or "").strip()
        return value or None

    @staticmethod
    def _build_tags_json(*, tags: list[str] | None, subject: str | None, existing: dict | None = None) -> dict[str, Any]:
        payload = dict(existing or {})
        normalized_tags = [str(tag).strip() for tag in (tags or []) if str(tag).strip()]
        payload["tags"] = normalized_tags
        normalized_subject = ReviewService._normalize_subject(subject)
        if normalized_subject:
            payload["subject"] = normalized_subject
        else:
            payload.pop("subject", None)
        return payload

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    @staticmethod
    async def create_review_card_job(
        session: AsyncSession,
        note_ids: list[int],
        *,
        all_notes: bool = False,
        parent_job_id: int | None = None,
        trigger: str = "manual",
        source_job_type: str | None = None,
    ) -> Job:
        normalized_note_ids = sorted({int(note_id) for note_id in note_ids if int(note_id) > 0})
        return await JobService.create_job(
            session,
            JobType.REVIEW_CARD_GENERATION,
            {
                "note_ids": normalized_note_ids,
                "all_notes": all_notes,
                "parent_job_id": parent_job_id,
                "trigger": trigger,
                "source_job_type": source_job_type,
            },
        )

    @staticmethod
    async def enqueue_note_review_card_generation(
        session: AsyncSession,
        note_ids: list[int],
        *,
        parent_job_id: int | None,
        trigger: str,
        source_job_type: str | None,
    ) -> Job | None:
        normalized_note_ids = sorted({int(note_id) for note_id in note_ids if int(note_id) > 0})
        if not normalized_note_ids:
            return None
        return await ReviewService.create_review_card_job(
            session,
            note_ids=normalized_note_ids,
            all_notes=False,
            parent_job_id=parent_job_id,
            trigger=trigger,
            source_job_type=source_job_type,
        )

    @staticmethod
    async def execute_review_card_job(
        session: AsyncSession,
        *,
        job_id: int,
        note_ids: list[int],
        all_notes: bool = False,
        parent_job_id: int | None = None,
        trigger: str = "manual",
        source_job_type: str | None = None,
    ) -> dict[str, Any]:
        job = await session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if job.status == "pending":
            await JobService.mark_running(session, job)

        await JobService.append_log(
            session,
            job,
            "info",
            "review card generation pipeline started",
            stage="review_card_generation",
            note_count=len(note_ids or []),
            all_notes=all_notes,
            parent_job_id=parent_job_id,
            trigger=trigger,
            source_job_type=source_job_type,
        )
        try:
            bootstrap_result = await ReviewService.bootstrap_cards(
                session,
                note_ids=note_ids,
                all_notes=all_notes,
                commit=False,
                job=job,
            )
            result_payload = {
                **bootstrap_result,
                "parent_job_id": parent_job_id,
                "trigger": trigger,
                "source_job_type": source_job_type,
            }
            await JobService.append_log(
                session,
                job,
                "info",
                "review card generation pipeline completed",
                stage="review_card_generation",
                created_knowledge_points=bootstrap_result["created_knowledge_points"],
                created_cards=bootstrap_result["created_cards"],
                generation_mode=bootstrap_result["generation_mode"],
                ai_generated_knowledge_points=bootstrap_result["ai_generated_knowledge_points"],
                fallback_generated_knowledge_points=bootstrap_result["fallback_generated_knowledge_points"],
                note_ids=bootstrap_result["note_ids"],
                parent_job_id=parent_job_id,
                trigger=trigger,
                source_job_type=source_job_type,
            )
            await JobService.mark_completed(session, job, result_payload)
            return result_payload
        except Exception as exc:  # noqa: BLE001
            await JobService.mark_failed(session, job, str(exc))
            raise

    @staticmethod
    async def bootstrap_cards(
        session: AsyncSession,
        note_ids: list[int],
        all_notes: bool = False,
        *,
        commit: bool = True,
        job: Job | None = None,
    ) -> dict:
        stmt = select(Note).order_by(Note.id.asc())
        if not all_notes:
            stmt = stmt.where(Note.id.in_(note_ids))
        result = await session.execute(stmt)
        notes = list(result.scalars().all())

        created_knowledge_points = 0
        created_cards = 0
        ai_generated_knowledge_points = 0
        fallback_generated_knowledge_points = 0
        selected_note_ids = [note.id for note in notes]

        for note in notes:
            existing_points_result = await session.execute(
                select(KnowledgePoint).where(KnowledgePoint.note_id == note.id)
            )
            knowledge_points = list(existing_points_result.scalars().all())
            if not knowledge_points:
                knowledge_points, generation_meta = await ReviewService._extract_knowledge_points(session, note, job=job)
                created_knowledge_points += len(knowledge_points)
                if generation_meta["mode"] == "ai":
                    ai_generated_knowledge_points += len(knowledge_points)
                else:
                    fallback_generated_knowledge_points += len(knowledge_points)

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

        if commit:
            await session.commit()
        else:
            await session.flush()
        return {
            "created_knowledge_points": created_knowledge_points,
            "created_cards": created_cards,
            "note_ids": selected_note_ids,
            "generation_mode": "ai" if ai_generated_knowledge_points > 0 and fallback_generated_knowledge_points == 0 else "mixed" if ai_generated_knowledge_points > 0 else "fallback",
            "ai_generated_knowledge_points": ai_generated_knowledge_points,
            "fallback_generated_knowledge_points": fallback_generated_knowledge_points,
        }

    @staticmethod
    async def _extract_knowledge_points(
        session: AsyncSession,
        note: Note,
        *,
        job: Job | None = None,
    ) -> tuple[list[KnowledgePoint], dict[str, Any]]:
        content = SafeFileService.read_text(note.relative_path)
        adapter = OpenAICompatibleProviderAdapter(session)
        provider = await adapter.get_provider(ProviderType.LLM)
        if provider is not None:
            try:
                if job is not None:
                    await JobService.append_log(
                        session,
                        job,
                        "info",
                        "review card ai generation started",
                        stage="review_card_generation",
                        note_id=note.id,
                        note_title=note.title,
                    )
                created = await ReviewService._extract_knowledge_points_with_ai(session, note, content, adapter)
                if created:
                    if job is not None:
                        await JobService.append_log(
                            session,
                            job,
                            "info",
                            "review card ai generation completed",
                            stage="review_card_generation",
                            note_id=note.id,
                            note_title=note.title,
                            generated_count=len(created),
                            provider_model=provider.model_name,
                        )
                    return created, {"mode": "ai", "provider_model": provider.model_name, "count": len(created)}
                if job is not None:
                    await JobService.append_log(
                        session,
                        job,
                        "warning",
                        "review card ai generation returned no usable cards, fallback applied",
                        stage="review_card_generation",
                        note_id=note.id,
                        note_title=note.title,
                        provider_model=provider.model_name,
                    )
            except Exception as exc:  # noqa: BLE001
                if job is not None:
                    await JobService.append_log(
                        session,
                        job,
                        "warning",
                        "review card ai generation failed, fallback applied",
                        stage="review_card_generation",
                        note_id=note.id,
                        note_title=note.title,
                        error_message=str(exc),
                        provider_model=provider.model_name,
                    )

        created = await ReviewService._extract_knowledge_points_by_rules(session, note, content)
        if job is not None:
            await JobService.append_log(
                session,
                job,
                "info",
                "review card fallback generation completed",
                stage="review_card_generation",
                note_id=note.id,
                note_title=note.title,
                generated_count=len(created),
            )
        return created, {"mode": "fallback", "count": len(created)}

    @staticmethod
    async def _extract_knowledge_points_by_rules(
        session: AsyncSession,
        note: Note,
        content: str,
    ) -> list[KnowledgePoint]:
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
    async def _extract_knowledge_points_with_ai(
        session: AsyncSession,
        note: Note,
        content: str,
        adapter: OpenAICompatibleProviderAdapter,
    ) -> list[KnowledgePoint]:
        prompt = ReviewService._build_review_card_generation_prompt(note=note, content=content)
        llm_result = await adapter.chat(
            [OpenAIMessage(role="user", content=prompt)],
            system_prompt=(
                "你是复习卡片生成助手。请把学习笔记拆成可独立复习、最小记忆单元、可判分的卡片。"
                "每张卡片只覆盖一个知识点，answer 必须简洁、明确、可作为标准答案。"
                "只返回 JSON，不要 markdown，不要解释。"
            ),
        )
        payload = ReviewService._parse_review_card_generation_response(llm_result.content)
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise ValueError("review card generation output missing items")

        created: list[KnowledgePoint] = []
        seen_signatures: set[str] = set()
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("question") or "").strip()
            question = str(item.get("question") or title or "").strip()
            answer = str(item.get("answer") or "").strip()
            if not question or not answer:
                continue
            normalized_title = title or question[:80]
            tags = item.get("tags") if isinstance(item.get("tags"), list) else []
            normalized_tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()][:6]
            if not normalized_tags:
                normalized_tags = ReviewService._extract_tags(title=normalized_title, content=answer)
            signature = ReviewService._normalize_signature(normalized_title, answer)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            point = KnowledgePoint(
                note_id=note.id,
                title=normalized_title[:255],
                content_md=answer,
                embedding_vector=None,
                tags_json={
                    "source": "ai_review_card_generation",
                    "order": index,
                    "tags": normalized_tags,
                    "question": question[:500],
                    "card_kind": str(item.get("card_kind") or "short_answer")[:50],
                    "principles": ["atomic", "gradable", "independent"],
                },
                summary_text=ReviewService._build_summary_text(answer),
                source_anchor=ReviewService._slugify_anchor(normalized_title),
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
    def _build_review_card_generation_prompt(*, note: Note, content: str) -> str:
        trimmed_content = (content or "").strip()[:12000]
        return (
            "请把下面笔记拆成用于主动回忆的复习卡片，严格遵守以下原则：\n"
            "1. 每张卡片只覆盖一个最小知识点；\n"
            "2. 卡片应独立，不依赖上下文才能理解；\n"
            "3. answer 必须可判分、简洁、尽量唯一；\n"
            "4. 优先生成问答型 short_answer 卡片，不要生成开放式长论述；\n"
            "5. 若内容偏定义/概念/公式/区别/步骤，可直接提炼为问答。\n\n"
            "输出 JSON 对象，格式固定：\n"
            "{\n"
            '  "items": [\n'
            "    {\n"
            '      "title": "卡片标题",\n'
            '      "question": "问题",\n'
            '      "answer": "标准答案",\n'
            '      "card_kind": "short_answer",\n'
            '      "tags": ["标签1", "标签2"]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"note_title: {note.title}\n"
            f"note_path: {note.relative_path}\n\n"
            "note_content:\n"
            f"{trimmed_content}"
        )

    @staticmethod
    def _parse_review_card_generation_response(content: str) -> dict[str, Any]:
        raw_text = (content or "").strip()
        if not raw_text:
            raise ValueError("LLM review card generation returned empty content")

        payload_text = raw_text
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fence_match:
            payload_text = fence_match.group(1).strip()
        elif not raw_text.startswith("{"):
            object_match = re.search(r"\{[\s\S]*\}", raw_text)
            if object_match:
                payload_text = object_match.group(0).strip()

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM review card generation output is not valid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("LLM review card generation output must be a JSON object")
        return payload

    @staticmethod
    def _slugify_anchor(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower()).strip("-")
        return slug[:255] or "knowledge-point"

    @staticmethod
    async def _get_or_create_activity_snapshot(session: AsyncSession, user: User) -> UserActivitySnapshot:
        result = await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == user.id))
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            snapshot = UserActivitySnapshot(user_id=user.id)
            session.add(snapshot)
            await session.flush()
        return snapshot

    @staticmethod
    def _coerce_utc_datetime(value: datetime | None, fallback: datetime) -> datetime:
        if value is None:
            return fallback
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _review_session_payload(snapshot: UserActivitySnapshot) -> dict:
        return {
            "active_card_id": snapshot.active_review_card_id,
            "accumulated_seconds": int(snapshot.active_review_session_seconds or 0),
            "started_at": snapshot.review_session_started_at,
            "last_heartbeat_at": snapshot.review_session_last_heartbeat_at,
        }

    @staticmethod
    def _consume_review_session_seconds(
        snapshot: UserActivitySnapshot,
        *,
        card_id: int,
        now: datetime,
        reported_duration_seconds: int | None = None,
        clear_session: bool = True,
    ) -> dict[str, int]:
        accumulated_seconds = 0
        if snapshot.active_review_card_id == card_id:
            last_heartbeat = ReviewService._coerce_utc_datetime(
                snapshot.review_session_last_heartbeat_at or snapshot.review_session_started_at,
                now,
            )
            tail_increment = max(0, int((now - last_heartbeat).total_seconds()))
            tail_increment = min(tail_increment, ReviewService.REVIEW_HEARTBEAT_MAX_STEP_SECONDS)
            accumulated_seconds = int(snapshot.active_review_session_seconds or 0) + tail_increment

        reported_duration = max(int(reported_duration_seconds or 0), 0)
        final_duration = max(accumulated_seconds, reported_duration)

        if clear_session and snapshot.active_review_card_id == card_id:
            snapshot.active_review_card_id = None
            snapshot.active_review_session_seconds = 0
            snapshot.review_session_started_at = None
            snapshot.review_session_last_heartbeat_at = None

        return {
            "duration_seconds": final_duration,
            "server_accumulated_seconds": accumulated_seconds,
            "client_reported_seconds": reported_duration,
        }

    @staticmethod
    async def start_review_session(
        session: AsyncSession,
        *,
        card_id: int,
        user: User,
    ) -> dict:
        now = datetime.now(timezone.utc)
        snapshot = await ReviewService._get_or_create_activity_snapshot(session, user)
        if snapshot.active_review_card_id != card_id:
            snapshot.active_review_card_id = card_id
            snapshot.active_review_session_seconds = 0
            snapshot.review_session_started_at = now
        elif snapshot.review_session_started_at is None:
            snapshot.review_session_started_at = now
        snapshot.review_session_last_heartbeat_at = now
        snapshot.last_activity_at = now
        snapshot.last_event_type = "review_session_start"
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return ReviewService._review_session_payload(snapshot)

    @staticmethod
    async def heartbeat_review_session(
        session: AsyncSession,
        *,
        card_id: int,
        user: User,
    ) -> dict:
        now = datetime.now(timezone.utc)
        snapshot = await ReviewService._get_or_create_activity_snapshot(session, user)
        if snapshot.active_review_card_id != card_id:
            snapshot.active_review_card_id = card_id
            snapshot.active_review_session_seconds = 0
            snapshot.review_session_started_at = now
            increment = 0
        else:
            last_heartbeat = ReviewService._coerce_utc_datetime(
                snapshot.review_session_last_heartbeat_at or snapshot.review_session_started_at,
                now,
            )
            increment = max(0, int((now - last_heartbeat).total_seconds()))
            increment = min(increment, ReviewService.REVIEW_HEARTBEAT_MAX_STEP_SECONDS)
        snapshot.active_review_session_seconds = int(snapshot.active_review_session_seconds or 0) + increment
        snapshot.review_session_last_heartbeat_at = now
        snapshot.last_activity_at = now
        snapshot.last_event_type = "review_session_heartbeat"
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        payload = ReviewService._review_session_payload(snapshot)
        payload["increment_seconds"] = increment
        return payload

    @staticmethod
    async def finalize_review_session(
        session: AsyncSession,
        *,
        card_id: int,
        user: User,
        reported_duration_seconds: int | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        snapshot = await ReviewService._get_or_create_activity_snapshot(session, user)
        session_result = ReviewService._consume_review_session_seconds(
            snapshot,
            card_id=card_id,
            now=now,
            reported_duration_seconds=reported_duration_seconds,
            clear_session=True,
        )
        snapshot.last_activity_at = now
        snapshot.last_event_type = "review_session_finalize"
        session.add(snapshot)
        await session.commit()
        return {
            "card_id": card_id,
            **session_result,
            "finalized_at": now,
        }

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
    async def get_queue(
        session: AsyncSession,
        limit: int = 20,
        due_only: bool = True,
        *,
        subject: str | None = None,
    ) -> list[ReviewCard]:
        normalized_subject = ReviewService._normalize_subject(subject)
        stmt = (
            select(ReviewCard)
            .options(
                selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note),
            )
            .join(ReviewCard.knowledge_point)
            .join(KnowledgePoint.note)
            .where(ReviewCard.suspended.is_(False))
            .order_by(ReviewCard.due_at.asc(), ReviewCard.id.asc())
            .limit(limit)
        )
        if due_only:
            stmt = stmt.where(ReviewCard.due_at <= datetime.now(timezone.utc))
        if normalized_subject:
            stmt = stmt.where(Note.frontmatter_json["subject"].as_string() == normalized_subject)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_subjects(session: AsyncSession) -> list[dict[str, Any]]:
        result = await session.execute(
            select(ReviewCard)
            .options(selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note))
            .join(ReviewCard.knowledge_point)
            .join(KnowledgePoint.note)
            .where(ReviewCard.suspended.is_(False))
            .order_by(ReviewCard.id.asc())
        )
        cards = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        summary_map: dict[str, dict[str, Any]] = {}
        for card in cards:
            subject_name = ReviewService._extract_subject_from_note(card.knowledge_point.note) or "未分类"
            bucket = summary_map.setdefault(subject_name, {"subject": subject_name, "total_cards": 0, "due_cards": 0})
            bucket["total_cards"] += 1
            if ReviewService._coerce_utc(card.due_at) <= now:
                bucket["due_cards"] += 1
        return sorted(summary_map.values(), key=lambda item: (item["subject"] != "未分类", -item["due_cards"], item["subject"]))

    @staticmethod
    async def list_admin_cards(
        session: AsyncSession,
        *,
        subject: str | None = None,
        note_id: int | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewCard]:
        normalized_subject = ReviewService._normalize_subject(subject)
        normalized_query = str(query or "").strip()
        stmt = (
            select(ReviewCard)
            .options(selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note))
            .join(ReviewCard.knowledge_point)
            .join(KnowledgePoint.note)
            .order_by(ReviewCard.updated_at.desc(), ReviewCard.id.desc())
            .offset(max(offset, 0))
            .limit(limit)
        )
        if normalized_subject:
            stmt = stmt.where(Note.frontmatter_json["subject"].as_string() == normalized_subject)
        if note_id is not None:
            stmt = stmt.where(KnowledgePoint.note_id == note_id)
        if normalized_query:
            like_value = f"%{normalized_query}%"
            stmt = stmt.where(
                or_(
                    KnowledgePoint.title.ilike(like_value),
                    KnowledgePoint.content_md.ilike(like_value),
                    KnowledgePoint.summary_text.ilike(like_value),
                    Note.title.ilike(like_value),
                )
            )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_admin_card(
        session: AsyncSession,
        *,
        note_id: int,
        title: str,
        content_md: str,
        summary_text: str | None,
        source_anchor: str | None,
        tags: list[str] | None,
        subject: str | None,
        suspended: bool,
    ) -> ReviewCard:
        note = await session.get(Note, note_id)
        if note is None:
            raise ValueError("Note not found")

        normalized_subject = ReviewService._normalize_subject(subject)
        frontmatter = dict(note.frontmatter_json or {})
        if normalized_subject:
            frontmatter["subject"] = normalized_subject
            note.frontmatter_json = frontmatter
            session.add(note)

        point = KnowledgePoint(
            note_id=note.id,
            title=title.strip(),
            content_md=content_md.strip(),
            embedding_vector=None,
            tags_json=ReviewService._build_tags_json(tags=tags, subject=normalized_subject, existing={}),
            summary_text=(summary_text or "").strip() or None,
            source_anchor=(source_anchor or "").strip() or None,
        )
        session.add(point)
        await session.flush()

        card = ReviewCard(
            knowledge_point_id=point.id,
            state_json=FsrsSchedulerService.initial_state(),
            due_at=FsrsSchedulerService.initial_due_at(),
            last_reviewed_at=None,
            suspended=bool(suspended),
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card

    @staticmethod
    async def update_admin_card(
        session: AsyncSession,
        *,
        card_id: int,
        title: str | None = None,
        content_md: str | None = None,
        summary_text: str | None = None,
        source_anchor: str | None = None,
        tags: list[str] | None = None,
        subject: str | None = None,
        suspended: bool | None = None,
    ) -> ReviewCard | None:
        result = await session.execute(
            select(ReviewCard)
            .options(selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note))
            .where(ReviewCard.id == card_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            return None

        point = card.knowledge_point
        note = point.note

        if title is not None:
            point.title = title.strip()
        if content_md is not None:
            point.content_md = content_md.strip()
        if summary_text is not None:
            point.summary_text = (summary_text or "").strip() or None
        if source_anchor is not None:
            point.source_anchor = (source_anchor or "").strip() or None
        if tags is not None or subject is not None:
            effective_subject = ReviewService._normalize_subject(subject) if subject is not None else ReviewService._extract_subject_from_note(note)
            point.tags_json = ReviewService._build_tags_json(tags=tags if tags is not None else point.tags_json.get("tags"), subject=effective_subject, existing=point.tags_json)
        if subject is not None and note is not None:
            normalized_subject = ReviewService._normalize_subject(subject)
            frontmatter = dict(note.frontmatter_json or {})
            if normalized_subject:
                frontmatter["subject"] = normalized_subject
            else:
                frontmatter.pop("subject", None)
            note.frontmatter_json = frontmatter
            session.add(note)
        if suspended is not None:
            card.suspended = bool(suspended)

        session.add(point)
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card

    @staticmethod
    async def delete_admin_card(session: AsyncSession, *, card_id: int) -> dict[str, Any]:
        result = await session.execute(select(ReviewCard).where(ReviewCard.id == card_id))
        card = result.scalar_one_or_none()
        if card is None:
            return {"card_id": card_id, "deleted": False, "deleted_knowledge_point_id": None}
        deleted_knowledge_point_id = card.knowledge_point_id
        await session.delete(card)
        point = await session.get(KnowledgePoint, deleted_knowledge_point_id)
        if point is not None:
            await session.delete(point)
        await session.commit()
        return {"card_id": card_id, "deleted": True, "deleted_knowledge_point_id": deleted_knowledge_point_id}

    @staticmethod
    async def judge_answer(
        session: AsyncSession,
        *,
        card_id: int,
        answer: str,
        user: User,
    ) -> dict[str, Any]:
        result = await session.execute(
            select(ReviewCard)
            .options(selectinload(ReviewCard.knowledge_point).selectinload(KnowledgePoint.note))
            .where(ReviewCard.id == card_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise ValueError("Review card not found")

        normalized_answer = (answer or "").strip()
        if not normalized_answer:
            raise ValueError("Answer must not be empty")

        expected_answer = ReviewService._build_expected_answer(card.knowledge_point)
        fallback_result = ReviewService._fallback_judge(
            question_title=card.knowledge_point.title,
            expected_answer=expected_answer,
            answer=normalized_answer,
        )

        adapter = OpenAICompatibleProviderAdapter(session)
        provider = await adapter.get_provider(ProviderType.LLM)
        if provider is None:
            return fallback_result

        try:
            prompt = ReviewService._build_review_judge_prompt(
                title=card.knowledge_point.title,
                source_note_title=card.knowledge_point.note.title if card.knowledge_point.note else None,
                expected_answer=expected_answer,
                learner_answer=normalized_answer,
            )
            llm_result = await adapter.chat(
                [OpenAIMessage(role="user", content=prompt)],
                system_prompt=(
                    "你是复习判分助手。请依据知识点标准答案对用户短答做最小可行判分，"
                    "只返回 JSON，不要输出额外解释或 markdown。"
                ),
            )
            parsed = ReviewService._parse_review_judge_response(llm_result.content)
            return {
                "card_id": card.id,
                "answer": normalized_answer,
                "expected_answer": expected_answer,
                "suggested_rating": max(1, min(int(parsed.get("suggested_rating", fallback_result["suggested_rating"])), 4)),
                "correctness": parsed.get("correctness") or fallback_result["correctness"],
                "explanation": (parsed.get("explanation") or fallback_result["explanation"]).strip(),
                "judge_status": "ai",
                "judge_error": None,
            }
        except Exception as exc:  # noqa: BLE001
            fallback_result["judge_error"] = str(exc)
            return fallback_result

    @staticmethod
    async def grade_card(
        session: AsyncSession,
        card_id: int,
        rating: int,
        duration_seconds: int,
        note: str | None,
        user: User,
        answer: str | None = None,
        ai_judge: dict | None = None,
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

        snapshot = await ReviewService._get_or_create_activity_snapshot(session, user)
        session_result = ReviewService._consume_review_session_seconds(
            snapshot,
            card_id=card.id,
            now=now,
            reported_duration_seconds=duration_seconds,
            clear_session=True,
        )
        effective_duration_seconds = session_result["duration_seconds"]

        review_log = ReviewLog(
            user_id=user.id,
            review_card_id=card.id,
            rating=rating,
            duration_seconds=effective_duration_seconds,
            note=ReviewService._compose_review_log_note(note=note, answer=answer, ai_judge=ai_judge, final_rating=rating),
        )
        session.add(review_log)
        await ReviewService.record_user_activity(
            session,
            user=user,
            event_type="review_grade",
            watch_seconds=effective_duration_seconds,
            review_watch_seconds=effective_duration_seconds,
            review_increment=1,
            occurred_at=now,
        )

        snapshot.last_activity_at = now
        snapshot.last_event_type = "review_grade"
        session.add(snapshot)

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
            review_watch_seconds=duration_seconds,
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
        review_watch_seconds: int = 0,
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
        review_watch_seconds = max(int(review_watch_seconds or 0), 0)

        snapshot.total_watch_seconds = int(snapshot.total_watch_seconds or 0) + watch_seconds
        snapshot.review_watch_seconds = int(snapshot.review_watch_seconds or 0) + review_watch_seconds
        snapshot.page_view_count = int(snapshot.page_view_count or 0) + page_view_increment
        snapshot.note_view_count = int(snapshot.note_view_count or 0) + note_view_increment
        snapshot.review_count = int(snapshot.review_count or 0) + review_increment
        snapshot.last_activity_at = effective_time
        snapshot.last_event_type = event_type
        session.add(snapshot)
        await session.flush()
        return snapshot

    @staticmethod
    def _build_expected_answer(point: KnowledgePoint) -> str:
        candidate = (point.summary_text or point.content_md or point.title or "").strip()
        candidate = re.sub(r"\s+", " ", candidate)
        return candidate[:500]

    @staticmethod
    def _tokenize_for_judgement(value: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_+-]{2,}|[\u4e00-\u9fff]{1,8}", (value or "").lower())

    @staticmethod
    def _fallback_judge(*, question_title: str, expected_answer: str, answer: str) -> dict[str, Any]:
        answer_tokens = set(ReviewService._tokenize_for_judgement(answer))
        expected_tokens = set(ReviewService._tokenize_for_judgement(expected_answer))
        overlap = answer_tokens & expected_tokens
        coverage = (len(overlap) / len(expected_tokens)) if expected_tokens else 0.0

        if not answer_tokens:
            correctness = "incorrect"
            suggested_rating = 1
        elif answer.strip().lower() == expected_answer.strip().lower() or answer_tokens.issubset(expected_tokens) or coverage >= 0.66:
            correctness = "correct"
            suggested_rating = 3 if coverage < 0.9 else 4
        elif coverage >= 0.25:
            correctness = "partial"
            suggested_rating = 2
        else:
            correctness = "incorrect"
            suggested_rating = 1

        explanation = (
            f"{question_title} 的参考要点是：{expected_answer[:180]}。"
            f"你的回答中命中了 {len(overlap)} 个关键片段，系统建议评分为 {suggested_rating}。"
            "若你认为自己表达正确但措辞不同，可以手动覆盖评分后继续复习。"
        )
        return {
            "card_id": 0,
            "answer": answer,
            "expected_answer": expected_answer,
            "suggested_rating": suggested_rating,
            "correctness": correctness,
            "explanation": explanation,
            "judge_status": "fallback",
            "judge_error": "LLM provider unavailable or response invalid",
        }

    @staticmethod
    def _build_review_judge_prompt(
        *,
        title: str,
        source_note_title: str | None,
        expected_answer: str,
        learner_answer: str,
    ) -> str:
        return (
            "请判断以下复习作答，并给出最小可行讲解。返回 JSON，字段固定为 "
            "suggested_rating(1-4), correctness(correct|partial|incorrect|unknown), explanation。\n\n"
            f"知识点标题：{title}\n"
            f"来源笔记：{source_note_title or '未知'}\n"
            f"标准答案/参考要点：{expected_answer}\n"
            f"用户答案：{learner_answer}\n\n"
            "评分口径：1=Again, 2=Hard, 3=Good, 4=Easy。"
            "explanation 要简短，说明哪里答对/遗漏，并提醒用户可确认或覆盖评分。"
        )

    @staticmethod
    def _parse_review_judge_response(content: str) -> dict[str, Any]:
        raw = (content or "").strip()
        if not raw:
            raise ValueError("empty judge response")
        if raw.startswith("```"):
            fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
            if fenced:
                raw = fenced.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            if not match:
                raise
            return json.loads(match.group(0))

    @staticmethod
    def _compose_review_log_note(
        *,
        note: str | None,
        answer: str | None,
        ai_judge: dict | None,
        final_rating: int,
    ) -> str | None:
        base_note = (note or "").strip()
        meta_lines: list[str] = []
        if answer and answer.strip():
            meta_lines.append(f"answer={answer.strip()[:500]}")
        if ai_judge:
            suggested_rating = ai_judge.get("suggested_rating")
            correctness = ai_judge.get("correctness")
            judge_status = ai_judge.get("judge_status")
            explanation = str(ai_judge.get("explanation") or "").strip()
            if suggested_rating is not None:
                meta_lines.append(f"ai_suggested_rating={suggested_rating}")
            if correctness:
                meta_lines.append(f"ai_correctness={correctness}")
            if judge_status:
                meta_lines.append(f"ai_judge_status={judge_status}")
            if explanation:
                meta_lines.append(f"ai_explanation={explanation[:500]}")
        if meta_lines:
            meta_lines.append(f"final_rating={final_rating}")
            meta_block = "[AI Review]\n" + "\n".join(meta_lines)
            return f"{base_note}\n\n{meta_block}".strip()
        return base_note or None

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
