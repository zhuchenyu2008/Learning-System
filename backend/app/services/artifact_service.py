from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.openai_compatible import OpenAICompatibleProviderAdapter
from app.models.enums import ArtifactScopeType, ArtifactType, JobType, NoteType
from app.models.generated_artifact import GeneratedArtifact
from app.models.job import Job
from app.models.note import Note
from app.schemas.integrations import OpenAIMessage
from app.services.file_write_service import FileWriteService
from app.services.job_service import JobService
from app.services.review_service import ReviewService
from app.services.safe_file_service import SafeFileService


class ArtifactService:
    @staticmethod
    async def create_summary_job(
        session: AsyncSession,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> Job:
        return await JobService.create_job(
            session,
            JobType.SUMMARY_GENERATION,
            {"scope": scope.value, "note_ids": note_ids, "prompt_extra": prompt_extra},
        )

    @staticmethod
    async def create_mindmap_job(
        session: AsyncSession,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> Job:
        return await JobService.create_job(
            session,
            JobType.MINDMAP_GENERATION,
            {"scope": scope.value, "note_ids": note_ids, "prompt_extra": prompt_extra},
        )

    @staticmethod
    async def execute_summary_job(
        session: AsyncSession,
        job_id: int,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        return await ArtifactService._execute_artifact_job(
            session=session,
            job_id=job_id,
            artifact_type=ArtifactType.SUMMARY,
            scope=scope,
            note_ids=note_ids,
            prompt_extra=prompt_extra,
        )

    @staticmethod
    async def execute_mindmap_job(
        session: AsyncSession,
        job_id: int,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        return await ArtifactService._execute_artifact_job(
            session=session,
            job_id=job_id,
            artifact_type=ArtifactType.MINDMAP,
            scope=scope,
            note_ids=note_ids,
            prompt_extra=prompt_extra,
        )

    @staticmethod
    async def generate_summary(
        session: AsyncSession,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        job = await ArtifactService.create_summary_job(session, scope, note_ids, prompt_extra)
        return await ArtifactService.execute_summary_job(session, job.id, scope, note_ids, prompt_extra)

    @staticmethod
    async def generate_mindmap(
        session: AsyncSession,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        job = await ArtifactService.create_mindmap_job(session, scope, note_ids, prompt_extra)
        return await ArtifactService.execute_mindmap_job(session, job.id, scope, note_ids, prompt_extra)

    @staticmethod
    async def _execute_artifact_job(
        session: AsyncSession,
        job_id: int,
        artifact_type: ArtifactType,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        job = await session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if job.status == "pending":
            await JobService.mark_running(session, job)

        try:
            notes = await ArtifactService._load_notes(session, note_ids)
            combined_source = ArtifactService._combine_note_sources(notes)
            body = await ArtifactService._generate_artifact_body(
                session=session,
                artifact_type=artifact_type,
                combined_source=combined_source,
                prompt_extra=prompt_extra,
            )
            title = ArtifactService._build_title(artifact_type, notes)
            markdown = ArtifactService._wrap_markdown(artifact_type, title, body)
            slug = ArtifactService._build_slug(artifact_type)
            relative_path = ReviewService.artifact_relative_path(artifact_type.value, slug)
            FileWriteService.write_markdown(relative_path, markdown)

            output_note = Note(
                title=title,
                relative_path=relative_path,
                note_type=NoteType(artifact_type.value).value,
                content_hash=ReviewService.hash_content(markdown),
                source_asset_id=None,
                frontmatter_json={
                    "artifact_type": artifact_type.value,
                    "scope": scope.value,
                    "note_ids": note_ids,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            session.add(output_note)
            await session.flush()

            artifact = GeneratedArtifact(
                artifact_type=artifact_type.value,
                scope_type=scope.value,
                note_ids_json=note_ids,
                prompt_extra=prompt_extra,
                output_note_id=output_note.id,
                status="completed",
            )
            session.add(artifact)
            await session.flush()
            await session.commit()
            await session.refresh(output_note)
            await session.refresh(artifact)

            await JobService.mark_completed(
                session,
                job,
                {
                    "artifact_id": artifact.id,
                    "output_note_id": output_note.id,
                    "relative_path": relative_path,
                    "status": artifact.status,
                },
            )
            return {
                "job": job,
                "artifact": artifact,
                "output_note": output_note,
                "relative_path": relative_path,
            }
        except Exception as exc:  # noqa: BLE001
            await JobService.mark_failed(session, job, str(exc))
            raise

    @staticmethod
    async def _generate_artifact(
        session: AsyncSession,
        artifact_type: ArtifactType,
        job_type: JobType,
        scope: ArtifactScopeType,
        note_ids: list[int],
        prompt_extra: str | None,
    ) -> dict:
        job = await JobService.create_job(
            session,
            job_type,
            {"scope": scope.value, "note_ids": note_ids, "prompt_extra": prompt_extra},
        )
        return await ArtifactService._execute_artifact_job(
            session=session,
            job_id=job.id,
            artifact_type=artifact_type,
            scope=scope,
            note_ids=note_ids,
            prompt_extra=prompt_extra,
        )

    @staticmethod
    async def _load_notes(session: AsyncSession, note_ids: list[int]) -> list[Note]:
        stmt = select(Note).order_by(Note.updated_at.desc(), Note.id.desc())
        if note_ids:
            stmt = stmt.where(Note.id.in_(note_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _combine_note_sources(notes: list[Note]) -> str:
        parts: list[str] = []
        for note in notes:
            content = SafeFileService.read_text(Path(note.relative_path))
            parts.append(f"# {note.title}\n\n{content.strip()}")
        return "\n\n".join(parts)

    @staticmethod
    async def _generate_artifact_body(
        session: AsyncSession,
        artifact_type: ArtifactType,
        combined_source: str,
        prompt_extra: str | None,
    ) -> str:
        adapter = OpenAICompatibleProviderAdapter(session)
        if artifact_type == ArtifactType.SUMMARY:
            base_prompt = (
                "请根据以下学习笔记生成中文 Markdown 总结，突出核心概念、关键结论、复习建议。"
            )
        else:
            base_prompt = (
                "请根据以下学习笔记生成 Mermaid mindmap，返回可直接放入 markdown 代码块的 mindmap 内容。"
            )
        if prompt_extra:
            base_prompt = f"{base_prompt}\n\n额外要求：{prompt_extra}"

        result = await adapter.chat(
            [OpenAIMessage(role="user", content=f"{base_prompt}\n\n学习资料：\n{combined_source[:16000]}")],
            system_prompt="你是学习总结助手，请严格输出适合知识复习的内容。",
        )
        return result.content

    @staticmethod
    def _wrap_markdown(artifact_type: ArtifactType, title: str, body: str) -> str:
        if artifact_type == ArtifactType.MINDMAP:
            return f"# {title}\n\n```mermaid\n{body.strip()}\n```\n"
        return f"# {title}\n\n{body.strip()}\n"

    @staticmethod
    def _build_title(artifact_type: ArtifactType, notes: list[Note]) -> str:
        if notes:
            base = notes[0].title
            suffix = "总结" if artifact_type == ArtifactType.SUMMARY else "思维导图"
            if len(notes) == 1:
                return f"{base} - {suffix}"
            return f"{base} 等{len(notes)}篇 - {suffix}"
        return "全部笔记总结" if artifact_type == ArtifactType.SUMMARY else "全部笔记思维导图"

    @staticmethod
    def _build_slug(artifact_type: ArtifactType) -> str:
        return f"{artifact_type.value}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    async def list_artifacts(session: AsyncSession, artifact_type: ArtifactType) -> list[GeneratedArtifact]:
        result = await session.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.artifact_type == artifact_type.value)
            .order_by(GeneratedArtifact.created_at.desc(), GeneratedArtifact.id.desc())
        )
        return list(result.scalars().all())
