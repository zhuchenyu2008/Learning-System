from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from textwrap import dedent

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
from app.services.note_lifecycle_service import NoteLifecycleService
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
            combined_source = ArtifactService._combine_note_sources(notes, artifact_type)
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
    def _combine_note_sources(notes: list[Note], artifact_type: ArtifactType) -> str:
        parts: list[str] = []
        for note in notes:
            content = SafeFileService.read_text(Path(note.relative_path))
            prepared_content = ArtifactService._prepare_note_content_for_artifact(content, artifact_type)
            parts.append(f"# {note.title}\n\n{prepared_content}".strip())
        return "\n\n".join(part for part in parts if part.strip())

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
            system_prompt = "你是学习总结助手，请严格输出适合知识复习的内容。"
            source_text = combined_source[:16000]
        else:
            base_prompt = dedent(
                """
                请根据以下学习笔记生成 Mermaid `mindmap` 图，目标是帮助复习，避免内容混乱。

                严格要求：
                1. 只输出 Mermaid mindmap 正文，不要输出解释、前后缀、Markdown、代码围栏。
                2. 第一行必须是 `mindmap`。
                3. 必须且只能有一个根节点，格式为 `root((主题))`。
                4. 根节点下保留 3-6 个一级分支；每个一级分支最多 2-4 个二级分支；总节点数尽量控制在 12-24 个。
                5. 节点文案必须简短，优先用名词或短语，单个节点不超过 18 个汉字；禁止整句复述、段落、举例展开。
                6. 只保留对理解主题最关键的概念、关系、分类、步骤；不要抄写元信息、路径、标签、前言、附录、原始摘录、代码示例。
                7. 如果笔记里同时出现多块内容，只抽取共同主题与高频主线；拿不准时宁可少写，不要堆砌。
                8. 禁止输出序号风格的大纲（如“1. 2. 3.”、“一、二、三、”）作为节点前缀。
                9. 不要生成 flowchart、graph、timeline、classDiagram 等其他 Mermaid 类型。
                """
            ).strip()
            system_prompt = "你是知识复习导图助手。输出必须稳定、克制、结构化，只能返回 Mermaid mindmap 正文。"
            source_text = ArtifactService._trim_for_mindmap_prompt(combined_source)
        if prompt_extra:
            base_prompt = f"{base_prompt}\n\n额外要求：{prompt_extra}"

        result = await adapter.chat(
            [OpenAIMessage(role="user", content=f"{base_prompt}\n\n学习资料：\n{source_text}")],
            system_prompt=system_prompt,
        )
        return result.content

    @staticmethod
    def _wrap_markdown(artifact_type: ArtifactType, title: str, body: str) -> str:
        if artifact_type == ArtifactType.MINDMAP:
            sanitized_body = ArtifactService._sanitize_mermaid_body(body)
            return f"# {title}\n\n```mermaid\n{sanitized_body}\n```\n"
        return f"# {title}\n\n{body.strip()}\n"

    @staticmethod
    def _sanitize_mermaid_body(body: str) -> str:
        normalized = body.replace("\r\n", "\n").strip()
        if not normalized:
            return "mindmap\n  root((空思维导图))"

        fenced_match = re.fullmatch(r"```(?:\s*mermaid)?\s*\n?([\s\S]*?)\n?```", normalized, flags=re.IGNORECASE)
        if fenced_match:
            normalized = fenced_match.group(1).strip()

        normalized = re.sub(r"^```\s*mermaid\s*$", "", normalized, flags=re.IGNORECASE | re.MULTILINE)
        normalized = re.sub(r"^```\s*$", "", normalized, flags=re.MULTILINE)
        normalized = normalized.strip()

        if normalized.lower().startswith("mermaid\n"):
            normalized = normalized.split("\n", 1)[1].strip()
        elif normalized.lower() == "mermaid":
            normalized = ""

        if "mindmap" in normalized.lower():
            match = re.search(r"(?im)^mindmap\s*$", normalized)
            if match:
                normalized = normalized[match.start():].strip()

        if not normalized:
            return "mindmap\n  root((空思维导图))"

        lines = [line.rstrip() for line in normalized.split("\n") if line.strip()]
        cleaned_lines: list[str] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if index == 0:
                cleaned_lines.append("mindmap")
                continue

            if stripped.startswith("%%"):
                continue

            indent_match = re.match(r"^(\s*)", line)
            indent = indent_match.group(1) if indent_match else ""
            if len(indent) < 2:
                indent = "  "
            content = stripped.lstrip("-").strip()
            content = re.sub(r"^(?:\d+[\.\)]|[一二三四五六七八九十]+[、\.])\s*", "", content)
            content = content.replace("`", "")
            if not content:
                continue
            cleaned_lines.append(f"{indent}{content}")

        if len(cleaned_lines) == 1:
            cleaned_lines.append("  root((空思维导图))")
        elif not any(line.strip().startswith("root(") or line.strip().startswith("root[") or line.strip().startswith("root{") for line in cleaned_lines[1:]):
            first_node = cleaned_lines[1].strip()
            cleaned_lines[1] = f"  root(({first_node[:24]}))"

        return "\n".join(cleaned_lines) or "mindmap\n  root((空思维导图))"

    @staticmethod
    def _prepare_note_content_for_artifact(content: str, artifact_type: ArtifactType) -> str:
        normalized = content.replace("\r\n", "\n")
        normalized = re.sub(r"^---\n[\s\S]*?\n---\n?", "", normalized, count=1)
        normalized = normalized.strip()

        if artifact_type != ArtifactType.MINDMAP:
            return normalized

        text = normalized
        text = re.sub(r"```mermaid[\s\S]*?```", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"^>\s?.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^source_\w+:.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^tags:\s*$[\s\S]*?(?=^#|^##|^---|\Z)", "", text, flags=re.MULTILINE)
        text = re.sub(r"^##\s*(原始提取摘录|原始内容|附录|参考|说明)\s*$[\s\S]*?(?=^##\s+|^#\s+|\Z)", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[-*]\s*\[[ xX]\]\s*", "- ", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _trim_for_mindmap_prompt(combined_source: str, per_section_limit: int = 2200, total_limit: int = 12000) -> str:
        sections = re.split(r"(?=^# )", combined_source, flags=re.MULTILINE)
        trimmed_sections: list[str] = []
        for section in sections:
            cleaned = section.strip()
            if not cleaned:
                continue
            kept_lines: list[str] = []
            in_code_block = False
            for raw_line in cleaned.splitlines():
                line = raw_line.rstrip()
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue
                if not stripped:
                    if kept_lines and kept_lines[-1] != "":
                        kept_lines.append("")
                    continue
                if re.match(r"^source_\w+:", stripped):
                    continue
                if stripped.startswith("title:"):
                    continue
                if stripped.startswith("tags:"):
                    continue
                if stripped.startswith(">"):
                    continue
                kept_lines.append(line)
                preview = "\n".join(kept_lines)
                if len(preview) >= per_section_limit:
                    break
            preview = "\n".join(kept_lines).strip()
            if preview:
                trimmed_sections.append(preview[:per_section_limit].strip())
            candidate = "\n\n".join(trimmed_sections)
            if len(candidate) >= total_limit:
                break
        result = "\n\n".join(trimmed_sections).strip()
        return result[:total_limit].strip() or combined_source[:total_limit].strip()

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

    @staticmethod
    async def delete_artifact(session: AsyncSession, artifact_type: ArtifactType, artifact_id: int) -> dict | None:
        artifact = await session.get(GeneratedArtifact, artifact_id)
        if artifact is None or artifact.artifact_type != artifact_type.value:
            return None

        output_note_id = artifact.output_note_id
        if output_note_id is not None:
            note_delete_result = await NoteLifecycleService.delete_note(session, output_note_id)
            if note_delete_result is not None:
                return {
                    "id": artifact_id,
                    "artifact_id": artifact_id,
                    "output_note_id": output_note_id,
                    "deleted_note_id": note_delete_result.deleted_note_id,
                    "deleted_relative_paths": note_delete_result.deleted_relative_paths,
                }

        await session.delete(artifact)
        await session.commit()
        return {
            "id": artifact_id,
            "artifact_id": artifact_id,
            "output_note_id": output_note_id,
            "deleted_note_id": None,
            "deleted_relative_paths": [],
        }
