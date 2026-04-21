from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from app.schemas.integrations import GeneratedNoteResult, NoteRetrievalResult, OpenAIMessage, ProviderExtractionResult
from app.services.file_write_service import FileWriteService
from app.services.job_service import JobService
from app.services.note_naming_service import NoteNamingService
from app.services.note_retrieval_service import NoteRetrievalService


@dataclass(slots=True)
class ExtractionQualityAssessment:
    status: str
    business_status: str
    should_fail: bool
    warnings: list[str]
    reason: str | None = None


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
        processed_assets: list[dict[str, Any]] = []

        try:
            await JobService.append_log(
                session,
                job,
                "info",
                "note generation pipeline started",
                stage="ingest",
                total_assets=len(source_asset_ids),
            )
            for index, source_asset_id in enumerate(source_asset_ids, start=1):
                result = await session.execute(select(SourceAsset).where(SourceAsset.id == source_asset_id))
                source_asset = result.scalar_one_or_none()
                if source_asset is None:
                    await JobService.append_log(
                        session,
                        job,
                        "warning",
                        "source asset missing, skipped",
                        stage="ingest",
                        source_asset_id=source_asset_id,
                        asset_index=index,
                    )
                    continue

                note, asset_result = await NoteGenerationService._generate_single_note(
                    session=session,
                    job=job,
                    adapter=adapter,
                    source_asset=source_asset,
                    note_directory=note_directory,
                    force_regenerate=force_regenerate,
                    asset_index=index,
                    total_assets=len(source_asset_ids),
                )
                generated_note_ids.append(note.id)
                written_paths.append(note.relative_path)
                processed_assets.append(asset_result)

            sync_result = None
            if sync_to_obsidian:
                sync_result = ObsidianHeadlessSyncService.sync().model_dump()

            await JobService.mark_completed(
                session,
                job,
                {
                    "generated_note_ids": generated_note_ids,
                    "written_paths": written_paths,
                    "processed_assets": processed_assets,
                    "obsidian_sync": sync_result,
                },
            )
            return {
                "job": job,
                "generated_note_ids": generated_note_ids,
                "written_paths": written_paths,
                "processed_assets": processed_assets,
            }
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
        job: Job,
        adapter: OpenAICompatibleProviderAdapter,
        source_asset: SourceAsset,
        note_directory: str | None,
        force_regenerate: bool,
        asset_index: int,
        total_assets: int,
    ) -> tuple[Note, dict[str, Any]]:
        reuse_directory = note_directory or NoteNamingService.DEFAULT_BASE_DIR

        await JobService.append_log(
            session,
            job,
            "info",
            "source asset ingested",
            stage="ingest",
            source_asset_id=source_asset.id,
            source_path=source_asset.file_path,
            source_type=source_asset.file_type,
            asset_index=asset_index,
            total_assets=total_assets,
        )

        if not force_regenerate:
            existing_result = await session.execute(select(Note).where(Note.source_asset_id == source_asset.id))
            existing_note = existing_result.scalar_one_or_none()
            if existing_note is not None:
                await JobService.append_log(
                    session,
                    job,
                    "info",
                    "existing note reused",
                    stage="write",
                    source_asset_id=source_asset.id,
                    note_id=existing_note.id,
                    relative_path=existing_note.relative_path,
                )
                return existing_note, {
                    "source_asset_id": source_asset.id,
                    "source_path": source_asset.file_path,
                    "source_type": source_asset.file_type,
                    "note_id": existing_note.id,
                    "relative_path": existing_note.relative_path,
                    "status": "reused",
                }

        extraction = await NoteGenerationService._extract_source_text(
            session=session,
            job=job,
            adapter=adapter,
            source_asset=source_asset,
        )
        normalized = await NoteGenerationService._normalize_extracted_text(
            session=session,
            job=job,
            source_asset=source_asset,
            extraction=extraction,
        )
        retrieval = await NoteGenerationService._retrieve_related_context(
            session=session,
            job=job,
            source_asset=source_asset,
            normalized=normalized,
        )
        generated_note = await NoteGenerationService._generate_note_body(
            session=session,
            job=job,
            adapter=adapter,
            source_asset=source_asset,
            normalized=normalized,
            retrieval=retrieval,
        )

        resolved_naming = await NoteNamingService.resolve_note_naming(
            session,
            raw_subject=generated_note.subject,
            raw_title=generated_note.title,
            generated_at=datetime.now(timezone.utc),
            note_directory=reuse_directory,
        )
        generated_note.title = resolved_naming.final_title
        generated_note.subject = resolved_naming.subject

        markdown = NoteGenerationService._build_markdown(
            source_asset,
            normalized,
            retrieval,
            generated_note,
            resolved_naming.subject_slug,
            resolved_naming.relative_path,
        )
        write_result = FileWriteService.write_markdown(resolved_naming.relative_path, markdown)
        await JobService.append_log(
            session,
            job,
            "info",
            "note markdown written",
            stage="write",
            source_asset_id=source_asset.id,
            relative_path=write_result.relative_path,
            bytes_written=write_result.bytes_written,
        )
        content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()

        existing_result = await session.execute(select(Note).where(Note.relative_path == write_result.relative_path))
        note = existing_result.scalar_one_or_none()
        extraction_frontmatter = {
            "extracted_text_preview": normalized.text[:1000],
            "extraction_metadata": normalized.metadata,
        }
        retrieval_summary = NoteGenerationService._build_retrieval_summary(retrieval)
        generation_frontmatter = {
            "title": generated_note.title,
            "base_title": resolved_naming.base_title,
            "subject": generated_note.subject,
            "subject_slug": resolved_naming.subject_slug,
            "warnings": generated_note.warnings,
            "confidence": generated_note.confidence,
            "summary": generated_note.summary,
            "relative_path": write_result.relative_path,
        }
        if note is None:
            note = Note(
                title=generated_note.title,
                relative_path=write_result.relative_path,
                note_type=NoteType.SOURCE_NOTE.value,
                content_hash=content_hash,
                source_asset_id=source_asset.id,
                frontmatter_json={
                    "source_asset_id": source_asset.id,
                    "source_path": source_asset.file_path,
                    "generated": True,
                    "subject": generated_note.subject,
                    "subject_slug": resolved_naming.subject_slug,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "relative_path": write_result.relative_path,
                    "extraction": extraction_frontmatter,
                    "retrieval_summary": retrieval_summary,
                    "generation": generation_frontmatter,
                },
            )
        else:
            note.title = generated_note.title
            note.relative_path = write_result.relative_path
            note.note_type = NoteType.SOURCE_NOTE.value
            note.content_hash = content_hash
            note.source_asset_id = source_asset.id
            note.frontmatter_json = {
                **(note.frontmatter_json or {}),
                "source_asset_id": source_asset.id,
                "source_path": source_asset.file_path,
                "generated": True,
                "subject": generated_note.subject,
                "subject_slug": resolved_naming.subject_slug,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "relative_path": write_result.relative_path,
                "extraction": extraction_frontmatter,
                "retrieval_summary": retrieval_summary,
                "generation": generation_frontmatter,
            }
        session.add(note)
        await session.commit()
        await session.refresh(note)
        await JobService.append_log(
            session,
            job,
            "info",
            "note record saved",
            stage="write",
            source_asset_id=source_asset.id,
            note_id=note.id,
            relative_path=note.relative_path,
        )
        return note, {
            "source_asset_id": source_asset.id,
            "source_path": source_asset.file_path,
            "source_type": source_asset.file_type,
            "note_id": note.id,
            "relative_path": note.relative_path,
            "status": "generated",
            "extracted_text_chars": len(normalized.text),
            "extraction_metadata": normalized.metadata,
            "retrieval_summary": retrieval_summary,
            "generation_result": generated_note.model_dump(exclude={"raw_text"}),
        }

    @staticmethod
    async def _extract_source_text(
        session: AsyncSession,
        job: Job,
        adapter: OpenAICompatibleProviderAdapter,
        source_asset: SourceAsset,
    ) -> ProviderExtractionResult:
        extraction = await adapter.extract_content(source_asset.file_path, SourceFileType(source_asset.file_type))
        extraction_metadata = extraction.metadata or {}
        log_extra: dict[str, Any] = {
            "stage": "extract",
            "source_asset_id": source_asset.id,
            "source_type": source_asset.file_type,
            "extracted_chars": len(extraction.text or ""),
            "extraction_mode": extraction_metadata.get("mode"),
        }
        if Path(source_asset.file_path).suffix.lower() == ".docx":
            docx_metadata = extraction_metadata.get("docx") or {}
            log_extra.update(
                {
                    "docx_extractor": docx_metadata.get("extractor"),
                    "docx_fallback_used": docx_metadata.get("fallback_used"),
                    "docx_fallback_reason": docx_metadata.get("fallback_reason"),
                    "docx_paragraph_count": docx_metadata.get("paragraph_count"),
                    "docx_table_count": docx_metadata.get("table_count"),
                    "docx_table_cell_count": docx_metadata.get("table_cell_count"),
                    "docx_line_break_count": docx_metadata.get("line_break_count"),
                    "docx_has_document_xml": docx_metadata.get("has_document_xml"),
                }
            )
        await JobService.append_log(
            session,
            job,
            "info",
            "source text extracted",
            **log_extra,
        )
        return extraction

    @staticmethod
    async def _normalize_extracted_text(
        session: AsyncSession,
        job: Job,
        source_asset: SourceAsset,
        extraction: ProviderExtractionResult,
    ) -> ProviderExtractionResult:
        source_type = SourceFileType(source_asset.file_type)
        normalized_text = extraction.text or ""
        normalized_metadata = dict(extraction.metadata or {})
        normalized_metadata["pipeline_stage"] = "normalization"
        normalized_metadata["source_type"] = source_asset.file_type

        if source_type == SourceFileType.PDF:
            normalized_text = PdfProcessingService.clean_extracted_text(normalized_text)
            normalized_metadata.setdefault("normalization_mode", "pdf_text_cleanup")
        else:
            normalized_text = PdfProcessingService.clean_extracted_text(normalized_text)
            normalized_metadata.setdefault("normalization_mode", "plain_text_cleanup")

        normalized_text = normalized_text.strip()
        normalized_metadata["normalized_char_count"] = len(normalized_text)
        normalized = ProviderExtractionResult(text=normalized_text, metadata=normalized_metadata)
        quality_assessment = NoteGenerationService._assess_extraction_quality(source_type, normalized)
        normalized.metadata["quality_assessment"] = {
            "status": quality_assessment.status,
            "business_status": quality_assessment.business_status,
            "should_fail": quality_assessment.should_fail,
            "warnings": quality_assessment.warnings,
            "reason": quality_assessment.reason,
        }
        await JobService.append_log(
            session,
            job,
            "info",
            "extracted text normalized",
            stage="normalize",
            source_asset_id=source_asset.id,
            normalized_chars=len(normalized.text),
            normalization_mode=normalized_metadata.get("normalization_mode"),
            quality_status=quality_assessment.status,
            business_status=quality_assessment.business_status,
        )
        await NoteGenerationService._enforce_quality_gate(
            session=session,
            job=job,
            source_asset=source_asset,
            normalized=normalized,
            assessment=quality_assessment,
        )
        return normalized

    @staticmethod
    async def _retrieve_related_context(
        session: AsyncSession,
        job: Job,
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
    ) -> NoteRetrievalResult:
        await JobService.append_log(
            session,
            job,
            "info",
            "retrieval started",
            stage="retrieve",
            source_asset_id=source_asset.id,
            normalized_chars=len(normalized.text or ""),
        )
        retrieval = await NoteRetrievalService.retrieve_related_notes(
            session,
            normalized_text=normalized.text,
            source_metadata={
                "source_asset_id": source_asset.id,
                "source_type": source_asset.file_type,
                "source_path": source_asset.file_path,
                "normalization_metadata": normalized.metadata,
            },
        )
        await JobService.append_log(
            session,
            job,
            "info",
            "retrieval completed",
            stage="retrieve",
            source_asset_id=source_asset.id,
            normalized_chars=len(normalized.text or ""),
            matched_count=len(retrieval.matched_note_ids),
            top_paths=retrieval.matched_paths,
            provider_model=retrieval.provider_model,
            retrieval_context_chars=len(retrieval.retrieval_context or ""),
        )
        return retrieval

    @staticmethod
    def _is_placeholder_pdf_text(text: str, metadata: dict[str, Any]) -> bool:
        mode = str(metadata.get("mode") or "")
        source_mode = str(metadata.get("source_mode") or "")
        if mode in {"placeholder", "provider_fallback"}:
            return True
        if source_mode in {"placeholder", "fallback"}:
            return True
        placeholder_hits = len(re.findall(r"\[placeholder extraction\]", text))
        if placeholder_hits >= max(1, int(metadata.get("page_count") or 1)):
            return True
        return False

    @staticmethod
    def _assess_extraction_quality(
        source_type: SourceFileType,
        normalized: ProviderExtractionResult,
    ) -> ExtractionQualityAssessment:
        text = (normalized.text or "").strip()
        metadata = normalized.metadata or {}
        normalized_chars = len(text)
        line_count = len([line for line in text.splitlines() if line.strip()])
        placeholder_hits = len(re.findall(r"\[placeholder extraction\]", text))
        alpha_num_chars = len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", text))
        meaningful_ratio = (alpha_num_chars / normalized_chars) if normalized_chars else 0.0
        repeated_line_ratio = 0.0
        non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if non_empty_lines:
            repeated_line_ratio = 1 - (len(set(non_empty_lines)) / len(non_empty_lines))

        if source_type == SourceFileType.PDF:
            if NoteGenerationService._is_placeholder_pdf_text(text, metadata):
                return ExtractionQualityAssessment(
                    status="failed",
                    business_status="failed",
                    should_fail=True,
                    warnings=[],
                    reason="pdf_placeholder_extraction",
                )
            if normalized_chars < 80 or meaningful_ratio < 0.3:
                return ExtractionQualityAssessment(
                    status="warning",
                    business_status="degraded",
                    should_fail=False,
                    warnings=["PDF 提取文本较少或噪声偏高，笔记质量可能不足，请人工复核原文。"],
                    reason="pdf_low_information_density",
                )
            return ExtractionQualityAssessment("passed", "passed", False, [])

        if source_type == SourceFileType.IMAGE:
            if normalized_chars < 20 or placeholder_hits > 0 or meaningful_ratio < 0.25:
                return ExtractionQualityAssessment(
                    status="failed",
                    business_status="failed",
                    should_fail=True,
                    warnings=[],
                    reason="image_text_not_meaningful",
                )
            if normalized_chars < 80 or repeated_line_ratio > 0.45:
                return ExtractionQualityAssessment(
                    status="warning",
                    business_status="degraded",
                    should_fail=False,
                    warnings=["图片 OCR 文本较短或重复较多，已生成但需关注识别误差。"],
                    reason="image_low_confidence",
                )
            return ExtractionQualityAssessment("passed", "passed", False, [])

        if source_type == SourceFileType.AUDIO:
            if normalized_chars < 6 or meaningful_ratio < 0.25:
                return ExtractionQualityAssessment(
                    status="failed",
                    business_status="failed",
                    should_fail=True,
                    warnings=[],
                    reason="audio_transcript_not_meaningful",
                )
            if normalized_chars < 60 or line_count <= 1:
                return ExtractionQualityAssessment(
                    status="warning",
                    business_status="degraded",
                    should_fail=False,
                    warnings=["音频转写内容较短，可能只覆盖片段信息，建议人工抽查。"],
                    reason="audio_short_transcript",
                )
            return ExtractionQualityAssessment("passed", "passed", False, [])

        if source_type in {SourceFileType.TEXT, SourceFileType.MARKDOWN}:
            docx_metadata = metadata.get("docx") if isinstance(metadata, dict) else None
            if isinstance(docx_metadata, dict):
                if docx_metadata.get("fallback_used") and normalized_chars < 20:
                    return ExtractionQualityAssessment(
                        status="failed",
                        business_status="failed",
                        should_fail=True,
                        warnings=[],
                        reason="docx_fallback_extraction_not_meaningful",
                    )
                if normalized_chars < 20 or meaningful_ratio < 0.2:
                    return ExtractionQualityAssessment(
                        status="warning",
                        business_status="degraded",
                        should_fail=False,
                        warnings=["DOCX 提取文本较短或结构异常，已继续生成，但建议人工核对原文与生成结果。"],
                        reason="docx_low_information_density",
                    )

        return ExtractionQualityAssessment("passed", "passed", False, [])

    @staticmethod
    async def _enforce_quality_gate(
        session: AsyncSession,
        job: Job,
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
        assessment: ExtractionQualityAssessment,
    ) -> None:
        metadata = normalized.metadata or {}
        if assessment.status == "warning":
            await JobService.append_log(
                session,
                job,
                "warning",
                f"{source_asset.file_type} extraction quality degraded",
                stage="normalize",
                source_asset_id=source_asset.id,
                quality_status=assessment.status,
                business_status=assessment.business_status,
                quality_reason=assessment.reason,
                normalized_chars=len(normalized.text or ""),
                warnings=assessment.warnings,
            )
            return

        if not assessment.should_fail:
            return

        message = {
            SourceFileType.PDF.value: "PDF 提取结果不可用于生成笔记：当前仅拿到占位/回退文本，请先配置可用 OCR 提供商，或提供带可抽取文本层的 PDF。",
            SourceFileType.IMAGE.value: "图片提取结果不可用于生成笔记：OCR 文本过短、噪声过高或无法形成有效学习内容，请更换更清晰图片后重试。",
            SourceFileType.AUDIO.value: "音频提取结果不可用于生成笔记：转写内容过短或无有效语义，请确认音频清晰度、时长与语音可辨识度。",
            SourceFileType.TEXT.value: "DOCX 提取结果不可用于生成笔记：文件结构异常或仅提取到极少文本，请检查原始 docx 是否损坏、加密，或主体内容是否主要存在于图片中。",
            SourceFileType.MARKDOWN.value: "DOCX 提取结果不可用于生成笔记：文件结构异常或仅提取到极少文本，请检查原始 docx 是否损坏、加密，或主体内容是否主要存在于图片中。",
        }.get(source_asset.file_type, "提取结果不可用于生成笔记：当前输入质量不足。")

        log_extra: dict[str, Any] = {
            "stage": "normalize",
            "source_asset_id": source_asset.id,
            "extraction_mode": metadata.get("mode"),
            "source_mode": metadata.get("source_mode"),
            "quality_status": assessment.status,
            "business_status": assessment.business_status,
            "quality_reason": assessment.reason,
            "normalized_chars": len(normalized.text or ""),
        }
        docx_metadata = metadata.get("docx") if isinstance(metadata, dict) else None
        if isinstance(docx_metadata, dict):
            log_extra.update(
                {
                    "docx_extractor": docx_metadata.get("extractor"),
                    "docx_fallback_used": docx_metadata.get("fallback_used"),
                    "docx_fallback_reason": docx_metadata.get("fallback_reason"),
                    "docx_paragraph_count": docx_metadata.get("paragraph_count"),
                    "docx_table_count": docx_metadata.get("table_count"),
                    "docx_table_cell_count": docx_metadata.get("table_cell_count"),
                }
            )
        await JobService.append_log(
            session,
            job,
            "error",
            f"{source_asset.file_type} extraction quality gate failed",
            **log_extra,
        )
        raise ValueError(message)

    @staticmethod
    async def _ensure_pdf_quality_gate(
        session: AsyncSession,
        job: Job,
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
    ) -> None:
        metadata = normalized.metadata or {}
        if not NoteGenerationService._is_placeholder_pdf_text(normalized.text, metadata):
            return
        await JobService.append_log(
            session,
            job,
            "error",
            "pdf extraction quality gate failed",
            stage="normalize",
            source_asset_id=source_asset.id,
            extraction_mode=metadata.get("mode"),
            source_mode=metadata.get("source_mode"),
            normalized_chars=len(normalized.text or ""),
        )
        raise ValueError(
            "PDF 提取结果不可用于生成笔记：当前仅拿到占位/回退文本，请先配置可用 OCR 提供商，或提供带可抽取文本层的 PDF。"
        )

    @staticmethod
    async def _generate_note_body(
        session: AsyncSession,
        job: Job,
        adapter: OpenAICompatibleProviderAdapter,
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
        retrieval: NoteRetrievalResult,
    ) -> GeneratedNoteResult:
        prompt = NoteGenerationService._build_prompt(source_asset, normalized, retrieval)
        await JobService.append_log(
            session,
            job,
            "info",
            "llm note generation started",
            stage="generate",
            source_asset_id=source_asset.id,
            normalized_chars=len(normalized.text),
            retrieval_context_chars=len(retrieval.retrieval_context or ""),
        )
        llm_result = await adapter.chat(
            [OpenAIMessage(role="user", content=prompt)],
            system_prompt=(
                "你是学习资料整理助手。请基于当前时间、来源元数据、规范化文本与相关旧笔记摘录，"
                "输出严格 JSON 对象，不要输出代码块，不要输出额外解释。"
                " JSON 至少包含 title、subject、markdown_body，可选 warnings、confidence、summary。"
                " markdown_body 应是适合 Obsidian 的学习笔记正文，优先保留结构、关键概念、定义、例子、结论、易错点与待复习点；"
                "若信息不确定，应在 warnings 或正文中明确标注，不要编造。"
            ),
        )
        if llm_result.raw_response.get("fallback"):
            generated_note = NoteGenerationService._build_fallback_generation_result(source_asset, normalized, retrieval)
        else:
            generated_note = NoteGenerationService._parse_generation_result(llm_result.content)
        quality_warnings = ((normalized.metadata or {}).get("quality_assessment") or {}).get("warnings") or []
        if quality_warnings:
            generated_note.warnings = [*quality_warnings, *generated_note.warnings]
        await JobService.append_log(
            session,
            job,
            "info",
            "llm note generation completed",
            stage="generate",
            source_asset_id=source_asset.id,
            generated_chars=len(llm_result.content or ""),
            generated_title=generated_note.title,
            generated_subject=generated_note.subject,
        )
        return generated_note

    @staticmethod
    def _build_prompt(
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
        retrieval: NoteRetrievalResult,
    ) -> str:
        source_type = SourceFileType(source_asset.file_type)
        metadata = normalized.metadata or {}
        now_utc = datetime.now(timezone.utc)
        source_metadata = {
            "source_asset_id": source_asset.id,
            "source_type": source_asset.file_type,
            "source_name": Path(source_asset.file_path).name,
            "source_path": source_asset.file_path,
            "extraction_metadata": metadata,
        }
        retrieval_summary = NoteGenerationService._build_retrieval_summary(retrieval)

        sections = [
            "请基于以下上下文生成结构化学习笔记结果。",
            f"current_datetime_utc: {now_utc.isoformat()}",
            "source_metadata:\n" + yaml.safe_dump(source_metadata, allow_unicode=True, sort_keys=False).strip(),
            "retrieval_summary:\n" + yaml.safe_dump(retrieval_summary, allow_unicode=True, sort_keys=False).strip(),
            "normalized_text:\n" + normalized.text[:12000],
            "retrieved_context:\n" + (retrieval.retrieval_context or "无命中，可留空参考。"),
        ]

        if source_type == SourceFileType.PDF:
            sections.append(PdfProcessingService.build_pdf_prompt(Path(source_asset.file_path), normalized.text, metadata))
            sections.append(PdfProcessingService.build_model_ready_context(Path(source_asset.file_path), normalized.text, metadata))

        sections.append(
            "输出 JSON 字段要求:\n"
            "1. title: 核心主题标题，不要包含日期时间后缀；\n"
            "2. subject: 稳定学科名；\n"
            "3. markdown_body: 最终 Markdown 正文，不要包含外层 frontmatter；\n"
            "4. warnings: 可选，字符串数组；\n"
            "5. confidence: 可选，0~1 数值；\n"
            "6. summary: 可选，1~3 句摘要。"
        )
        return "\n\n".join(section for section in sections if section.strip())

    @staticmethod
    def _parse_generation_result(content: str) -> GeneratedNoteResult:
        raw_text = (content or "").strip()
        if not raw_text:
            raise ValueError("LLM generation returned empty content")

        payload_text = raw_text
        fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fence_match:
            payload_text = fence_match.group(1).strip()

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM generation output is not valid JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("LLM generation output must be a JSON object")

        title = str(payload.get("title") or "").strip()
        subject = str(payload.get("subject") or "").strip()
        markdown_body = str(payload.get("markdown_body") or "").strip()
        if not title or not subject or not markdown_body:
            raise ValueError("LLM generation output missing required fields: title / subject / markdown_body")

        warnings_value = payload.get("warnings")
        warnings: list[str]
        if warnings_value is None:
            warnings = []
        elif isinstance(warnings_value, list):
            warnings = [str(item).strip() for item in warnings_value if str(item).strip()]
        else:
            warnings = [str(warnings_value).strip()] if str(warnings_value).strip() else []

        confidence_value = payload.get("confidence")
        confidence: float | None = None
        if confidence_value is not None:
            try:
                confidence = float(confidence_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("LLM generation output confidence must be numeric") from exc
            if confidence < 0 or confidence > 1:
                raise ValueError("LLM generation output confidence must be between 0 and 1")

        summary = payload.get("summary")
        if summary is not None:
            summary = str(summary).strip() or None

        return GeneratedNoteResult(
            title=title,
            subject=subject,
            markdown_body=markdown_body,
            warnings=warnings,
            confidence=confidence,
            summary=summary,
            raw_text=raw_text,
        )

    @staticmethod
    def _build_retrieval_summary(retrieval: NoteRetrievalResult) -> dict[str, Any]:
        return {
            "query_text": retrieval.query_text,
            "matched_count": len(retrieval.matched_note_ids),
            "matched_note_ids": retrieval.matched_note_ids,
            "matched_paths": retrieval.matched_paths,
            "similarity_scores": retrieval.similarity_scores,
            "provider_model": retrieval.provider_model,
            "retrieval_context_chars": len(retrieval.retrieval_context or ""),
        }

    @staticmethod
    def _build_fallback_generation_result(
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
        retrieval: NoteRetrievalResult,
    ) -> GeneratedNoteResult:
        excerpt = normalized.text.strip()[:1200] or "（无可用文本）"
        retrieval_hint = "有" if retrieval.matched_note_ids else "无"
        return GeneratedNoteResult(
            title=Path(source_asset.file_path).stem,
            subject="未分类",
            markdown_body=(
                "## 摘要\n\n"
                f"- 本笔记由系统 fallback 模式生成。\n"
                f"- 当前来源类型：{source_asset.file_type}。\n"
                f"- 检索上下文命中：{retrieval_hint}。\n\n"
                "## 核心内容\n\n"
                f"{excerpt}"
            ),
            warnings=["当前未配置可用 LLM provider，已使用本地结构化兜底结果。"],
            confidence=0.2,
            summary="本结果由 fallback 逻辑生成，仅用于保证主链可继续执行。",
            raw_text=excerpt,
        )

    @staticmethod
    def _build_markdown(
        source_asset: SourceAsset,
        normalized: ProviderExtractionResult,
        retrieval: NoteRetrievalResult,
        generated_note: GeneratedNoteResult,
        subject_slug: str,
        relative_path: str,
    ) -> str:
        frontmatter = yaml.safe_dump(
            {
                "title": generated_note.title,
                "subject": generated_note.subject,
                "subject_slug": subject_slug,
                "source_type": source_asset.file_type,
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        warnings_section = ""
        if generated_note.warnings:
            warnings_section = "\n\n## 使用提醒\n\n" + "\n".join(f"- {item}" for item in generated_note.warnings)
        return (
            f"---\n{frontmatter}\n---\n\n"
            f"# {generated_note.title}\n\n"
            f"{generated_note.markdown_body.strip()}"
            f"{warnings_section}\n"
        )
