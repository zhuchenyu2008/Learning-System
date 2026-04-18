from __future__ import annotations

import hashlib
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.obsidian_sync import ObsidianHeadlessSyncService
from app.integrations.openai_compatible import OpenAICompatibleProviderAdapter
from app.integrations.pdf_processing import PdfProcessingService
from app.models.enums import JobType, NoteType, SourceFileType
from app.models.job import Job
from app.models.note import Note
from app.models.source_asset import SourceAsset
from app.schemas.integrations import OpenAIMessage, ProviderExtractionResult
from app.services.file_write_service import FileWriteService
from app.services.job_service import JobService


class NoteGenerationService:
    @staticmethod
    async def create_job_for_assets(
        session: AsyncSession,
        source_asset_ids: list[int],
        note_directory: str | None = None,
        force_regenerate: bool = False,
        sync_to_obsidian: bool = False,
    ) -> Job:
        return await JobService.create_job(
            session,
            JobType.NOTE_GENERATION,
            {
                "source_asset_ids": source_asset_ids,
                "note_directory": note_directory,
                "force_regenerate": force_regenerate,
                "sync_to_obsidian": sync_to_obsidian,
            },
        )

    @staticmethod
    async def execute_job_payload(
        session: AsyncSession,
        job_id: int,
        source_asset_ids: list[int],
        note_directory: str | None = None,
        force_regenerate: bool = False,
        sync_to_obsidian: bool = False,
    ) -> dict:
        job = await session.get(Job, job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if job.status == "pending":
            await JobService.mark_running(session, job)

        adapter = OpenAICompatibleProviderAdapter(session)
        generated_note_ids: list[int] = []
        written_paths: list[str] = []

        try:
            for source_asset_id in source_asset_ids:
                result = await session.execute(select(SourceAsset).where(SourceAsset.id == source_asset_id))
                source_asset = result.scalar_one_or_none()
                if source_asset is None:
                    continue

                note = await NoteGenerationService._generate_single_note(
                    session=session,
                    adapter=adapter,
                    source_asset=source_asset,
                    note_directory=note_directory,
                    force_regenerate=force_regenerate,
                )
                generated_note_ids.append(note.id)
                written_paths.append(note.relative_path)

            sync_result = None
            if sync_to_obsidian:
                sync_result = ObsidianHeadlessSyncService.sync().model_dump()

            await JobService.mark_completed(
                session,
                job,
                {
                    "generated_note_ids": generated_note_ids,
                    "written_paths": written_paths,
                    "obsidian_sync": sync_result,
                },
            )
            return {"job": job, "generated_note_ids": generated_note_ids, "written_paths": written_paths}
        except Exception as exc:  # noqa: BLE001
            await JobService.mark_failed(session, job, str(exc))
            raise

    @staticmethod
    async def generate_notes_for_assets(
        session: AsyncSession,
        source_asset_ids: list[int],
        note_directory: str | None = None,
        force_regenerate: bool = False,
        sync_to_obsidian: bool = False,
    ) -> dict:
        job = await NoteGenerationService.create_job_for_assets(
            session,
            source_asset_ids=source_asset_ids,
            note_directory=note_directory,
            force_regenerate=force_regenerate,
            sync_to_obsidian=sync_to_obsidian,
        )
        return await NoteGenerationService.execute_job_payload(
            session=session,
            job_id=job.id,
            source_asset_ids=source_asset_ids,
            note_directory=note_directory,
            force_regenerate=force_regenerate,
            sync_to_obsidian=sync_to_obsidian,
        )

    @staticmethod
    async def _generate_single_note(
        session: AsyncSession,
        adapter: OpenAICompatibleProviderAdapter,
        source_asset: SourceAsset,
        note_directory: str | None,
        force_regenerate: bool,
    ) -> Note:
        base_name = Path(source_asset.file_path).stem
        target_dir = note_directory or "notes/generated"
        relative_path = f"{target_dir.strip('/')}/{base_name}.md"

        if not force_regenerate:
            existing_result = await session.execute(select(Note).where(Note.relative_path == relative_path))
            existing_note = existing_result.scalar_one_or_none()
            if existing_note is not None:
                return existing_note

        extraction = await adapter.extract_content(source_asset.file_path, SourceFileType(source_asset.file_type))
        prompt = NoteGenerationService._build_prompt(source_asset, extraction)

        llm_result = await adapter.chat(
            [OpenAIMessage(role="user", content=prompt)],
            system_prompt=(
                "你是学习资料整理助手，请输出结构化 Markdown 学习笔记。"
                " 优先保留章节结构，明确关键概念、定义、示例、结论与待复习点。"
            ),
        )

        markdown = NoteGenerationService._build_markdown(source_asset, extraction, llm_result.content)
        write_result = FileWriteService.write_markdown(relative_path, markdown)
        content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()

        existing_result = await session.execute(select(Note).where(Note.relative_path == write_result.relative_path))
        note = existing_result.scalar_one_or_none()
        if note is None:
            note = Note(
                title=base_name,
                relative_path=write_result.relative_path,
                note_type=NoteType.SOURCE_NOTE.value,
                content_hash=content_hash,
                source_asset_id=source_asset.id,
                frontmatter_json={
                    "source_asset_id": source_asset.id,
                    "source_path": source_asset.file_path,
                    "generated": True,
                    "extraction": extraction.metadata,
                },
            )
        else:
            note.title = base_name
            note.note_type = NoteType.SOURCE_NOTE.value
            note.content_hash = content_hash
            note.source_asset_id = source_asset.id
            note.frontmatter_json = {
                **(note.frontmatter_json or {}),
                "source_asset_id": source_asset.id,
                "source_path": source_asset.file_path,
                "generated": True,
                "extraction": extraction.metadata,
            }
        session.add(note)
        await session.commit()
        await session.refresh(note)
        return note

    @staticmethod
    def _build_prompt(source_asset: SourceAsset, extraction: ProviderExtractionResult) -> str:
        source_type = SourceFileType(source_asset.file_type)
        metadata = extraction.metadata or {}

        sections = [
            "请根据以下资料生成一份适合 Obsidian 使用的 Markdown 学习笔记。",
            f"来源文件: {source_asset.file_path}",
            f"资料类型: {source_asset.file_type}",
        ]
        if metadata:
            sections.append("提取元数据:\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip())

        if source_type == SourceFileType.PDF:
            sections.append(PdfProcessingService.build_pdf_prompt(Path(source_asset.file_path), extraction.text, metadata))
            sections.append(PdfProcessingService.build_model_ready_context(Path(source_asset.file_path), extraction.text, metadata))
        else:
            cleaned_text = PdfProcessingService.clean_extracted_text(extraction.text)
            sections.append("原始提取内容:\n" + cleaned_text[:12000])

        sections.append(
            "输出要求:\n"
            "1. 使用清晰标题与分级小节；\n"
            "2. 先给出总体摘要，再展开关键概念/流程/例子；\n"
            "3. 若内容噪声较多，请主动去噪并标注不确定处；\n"
            "4. 不要照抄无意义页码、页眉页脚或重复片段。"
        )
        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def _build_markdown(source_asset: SourceAsset, extraction: ProviderExtractionResult, generated_body: str) -> str:
        frontmatter = yaml.safe_dump(
            {
                "title": Path(source_asset.file_path).stem,
                "source_asset_id": source_asset.id,
                "source_path": source_asset.file_path,
                "source_type": source_asset.file_type,
                "extraction": extraction.metadata,
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        excerpt = PdfProcessingService.clean_extracted_text(extraction.text)[:12000]
        return (
            f"---\n{frontmatter}\n---\n\n"
            f"# {Path(source_asset.file_path).stem}\n\n"
            f"## AI 整理笔记\n\n{generated_body.strip()}\n\n"
            f"## 原始提取摘录\n\n````text\n{excerpt}\n````\n"
        )
