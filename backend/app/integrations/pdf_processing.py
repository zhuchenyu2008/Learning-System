from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.schemas.integrations import ObsidianSyncResult


class PdfProcessingService:
    _PAGE_BREAK_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:[#\-=>]{0,4}\s*)?(?:page|Page|PAGE|页)\s*(\d{1,4})(?:\s*(?:/|of|共)\s*\d{1,4})?(?:\s*[#\-=>]{0,4})?\s*(?:\n|$)"
    )

    @staticmethod
    def build_pdf_prompt(path: Path, extraction_text: str = "", metadata: dict[str, Any] | None = None) -> str:
        metadata = metadata or {}
        page_count = metadata.get("page_count") or metadata.get("estimated_page_count")
        strategy = metadata.get("page_strategy") or "sequential_page_chunks"
        summary_bits = [f"文件名：{path.name}", f"页处理策略：{strategy}"]
        if page_count:
            summary_bits.append(f"页数：{page_count}")
        if metadata.get("has_visual_context"):
            summary_bits.append("含视觉/OCR上下文")
        if metadata.get("source_mode"):
            summary_bits.append(f"提取模式：{metadata['source_mode']}")

        leading_excerpt = PdfProcessingService._limit_chars(extraction_text, 800)
        excerpt_block = f"\n\n提取预览：\n{leading_excerpt}" if leading_excerpt else ""
        return (
            "请基于该 PDF 的逐页内容提取核心结构、关键概念、要点摘要与可转为学习笔记的 Markdown。"
            " 优先保持原文档章节层级；若跨页延续，请在整理时合并同一小节。"
            " 对 OCR 噪声、页眉页脚、重复页码进行去噪，不要把无意义碎片写入最终笔记。\n"
            + "；".join(summary_bits)
            + excerpt_block
        )

    @staticmethod
    def build_model_ready_context(path: Path, extraction_text: str, metadata: dict[str, Any] | None = None) -> str:
        metadata = metadata or {}
        pages = PdfProcessingService.extract_page_chunks(extraction_text, metadata)
        header_lines = [
            "# 文档提取上下文",
            f"- 文件：{path.name}",
            f"- 类型：pdf",
        ]
        if metadata.get("page_count") or metadata.get("estimated_page_count"):
            header_lines.append(
                f"- 页数：{metadata.get('page_count') or metadata.get('estimated_page_count')}"
            )
        if metadata.get("source_mode"):
            header_lines.append(f"- 提取模式：{metadata['source_mode']}")
        if metadata.get("layout_hint"):
            header_lines.append(f"- 版面提示：{metadata['layout_hint']}")

        body_sections: list[str] = ["\n".join(header_lines)]
        if pages:
            page_sections: list[str] = []
            for index, page_text in pages[:12]:
                cleaned = PdfProcessingService.clean_extracted_text(page_text)
                if not cleaned:
                    continue
                page_sections.append(
                    f"## 第 {index} 页\n\n{PdfProcessingService._limit_chars(cleaned, 1800)}"
                )
            if page_sections:
                body_sections.append("\n\n".join(page_sections))

        if len(body_sections) == 1:
            body_sections.append(
                "## 全文提取\n\n" + PdfProcessingService._limit_chars(PdfProcessingService.clean_extracted_text(extraction_text), 12000)
            )
        return "\n\n".join(section for section in body_sections if section.strip())

    @staticmethod
    def normalize_provider_payload(path: Path, payload: dict[str, Any] | None, fallback_text: str = "") -> tuple[str, dict[str, Any]]:
        payload = payload or {}
        metadata: dict[str, Any] = {
            "source_mode": "provider",
            "has_visual_context": True,
        }

        pages = payload.get("pages") or payload.get("page_results") or payload.get("document", {}).get("pages") or []
        if isinstance(pages, list) and pages:
            normalized_pages: list[str] = []
            for idx, page in enumerate(pages, start=1):
                if isinstance(page, dict):
                    page_number = int(page.get("page") or page.get("page_number") or idx)
                    page_text = PdfProcessingService._coerce_page_text(page)
                else:
                    page_number = idx
                    page_text = str(page)
                cleaned = PdfProcessingService.clean_extracted_text(page_text)
                if cleaned:
                    normalized_pages.append(f"\n\n## Page {page_number}\n{cleaned}")
            if normalized_pages:
                metadata["page_count"] = len(normalized_pages)
                metadata["page_strategy"] = "provider_pages"
                metadata["layout_hint"] = "page_grouped"
                return "".join(normalized_pages).strip(), metadata

        combined_text = (
            payload.get("text")
            or payload.get("content")
            or payload.get("output_text")
            or payload.get("markdown")
            or fallback_text
            or ""
        )
        cleaned_text = PdfProcessingService.clean_extracted_text(combined_text)
        page_chunks = PdfProcessingService.extract_page_chunks(cleaned_text, metadata)
        if page_chunks:
            metadata["page_count"] = len(page_chunks)
            metadata["page_strategy"] = "text_split"
            metadata["layout_hint"] = "page_grouped"
        else:
            metadata["page_strategy"] = "single_block"
            metadata["layout_hint"] = "linear"
        estimated_page_count = PdfProcessingService.estimate_page_count(path)
        if estimated_page_count and not metadata.get("page_count"):
            metadata["estimated_page_count"] = estimated_page_count
        return cleaned_text, metadata

    @staticmethod
    def extract_page_chunks(text: str, metadata: dict[str, Any] | None = None) -> list[tuple[int, str]]:
        metadata = metadata or {}
        if not text.strip():
            return []

        if "\f" in text:
            chunks = [PdfProcessingService.clean_extracted_text(chunk) for chunk in text.split("\f")]
            return [(idx, chunk) for idx, chunk in enumerate(chunks, start=1) if chunk]

        matches = list(PdfProcessingService._PAGE_BREAK_PATTERN.finditer(text))
        if not matches:
            return []

        page_map: dict[int, str] = {}
        for pos, match in enumerate(matches):
            page_number = int(match.group(1))
            start = match.end()
            end = matches[pos + 1].start() if pos + 1 < len(matches) else len(text)
            chunk = PdfProcessingService.clean_extracted_text(text[start:end])
            if not chunk:
                continue
            if page_number in page_map:
                if chunk in page_map[page_number]:
                    continue
                page_map[page_number] = PdfProcessingService.clean_extracted_text(
                    page_map[page_number] + "\n" + chunk
                )
            else:
                page_map[page_number] = chunk
        return sorted(page_map.items(), key=lambda item: item[0])

    @staticmethod
    def clean_extracted_text(text: str) -> str:
        if not text:
            return ""

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(
            r"(?<=\S)-\n\s*(?:(?:page|Page|PAGE|页)\s*\d{1,4}(?:\s*/\s*\d{1,4})?\s*)?\n?\s*(?=\S)",
            "",
            normalized,
        )
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        cleaned_lines: list[str] = []
        previous_fingerprint = ""
        for raw_line in normalized.split("\n"):
            line = raw_line.strip()
            if not line:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue
            if re.fullmatch(r"(?:page|Page|PAGE|页)?\s*\d{1,4}(?:\s*/\s*\d{1,4})?", line):
                continue
            fingerprint = re.sub(r"\W+", "", line).lower()
            if fingerprint and fingerprint == previous_fingerprint:
                continue
            cleaned_lines.append(line)
            previous_fingerprint = fingerprint

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def estimate_page_count(path: Path) -> int | None:
        if path.suffix.lower() != ".pdf" or not path.exists():
            return None
        try:
            content = path.read_bytes()
        except OSError:
            return None

        matches = re.findall(rb"/Type\s*/Page\b", content)
        return len(matches) or None

    @staticmethod
    def _coerce_page_text(page: dict[str, Any]) -> str:
        direct = page.get("text") or page.get("content") or page.get("markdown")
        if direct:
            return str(direct)

        blocks = page.get("blocks") or page.get("lines") or []
        if isinstance(blocks, list):
            text_parts: list[str] = []
            for block in blocks:
                if isinstance(block, dict):
                    candidate = block.get("text") or block.get("content") or block.get("value")
                else:
                    candidate = str(block)
                if candidate:
                    text_parts.append(str(candidate))
            return "\n".join(text_parts)
        return ""

    @staticmethod
    def _limit_chars(text: str, max_chars: int) -> str:
        return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."
