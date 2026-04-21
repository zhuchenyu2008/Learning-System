from __future__ import annotations

from pathlib import Path

import pytest

from app.integrations.openai_compatible import OpenAICompatibleProviderAdapter
from app.models.ai_provider_config import AIProviderConfig
from app.models.enums import NoteType, ProviderType
from app.models.note import Note
from app.services.note_retrieval_service import NoteRetrievalService


@pytest.mark.asyncio
async def test_openai_compatible_adapter_embed_calls_embeddings_endpoint(session_factory, monkeypatch):
    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.EMBEDDING.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-embed",
                model_name="embed-model",
                extra_json={"encoding_format": "float"},
                is_enabled=True,
            )
        )
        await session.commit()

        captured: dict = {}

        class MockResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "model": "embed-model",
                    "data": [
                        {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                        {"index": 1, "embedding": [0.4, 0.5, 0.6]},
                    ],
                    "usage": {"prompt_tokens": 12, "total_tokens": 12},
                }

        async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
            captured["url"] = url
            captured["json"] = kwargs.get("json")
            captured["headers"] = kwargs.get("headers")
            return MockResponse()

        monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

        adapter = OpenAICompatibleProviderAdapter(session)
        result = await adapter.embed(["alpha", "beta"])

        assert captured["url"] == "https://example.com/v1/embeddings"
        assert captured["json"] == {
            "model": "embed-model",
            "input": ["alpha", "beta"],
            "encoding_format": "float",
        }
        assert captured["headers"]["Authorization"] == "Bearer sk-embed"
        assert result.model_name == "embed-model"
        assert result.vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        assert result.usage == {"prompt_tokens": 12, "total_tokens": 12}


@pytest.mark.asyncio
async def test_note_retrieval_service_returns_ranked_matches(session_factory, workspace_root, monkeypatch):
    notes_dir = workspace_root / "notes" / "generated"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "linear-algebra.md").write_text(
        "# 线性代数\n\n向量空间与基底。\n\n矩阵分解帮助理解线性变换。",
        encoding="utf-8",
    )
    (notes_dir / "probability.md").write_text(
        "# 概率论\n\n条件概率与贝叶斯公式。\n\n随机变量刻画不确定性。",
        encoding="utf-8",
    )

    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.EMBEDDING.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-embed",
                model_name="embed-v1",
                extra_json={},
                is_enabled=True,
            )
        )
        session.add_all(
            [
                Note(
                    title="linear-algebra",
                    relative_path="notes/generated/linear-algebra.md",
                    note_type=NoteType.SOURCE_NOTE.value,
                    content_hash="hash-linear",
                    frontmatter_json={},
                ),
                Note(
                    title="probability",
                    relative_path="notes/generated/probability.md",
                    note_type=NoteType.SOURCE_NOTE.value,
                    content_hash="hash-probability",
                    frontmatter_json={},
                ),
            ]
        )
        await session.commit()

        async def fake_embed(self, texts):  # noqa: ANN001
            assert isinstance(texts, list)
            assert len(texts) >= 3
            vectors = [[1.0, 0.0]]
            for text in texts[1:]:
                if "线性代数" in text or "矩阵分解" in text:
                    vectors.append([0.95, 0.05])
                else:
                    vectors.append([0.05, 0.95])
            return type("EmbedResult", (), {
                "vectors": vectors,
                "model_name": "embed-v1",
            })()

        monkeypatch.setattr(OpenAICompatibleProviderAdapter, "embed", fake_embed)

        result = await NoteRetrievalService.retrieve_related_notes(
            session,
            normalized_text="矩阵与线性变换的核心概念",
            source_metadata={"source_type": "text", "source_path": "uploads/source.txt"},
            top_k=2,
        )

        assert result.query_text.startswith("矩阵与线性变换的核心概念")
        assert set(result.matched_paths) == {
            "notes/generated/linear-algebra.md",
            "notes/generated/probability.md",
        }
        assert set(result.matched_note_ids) == {1, 2}
        assert len(result.snippets) == 2
        score_by_path = dict(zip(result.matched_paths, result.similarity_scores, strict=False))
        snippet_by_path = dict(zip(result.matched_paths, result.snippets, strict=False))
        assert snippet_by_path["notes/generated/linear-algebra.md"].startswith("# 线性代数")
        assert score_by_path["notes/generated/linear-algebra.md"] > score_by_path["notes/generated/probability.md"]
        assert result.provider_model == "embed-v1"
        assert "相关旧笔记摘录" in result.retrieval_context
        assert "notes/generated/linear-algebra.md" in result.retrieval_context


def test_note_retrieval_service_chunking_and_context_limits():
    text = "\n\n".join([f"段落 {index} - " + ("内容" * 80) for index in range(1, 6)])
    chunks = NoteRetrievalService._chunk_text(text)
    assert chunks
    assert all(len(chunk) <= NoteRetrievalService.CHUNK_SIZE for chunk in chunks)

    context = NoteRetrievalService._build_retrieval_context([
        type("Match", (), {
            "note_id": 1,
            "relative_path": "notes/generated/a.md",
            "score": 0.9,
            "snippet": "A" * 2000,
        })(),
        type("Match", (), {
            "note_id": 2,
            "relative_path": "notes/generated/b.md",
            "score": 0.8,
            "snippet": "B" * 2000,
        })(),
    ])
    assert context.startswith("以下是相关旧笔记摘录")
    assert len(context) <= NoteRetrievalService.MAX_CONTEXT_CHARS + 128
