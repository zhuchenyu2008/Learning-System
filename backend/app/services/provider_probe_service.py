from __future__ import annotations

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
            else:
                response = await client.get(base, headers=headers)

        if response.is_success:
            return {"status": "ok", "message": f"{provider_type.value} provider reachable"}
        return {
            "status": "error",
            "message": f"{provider_type.value} provider returned HTTP {response.status_code}",
        }
