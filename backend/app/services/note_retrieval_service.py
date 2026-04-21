from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.openai_compatible import OpenAICompatibleProviderAdapter
from app.models.note import Note
from app.schemas.integrations import NoteRetrievalResult, RetrievalMatch
from app.services.safe_file_service import SafeFileService


@dataclass(slots=True)
class RetrievalCandidate:
    note_id: int
    relative_path: str
    snippet: str


class NoteRetrievalService:
    DEFAULT_TOP_K = 3
    MAX_QUERY_CHARS = 2000
    MAX_CONTEXT_CHARS = 3000
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 120

    @staticmethod
    async def retrieve_related_notes(
        session: AsyncSession,
        normalized_text: str,
        source_metadata: dict[str, Any] | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> NoteRetrievalResult:
        query_text = NoteRetrievalService._build_query_text(normalized_text, source_metadata)
        if not query_text:
            return NoteRetrievalResult(
                query_text="",
                matched_note_ids=[],
                matched_paths=[],
                snippets=[],
                similarity_scores=[],
                provider_model=None,
                retrieval_context="",
                matches=[],
            )

        candidates = await NoteRetrievalService._load_candidates(session)
        if not candidates:
            return NoteRetrievalResult(
                query_text=query_text,
                matched_note_ids=[],
                matched_paths=[],
                snippets=[],
                similarity_scores=[],
                provider_model=None,
                retrieval_context="",
                matches=[],
            )

        adapter = OpenAICompatibleProviderAdapter(session)
        embedding_result = await adapter.embed([query_text, *[candidate.snippet for candidate in candidates]])
        if len(embedding_result.vectors) < 1 + len(candidates):
            raise ValueError("Embedding provider returned incomplete vectors for retrieval")

        query_vector = embedding_result.vectors[0]
        scored_matches: list[RetrievalMatch] = []
        for candidate, vector in zip(candidates, embedding_result.vectors[1:], strict=False):
            score = NoteRetrievalService._cosine_similarity(query_vector, vector)
            scored_matches.append(
                RetrievalMatch(
                    note_id=candidate.note_id,
                    relative_path=candidate.relative_path,
                    snippet=candidate.snippet,
                    score=score,
                )
            )

        scored_matches.sort(key=lambda item: item.score, reverse=True)
        top_matches = scored_matches[: max(0, top_k)]
        retrieval_context = NoteRetrievalService._build_retrieval_context(top_matches)
        return NoteRetrievalResult(
            query_text=query_text,
            matched_note_ids=[match.note_id for match in top_matches],
            matched_paths=[match.relative_path for match in top_matches],
            snippets=[match.snippet for match in top_matches],
            similarity_scores=[match.score for match in top_matches],
            provider_model=embedding_result.model_name,
            retrieval_context=retrieval_context,
            matches=top_matches,
        )

    @staticmethod
    def _build_query_text(normalized_text: str, source_metadata: dict[str, Any] | None = None) -> str:
        cleaned = " ".join((normalized_text or "").split()).strip()
        if not cleaned:
            return ""

        segments = [cleaned[: NoteRetrievalService.MAX_QUERY_CHARS]]
        if source_metadata:
            source_type = source_metadata.get("source_type")
            source_path = source_metadata.get("source_path")
            if source_type:
                segments.append(f"source_type={source_type}")
            if source_path:
                segments.append(f"source_path={source_path}")
        return "\n".join(segment for segment in segments if segment)

    @staticmethod
    async def _load_candidates(session: AsyncSession) -> list[RetrievalCandidate]:
        result = await session.execute(select(Note).order_by(Note.updated_at.desc(), Note.id.desc()))
        notes = list(result.scalars().all())
        candidates: list[RetrievalCandidate] = []
        for note in notes:
            try:
                content = SafeFileService.read_text(note.relative_path)
            except (FileNotFoundError, OSError, ValueError):
                continue
            for snippet in NoteRetrievalService._chunk_text(content):
                candidates.append(
                    RetrievalCandidate(
                        note_id=note.id,
                        relative_path=note.relative_path,
                        snippet=snippet,
                    )
                )
        return candidates

    @staticmethod
    def _chunk_text(content: str) -> list[str]:
        normalized = "\n".join(line.rstrip() for line in content.splitlines())
        paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
        if paragraphs:
            chunks: list[str] = []
            current = ""
            for paragraph in paragraphs:
                candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
                if len(candidate) <= NoteRetrievalService.CHUNK_SIZE:
                    current = candidate
                    continue
                if current:
                    chunks.append(current[: NoteRetrievalService.CHUNK_SIZE])
                if len(paragraph) <= NoteRetrievalService.CHUNK_SIZE:
                    current = paragraph
                else:
                    chunks.extend(NoteRetrievalService._slice_long_text(paragraph))
                    current = ""
            if current:
                chunks.append(current[: NoteRetrievalService.CHUNK_SIZE])
            return chunks
        return NoteRetrievalService._slice_long_text(normalized)

    @staticmethod
    def _slice_long_text(content: str) -> list[str]:
        cleaned = " ".join(content.split())
        if not cleaned:
            return []
        step = max(1, NoteRetrievalService.CHUNK_SIZE - NoteRetrievalService.CHUNK_OVERLAP)
        chunks = []
        for start in range(0, len(cleaned), step):
            chunk = cleaned[start : start + NoteRetrievalService.CHUNK_SIZE].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = sqrt(sum(value * value for value in left))
        right_norm = sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _build_retrieval_context(matches: list[RetrievalMatch]) -> str:
        if not matches:
            return ""

        sections = ["以下是相关旧笔记摘录，仅作辅助参考："]
        current_chars = len(sections[0])
        for index, match in enumerate(matches, start=1):
            section = (
                f"[{index}] note_id={match.note_id} path={match.relative_path} score={match.score:.4f}\n"
                f"{match.snippet.strip()}"
            )
            if current_chars + len(section) > NoteRetrievalService.MAX_CONTEXT_CHARS:
                break
            sections.append(section)
            current_chars += len(section)
        return "\n\n".join(sections)
