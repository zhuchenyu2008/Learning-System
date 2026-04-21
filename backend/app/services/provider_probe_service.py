from __future__ import annotations

import base64
import io
import struct
import wave
import zlib

import httpx

from app.models.enums import ProviderType


class ProviderProbeService:

    @staticmethod
    async def test_provider(*, provider_type: ProviderType, base_url: str, api_key: str | None, model_name: str) -> dict:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        base = base_url.rstrip("/")
        timeout = httpx.Timeout(20.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider_type in {ProviderType.LLM, ProviderType.EMBEDDING}:
                payload = {"model": model_name}
                endpoint = "/embeddings" if provider_type == ProviderType.EMBEDDING else "/chat/completions"
                if provider_type == ProviderType.EMBEDDING:
                    payload["input"] = "ping"
                else:
                    payload["messages"] = [{"role": "user", "content": "ping"}]
                    payload["max_tokens"] = 1
                response = await client.post(f"{base}{endpoint}", json=payload, headers=headers)
            elif provider_type == ProviderType.STT:
                probe_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
                files = {
                    "file": ("probe.wav", ProviderProbeService._build_probe_wav_bytes(), "audio/wav"),
                }
                data = {"model": model_name}
                response = await client.post(f"{base}/audio/transcriptions", data=data, files=files, headers=probe_headers)
            else:
                image_url = f"data:image/png;base64,{ProviderProbeService._build_probe_png_base64()}"
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Please read any visible text in this image."},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                    "max_tokens": 16,
                }
                response = await client.post(f"{base}/chat/completions", json=payload, headers=headers)

        if response.is_success:
            return {"status": "ok", "message": f"{provider_type.value} provider reachable"}
        return {
            "status": "error",
            "message": f"{provider_type.value} provider returned HTTP {response.status_code}",
        }

    @staticmethod
    def _build_probe_wav_bytes() -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * 1600)
        return buffer.getvalue()

    @staticmethod
    def _build_probe_png_base64() -> str:
        def chunk(chunk_type: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + chunk_type
                + data
                + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
            )

        width = 32
        height = 32
        signature = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        row = b"\x00" + (b"\xff\xff\xff" * width)
        raw = row * height
        idat = chunk(b"IDAT", zlib.compress(raw))
        iend = chunk(b"IEND", b"")
        return base64.b64encode(signature + ihdr + idat + iend).decode("ascii")
