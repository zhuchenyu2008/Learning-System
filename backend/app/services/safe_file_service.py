from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from app.core.config import get_settings


class SafeFileService:
    DOCX_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    @staticmethod
    def get_workspace_root() -> Path:
        settings = get_settings()
        workspace_root = Path(settings.workspace_root).expanduser().resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root

    @staticmethod
    def resolve_workspace_path(relative_path: str | Path) -> Path:
        workspace_root = SafeFileService.get_workspace_root()
        candidate = (workspace_root / Path(relative_path)).resolve()
        if workspace_root != candidate and workspace_root not in candidate.parents:
            raise ValueError("Path escapes workspace root")
        return candidate

    @staticmethod
    def to_relative_path(absolute_path: Path) -> str:
        workspace_root = SafeFileService.get_workspace_root()
        resolved = absolute_path.resolve()
        if workspace_root != resolved and workspace_root not in resolved.parents:
            raise ValueError("Path escapes workspace root")
        return resolved.relative_to(workspace_root).as_posix()

    @staticmethod
    def read_text(relative_path: str | Path, encoding: str = "utf-8") -> str:
        path = SafeFileService.resolve_workspace_path(relative_path)
        if path.suffix.lower() == ".docx":
            return SafeFileService.extract_docx_text_and_metadata(path)[0]
        return path.read_text(encoding=encoding, errors="ignore")

    @staticmethod
    def read_bytes(relative_path: str | Path) -> bytes:
        path = SafeFileService.resolve_workspace_path(relative_path)
        return path.read_bytes()

    @staticmethod
    def write_text(relative_path: str | Path, content: str, encoding: str = "utf-8") -> Path:
        path = SafeFileService.resolve_workspace_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path

    @staticmethod
    def write_bytes(relative_path: str | Path, content: bytes) -> Path:
        path = SafeFileService.resolve_workspace_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    @staticmethod
    def delete_file(relative_path: str | Path) -> None:
        path = SafeFileService.resolve_workspace_path(relative_path)
        try:
            path.unlink()
        except FileNotFoundError:
            return

    @staticmethod
    def sha256_for_path(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def extract_docx_text_and_metadata(path: Path) -> tuple[str, dict[str, object]]:
        metadata: dict[str, object] = {
            "container": "docx",
            "suffix": path.suffix.lower(),
            "file_size_bytes": path.stat().st_size if path.exists() else None,
        }
        try:
            with zipfile.ZipFile(path) as archive:
                archive_names = archive.namelist()
                metadata.update(
                    {
                        "zip_entry_count": len(archive_names),
                        "has_document_xml": "word/document.xml" in archive_names,
                        "has_numbering_xml": "word/numbering.xml" in archive_names,
                        "has_styles_xml": "word/styles.xml" in archive_names,
                        "has_footnotes_xml": "word/footnotes.xml" in archive_names,
                        "has_endnotes_xml": "word/endnotes.xml" in archive_names,
                    }
                )
                document_xml = archive.read("word/document.xml")
        except KeyError:
            fallback_text = path.read_text(encoding="utf-8", errors="ignore")
            metadata.update(
                {
                    "extractor": "docx_zip_missing_document_xml_fallback",
                    "fallback_used": True,
                    "fallback_reason": "missing_word_document_xml",
                    "extracted_char_count": len(fallback_text),
                }
            )
            return fallback_text, metadata
        except (zipfile.BadZipFile, OSError):
            fallback_text = path.read_text(encoding="utf-8", errors="ignore")
            metadata.update(
                {
                    "extractor": "docx_bad_zip_fallback",
                    "fallback_used": True,
                    "fallback_reason": "bad_zip_or_os_error",
                    "extracted_char_count": len(fallback_text),
                }
            )
            return fallback_text, metadata

        try:
            root = ET.fromstring(document_xml)
        except ET.ParseError:
            fallback_text = path.read_text(encoding="utf-8", errors="ignore")
            metadata.update(
                {
                    "extractor": "docx_xml_parse_fallback",
                    "fallback_used": True,
                    "fallback_reason": "document_xml_parse_error",
                    "extracted_char_count": len(fallback_text),
                }
            )
            return fallback_text, metadata

        block_texts: list[str] = []
        paragraph_count = 0
        table_count = 0
        table_cell_count = 0
        line_break_count = 0

        body = root.find(".//w:body", SafeFileService.DOCX_NAMESPACE)
        if body is not None:
            for child in body:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "p":
                    paragraph_count += 1
                    paragraph_text, paragraph_breaks = SafeFileService._extract_docx_paragraph_text(child)
                    line_break_count += paragraph_breaks
                    if paragraph_text:
                        block_texts.append(paragraph_text)
                elif tag == "tbl":
                    table_count += 1
                    table_rows: list[str] = []
                    for row in child.findall("./w:tr", SafeFileService.DOCX_NAMESPACE):
                        row_cells: list[str] = []
                        for cell in row.findall("./w:tc", SafeFileService.DOCX_NAMESPACE):
                            table_cell_count += 1
                            cell_lines: list[str] = []
                            for paragraph in cell.findall("./w:p", SafeFileService.DOCX_NAMESPACE):
                                paragraph_text, paragraph_breaks = SafeFileService._extract_docx_paragraph_text(paragraph)
                                line_break_count += paragraph_breaks
                                if paragraph_text:
                                    cell_lines.append(paragraph_text)
                            cell_text = "\n".join(cell_lines).strip()
                            if cell_text:
                                row_cells.append(cell_text)
                        if row_cells:
                            table_rows.append(" | ".join(row_cells))
                    if table_rows:
                        block_texts.append("\n".join(table_rows))

        extracted_text = "\n\n".join(text for text in block_texts if text.strip()).strip()
        if not extracted_text:
            extracted_text = " ".join(text for text in root.itertext() if text and text.strip())
            extracted_text = re.sub(r"\s+", " ", extracted_text).strip()
            metadata["fallback_to_itertext"] = True

        metadata.update(
            {
                "extractor": "docx_xml",
                "fallback_used": bool(metadata.get("fallback_used", False)),
                "paragraph_count": paragraph_count,
                "table_count": table_count,
                "table_cell_count": table_cell_count,
                "line_break_count": line_break_count,
                "extracted_char_count": len(extracted_text),
            }
        )
        return extracted_text, metadata

    @staticmethod
    def _extract_docx_paragraph_text(paragraph: ET.Element) -> tuple[str, int]:
        parts: list[str] = []
        line_break_count = 0
        for node in paragraph.iter():
            tag = node.tag.rsplit("}", 1)[-1]
            if tag == "t":
                parts.append(node.text or "")
            elif tag in {"br", "cr"}:
                parts.append("\n")
                line_break_count += 1
            elif tag == "tab":
                parts.append("\t")
        paragraph_text = "".join(parts)
        paragraph_text = re.sub(r"[ \t]+", " ", paragraph_text)
        paragraph_text = re.sub(r"\n{3,}", "\n\n", paragraph_text)
        return paragraph_text.strip(), line_break_count

    @staticmethod
    def _read_docx_text(path: Path) -> str:
        return SafeFileService.extract_docx_text_and_metadata(path)[0]
