from __future__ import annotations

import mimetypes
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.pdf_processing import PdfProcessingService
from app.models.ai_provider_config import AIProviderConfig
from app.models.enums import ProviderType, SourceFileType
from app.schemas.integrations import OpenAIChatResult, OpenAIMessage, ProviderExtractionResult, ProviderHealthResult
from app.services.safe_file_service import SafeFileService


class OpenAICompatibleProviderAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_provider(self, provider_type: ProviderType) -> AIProviderConfig | None:
        result = await self.session.execute(
            select(AIProviderConfig).where(
                AIProviderConfig.provider_type == provider_type.value,
                AIProviderConfig.is_enabled.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_health(self, provider_type: ProviderType) -> ProviderHealthResult:
        provider = await self.get_provider(provider_type)
        return ProviderHealthResult(
            configured=provider is not None,
            provider_type=provider_type.value,
            model_name=provider.model_name if provider else None,
        )

    async def chat(self, messages: list[OpenAIMessage], system_prompt: str | None = None) -> OpenAIChatResult:
        provider = await self.get_provider(ProviderType.LLM)
        if provider is None:
            prompt_parts = [system_prompt] if system_prompt else []
            prompt_parts.extend(message.content for message in messages)
            content = "\n\n".join(part for part in prompt_parts if part)
            return OpenAIChatResult(content=content, raw_response={"fallback": True})

        payload_messages: list[dict] = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(message.model_dump() for message in messages)
        payload = {
            "model": provider.model_name,
            "messages": payload_messages,
            **(provider.extra_json or {}),
        }
        headers = {
            "Authorization": f"Bearer {provider.api_key_encrypted}",
            "Content-Type": "application/json",
        }
        base_url = provider.base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return OpenAIChatResult(content=content, raw_response=data)

    async def extract_content(self, relative_path: str, file_type: SourceFileType) -> ProviderExtractionResult:
        if file_type in {SourceFileType.TEXT, SourceFileType.MARKDOWN, SourceFileType.OTHER}:
            text = SafeFileService.read_text(relative_path)
            return ProviderExtractionResult(text=text, metadata={"mode": "plain_text"})

        absolute_path = SafeFileService.resolve_workspace_path(relative_path)
        if file_type in {SourceFileType.IMAGE, SourceFileType.PDF, SourceFileType.AUDIO, SourceFileType.VIDEO}:
            return await self._extract_multimodal_or_media(absolute_path, file_type)

        text = SafeFileService.read_text(relative_path)
        return ProviderExtractionResult(text=text, metadata={"mode": "fallback_text"})

    async def _extract_multimodal_or_media(self, absolute_path: Path, file_type: SourceFileType) -> ProviderExtractionResult:
        provider_type = ProviderType.OCR if file_type in {SourceFileType.IMAGE, SourceFileType.PDF} else ProviderType.STT
        provider = await self.get_provider(provider_type)
        if provider is None:
            fallback_text = self._build_placeholder_extraction(absolute_path, file_type)
            metadata = {
                "mode": "placeholder",
                "provider_type": provider_type.value,
                "source_mode": "placeholder",
            }
            if file_type == SourceFileType.PDF:
                normalized_text, pdf_meta = PdfProcessingService.normalize_provider_payload(
                    absolute_path,
                    payload={},
                    fallback_text=fallback_text,
                )
                metadata.update(pdf_meta)
                return ProviderExtractionResult(text=normalized_text, metadata=metadata)
            return ProviderExtractionResult(text=fallback_text, metadata=metadata)

        mime_type = mimetypes.guess_type(absolute_path.name)[0] or "application/octet-stream"
        file_bytes = absolute_path.read_bytes()
        files = {"file": (absolute_path.name, file_bytes, mime_type)}
        data = {"model": provider.model_name, **(provider.extra_json or {})}
        headers = {"Authorization": f"Bearer {provider.api_key_encrypted}"}
        base_url = provider.base_url.rstrip("/")
        endpoint = "/audio/transcriptions" if provider_type == ProviderType.STT else "/files/extract"

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{base_url}{endpoint}", data=data, files=files, headers=headers)
            if response.is_success:
                payload = response.json()
                text = payload.get("text") or payload.get("content") or payload.get("output_text") or ""
                metadata = {"mode": "provider", "raw": payload, "source_mode": "provider"}
                if file_type == SourceFileType.PDF:
                    normalized_text, pdf_meta = PdfProcessingService.normalize_provider_payload(
                        absolute_path,
                        payload=payload,
                        fallback_text=text,
                    )
                    metadata.update(pdf_meta)
                    return ProviderExtractionResult(text=normalized_text, metadata=metadata)
                if file_type == SourceFileType.IMAGE:
                    text = PdfProcessingService.clean_extracted_text(text)
                    metadata["has_visual_context"] = True
                return ProviderExtractionResult(text=text, metadata=metadata)

        fallback_text = self._build_placeholder_extraction(absolute_path, file_type)
        metadata = {"mode": "provider_fallback", "provider_type": provider_type.value, "source_mode": "fallback"}
        if file_type == SourceFileType.PDF:
            normalized_text, pdf_meta = PdfProcessingService.normalize_provider_payload(
                absolute_path,
                payload={},
                fallback_text=fallback_text,
            )
            metadata.update(pdf_meta)
            return ProviderExtractionResult(text=normalized_text, metadata=metadata)
        return ProviderExtractionResult(text=fallback_text, metadata=metadata)

    @staticmethod
    def _build_placeholder_extraction(absolute_path: Path, file_type: SourceFileType) -> str:
        description = f"文件={absolute_path.name} 类型={file_type.value}"
        if file_type == SourceFileType.PDF:
            estimated_page_count = PdfProcessingService.estimate_page_count(absolute_path)
            if estimated_page_count:
                page_sections = [
                    f"## Page {index}\n[placeholder extraction] {description} 第{index}页内容暂不可用"
                    for index in range(1, estimated_page_count + 1)
                ]
                return "\n\n".join(page_sections)
        return f"[placeholder extraction] {description}"
