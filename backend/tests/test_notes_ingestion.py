from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import zipfile

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.ai_provider_config import AIProviderConfig
from app.models.enums import NoteType, ProviderType
from app.models.job import Job
from app.models.note import Note
from app.services.note_generation_service import NoteGenerationService
from app.services.note_naming_service import NoteNamingService
from app.services.safe_file_service import SafeFileService


@pytest.mark.asyncio
async def test_generate_note_and_query_apis(client, workspace_root, auth_headers):
    upload_response = await client.post(
        "/api/v1/sources/upload",
        files={"file": ("lesson.txt", "机器学习基础\n监督学习与无监督学习".encode("utf-8"), "text/plain")},
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    asset_id = upload_response.json()["data"]["id"]

    generate_response = await client.post(
        "/api/v1/notes/generate",
        json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
        headers=auth_headers,
    )
    assert generate_response.status_code == 200
    generate_payload = generate_response.json()["data"]
    assert len(generate_payload["generated_note_ids"]) == 1
    assert generate_payload["written_paths"][0].startswith("notes/generated/")
    assert "/未分类/" in generate_payload["written_paths"][0]
    assert Path(generate_payload["written_paths"][0]).name.startswith("lesson-")

    note_path = Path(workspace_root) / generate_payload["written_paths"][0]
    assert note_path.exists()
    note_content = note_path.read_text(encoding="utf-8")
    assert "subject_slug:" in note_content
    assert "source_type:" in note_content
    assert "retrieval_summary:" not in note_content
    assert "relative_path:" not in note_content
    assert "source_asset_id:" not in note_content
    assert "source_path:" not in note_content
    assert "## 检索上下文摘要" not in note_content
    assert "## 规范化文本摘录" not in note_content
    assert "AI 整理笔记" not in note_content

    list_response = await client.get("/api/v1/notes", headers=auth_headers)
    assert list_response.status_code == 200
    notes = list_response.json()["data"]
    assert len(notes) == 1
    note_id = notes[0]["id"]

    tree_response = await client.get("/api/v1/notes/tree", headers=auth_headers)
    assert tree_response.status_code == 200
    tree = tree_response.json()["data"]
    assert tree[0]["name"] == "notes"

    detail_response = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["relative_path"] == generate_payload["written_paths"][0]
    assert "监督学习" in detail["content"]

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()["data"]
    assert len(jobs) == 1
    assert jobs[0]["job_type"] == "note_generation"
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["started_at"] is not None
    assert jobs[0]["finished_at"] is not None
    assert jobs[0]["logs_json"]
    assert any(log["message"] == "job completed" for log in jobs[0]["logs_json"])
    stages = {log.get("stage") for log in jobs[0]["logs_json"] if log.get("stage")}
    assert {"ingest", "extract", "normalize", "retrieve", "generate", "write"}.issubset(stages)
    assert jobs[0]["result_json"]["processed_assets"][0]["retrieval_summary"]["matched_count"] == 0




@pytest.mark.asyncio
async def test_delete_note_removes_db_row_file_and_linked_artifact(client, workspace_root, auth_headers, session_factory):
    from app.models.generated_artifact import GeneratedArtifact
    from app.services.review_service import ReviewService

    note_relative_path = "notes/delete-me.md"
    note_path = Path(workspace_root) / note_relative_path
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# delete me", encoding="utf-8")

    artifact_relative_path = "artifacts/summary/delete-linked.md"
    artifact_path = Path(workspace_root) / artifact_relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("# linked artifact", encoding="utf-8")

    async with session_factory() as session:
        note = Note(
            title="Delete Me",
            relative_path=note_relative_path,
            note_type="source_note",
            content_hash=ReviewService.hash_content("# delete me"),
            source_asset_id=None,
            frontmatter_json={},
        )
        session.add(note)
        await session.flush()

        artifact_note = Note(
            title="Linked Summary",
            relative_path=artifact_relative_path,
            note_type="summary",
            content_hash=ReviewService.hash_content("# linked artifact"),
            source_asset_id=None,
            frontmatter_json={"artifact_type": "summary"},
        )
        session.add(artifact_note)
        await session.flush()

        artifact = GeneratedArtifact(
            artifact_type="summary",
            scope_type="manual",
            note_ids_json=[note.id],
            prompt_extra=None,
            output_note_id=artifact_note.id,
            status="completed",
        )
        session.add(artifact)
        await session.commit()
        await session.refresh(note)
        await session.refresh(artifact)

        note_id = note.id
        artifact_note_id = artifact_note.id
        artifact_id = artifact.id

    delete_response = await client.delete(f"/api/v1/notes/{artifact_note_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    delete_data = delete_response.json()["data"]
    assert delete_data["deleted_note_id"] == artifact_note_id
    assert delete_data["deleted_artifact_id"] == artifact_id
    assert delete_data["deleted_relative_paths"] == [artifact_relative_path]
    assert not artifact_path.exists()
    assert note_path.exists()

    deleted_note_detail = await client.get(f"/api/v1/notes/{artifact_note_id}", headers=auth_headers)
    assert deleted_note_detail.status_code == 404

    remaining_note_response = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert remaining_note_response.status_code == 200


async def test_notes_list_and_tree_hide_artifacts_by_default_but_allow_explicit_include(
    client,
    auth_headers,
    session_factory,
):
    async with session_factory() as session:
        session.add_all(
            [
                Note(
                    title="Main Note",
                    relative_path="notes/generated/main-note.md",
                    note_type=NoteType.SOURCE_NOTE.value,
                    content_hash="hash-main",
                    source_asset_id=None,
                    frontmatter_json={},
                ),
                Note(
                    title="Summary Artifact",
                    relative_path="artifacts/summary/summary-note.md",
                    note_type=NoteType.SUMMARY.value,
                    content_hash="hash-summary",
                    source_asset_id=None,
                    frontmatter_json={"artifact_type": "summary"},
                ),
                Note(
                    title="Mindmap Artifact",
                    relative_path="artifacts/mindmap/mindmap-note.md",
                    note_type=NoteType.MINDMAP.value,
                    content_hash="hash-mindmap",
                    source_asset_id=None,
                    frontmatter_json={"artifact_type": "mindmap"},
                ),
            ]
        )
        await session.commit()

    list_response = await client.get("/api/v1/notes", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert [item["title"] for item in list_data] == ["Main Note"]

    tree_response = await client.get("/api/v1/notes/tree", headers=auth_headers)
    assert tree_response.status_code == 200
    tree_data = tree_response.json()["data"]
    assert tree_data[0]["name"] == "notes"
    assert all(node["name"] != "artifacts" for node in tree_data)

    include_list_response = await client.get("/api/v1/notes?include_artifacts=true", headers=auth_headers)
    assert include_list_response.status_code == 200
    include_titles = {item["title"] for item in include_list_response.json()["data"]}
    assert include_titles == {"Main Note", "Summary Artifact", "Mindmap Artifact"}

    include_tree_response = await client.get("/api/v1/notes/tree?include_artifacts=true", headers=auth_headers)
    assert include_tree_response.status_code == 200
    include_tree_data = include_tree_response.json()["data"]
    assert {node["name"] for node in include_tree_data} == {"artifacts", "notes"}


@pytest.mark.asyncio
async def test_generate_note_queue_metadata_when_not_eager(client, auth_headers):
    from app.core.config import get_settings

    settings = get_settings()
    original_eager = settings.celery_task_always_eager
    settings.celery_task_always_eager = False

    try:
        with patch("app.api.v1.endpoints.notes.generate_notes_task.delay") as delay_mock:
            delay_mock.return_value.id = "celery-note-001"
            response = await client.post(
                "/api/v1/notes/generate",
                json={"source_asset_ids": [999], "note_directory": "notes/generated"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["status"] == "queued"
        assert payload["celery_task_id"] == "celery-note-001"
        assert payload["generated_note_ids"] == []

        jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
        jobs = jobs_response.json()["data"]
        queued_job = next(job for job in jobs if job["id"] == payload["job"])
        assert queued_job["status"] == "pending"
        assert queued_job["celery_task_id"] == "celery-note-001"
        assert any(log["message"] == "note generation queued" for log in queued_job["logs_json"])
    finally:
        settings.celery_task_always_eager = original_eager


@pytest.mark.asyncio
async def test_generate_note_image_low_quality_extraction_fails_quality_gate(client, auth_headers, session_factory):
    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.OCR.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-test",
                model_name="demo-ocr",
                extra_json={},
                is_enabled=True,
            )
        )
        await session.commit()

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload
            self.is_success = True

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.startswith("https://example.com") and url.endswith("/chat/completions"):
            messages = kwargs.get("json", {}).get("messages", [])
            if messages and isinstance(messages[0].get("content"), list):
                return MockResponse({"choices": [{"message": {"content": [{"type": "text", "text": "x"}]}}]})
            return MockResponse({"choices": [{"message": {"content": '{"title":"不应生成","subject":"未分类","markdown_body":"body"}'}}]})
        return await original_post(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.post", new=fake_post):
        upload_response = await client.post(
            "/api/v1/sources/upload",
            files={"file": ("board.png", b"fake-image", "image/png")},
            data={"upload_dir": "uploads/sources"},
            headers=auth_headers,
        )
        assert upload_response.status_code == 200
        asset_id = upload_response.json()["data"]["id"]

        with pytest.raises(ValueError, match="图片提取结果不可用于生成笔记"):
            await client.post(
                "/api/v1/notes/generate",
                json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
                headers=auth_headers,
            )

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        assert job.status == "failed"
        assert any(log["message"] == "image extraction quality gate failed" for log in (job.logs_json or []))


@pytest.mark.asyncio
async def test_generate_note_audio_low_quality_extraction_fails_quality_gate(client, auth_headers, session_factory):
    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.STT.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-test",
                model_name="demo-stt",
                extra_json={},
                is_enabled=True,
            )
        )
        await session.commit()

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload
            self.is_success = True

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.endswith("/audio/transcriptions"):
            return MockResponse({"text": "呃"})
        if isinstance(url, str) and url.endswith("/chat/completions"):
            return MockResponse({"choices": [{"message": {"content": '{"title":"不应生成","subject":"未分类","markdown_body":"body"}'}}]})
        return await original_post(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.post", new=fake_post):
        upload_response = await client.post(
            "/api/v1/sources/upload",
            files={"file": ("noise.wav", b"RIFFdemo-wave", "audio/wav")},
            data={"upload_dir": "uploads/sources"},
            headers=auth_headers,
        )
        assert upload_response.status_code == 200
        asset_id = upload_response.json()["data"]["id"]

        with pytest.raises(ValueError, match="音频提取结果不可用于生成笔记"):
            await client.post(
                "/api/v1/notes/generate",
                json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
                headers=auth_headers,
            )

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        assert job.status == "failed"
        assert any(log["message"] == "audio extraction quality gate failed" for log in (job.logs_json or []))


@pytest.mark.asyncio
async def test_generate_note_audio_quality_warning_is_carried_into_result(client, auth_headers, session_factory):
    from app.models.ai_provider_config import AIProviderConfig
    from app.models.enums import ProviderType

    async with session_factory() as session:
        session.add_all(
            [
                AIProviderConfig(
                    provider_type=ProviderType.LLM.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-test",
                    model_name="demo-model",
                    extra_json={},
                    is_enabled=True,
                ),
                AIProviderConfig(
                    provider_type=ProviderType.STT.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-test",
                    model_name="demo-stt",
                    extra_json={},
                    is_enabled=True,
                ),
                AIProviderConfig(
                    provider_type=ProviderType.EMBEDDING.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-embed",
                    model_name="demo-embed",
                    extra_json={},
                    is_enabled=True,
                ),
            ]
        )
        await session.commit()

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload
            self.is_success = True

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.endswith("/audio/transcriptions"):
            return MockResponse({"text": "牛顿第二定律"})
        if isinstance(url, str) and url.endswith("/embeddings"):
            inputs = kwargs.get("json", {}).get("input", [])
            data = [{"index": idx, "embedding": [1.0, 0.0]} for idx, _ in enumerate(inputs)]
            return MockResponse({"model": "demo-embed", "data": data, "usage": {"prompt_tokens": 1, "total_tokens": 1}})
        if isinstance(url, str) and url.endswith("/chat/completions"):
            messages = kwargs.get("json", {}).get("messages", [])
            if messages and isinstance(messages[0].get("content"), list):
                return MockResponse({"choices": [{"message": {"content": [{"type": "text", "text": "图片OCR内容"}]}}]})
            return MockResponse({
                "choices": [{"message": {"content": '{"title":"牛顿第二定律","subject":"物理","markdown_body":"## 摘要\\n\\n- 介绍牛顿第二定律。","warnings":["模型提示：存在轻微转写误差"],"confidence":0.8}'}}]
            })
        return await original_post(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.post", new=fake_post):
        upload_response = await client.post(
            "/api/v1/sources/upload",
            files={"file": ("short.wav", b"RIFFdemo-wave", "audio/wav")},
            data={"upload_dir": "uploads/sources"},
            headers=auth_headers,
        )
        assert upload_response.status_code == 200
        asset_id = upload_response.json()["data"]["id"]

        generate_response = await client.post(
            "/api/v1/notes/generate",
            json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
            headers=auth_headers,
        )
        assert generate_response.status_code == 200

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        processed = job.result_json["processed_assets"][0]
        quality = processed["extraction_metadata"]["quality_assessment"]
        assert quality["status"] == "warning"
        assert quality["business_status"] == "degraded"
        assert any("音频转写内容较短" in item for item in processed["generation_result"]["warnings"])
        assert any(log["message"] == "audio extraction quality degraded" for log in (job.logs_json or []))






def test_safe_file_service_extracts_docx_paragraphs_tables_and_linebreaks(tmp_path):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>""",
        )
        archive.writestr(
            "word/document.xml",
            """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">
  <w:body>
    <w:p>
      <w:r><w:t>复杂DOCX标题</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>第一行</w:t></w:r>
      <w:r><w:br/></w:r>
      <w:r><w:t>第二行</w:t></w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>单元格A1</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>单元格B1</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>单元格A2</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>单元格B2</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>""",
        )

    path = tmp_path / "complex.docx"
    path.write_bytes(buffer.getvalue())

    text, metadata = SafeFileService.extract_docx_text_and_metadata(path)

    assert "复杂DOCX标题" in text
    assert "第一行\n第二行" in text
    assert "单元格A1 | 单元格B1" in text
    assert "单元格A2 | 单元格B2" in text
    assert metadata["extractor"] == "docx_xml"
    assert metadata["table_count"] == 1
    assert metadata["table_cell_count"] == 4
    assert metadata["line_break_count"] == 1
    assert metadata["fallback_used"] is False


@pytest.mark.asyncio
async def test_generate_note_docx_fallback_extraction_fails_with_diagnostic_logs(client, auth_headers, session_factory):
    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.LLM.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-test",
                model_name="demo-model",
                extra_json={},
                is_enabled=True,
            )
        )
        await session.commit()

    broken_docx_bytes = b"x"

    upload_response = await client.post(
        "/api/v1/sources/upload",
        files={
            "file": (
                "broken.docx",
                broken_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert upload_response.status_code == 200
    asset_id = upload_response.json()["data"]["id"]

    with pytest.raises(ValueError, match="DOCX 提取结果不可用于生成笔记"):
        await client.post(
            "/api/v1/notes/generate",
            json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
            headers=auth_headers,
        )

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        assert job.status == "failed"
        assert "DOCX 提取结果不可用于生成笔记" in (job.error_message or "")
        logs = job.logs_json or []
        extract_log = next(log for log in logs if log["message"] == "source text extracted")
        assert extract_log["docx_extractor"] == "docx_bad_zip_fallback"
        assert extract_log["docx_fallback_used"] is True
        assert extract_log["docx_fallback_reason"] == "bad_zip_or_os_error"
        quality_log = next(log for log in logs if log["message"] == "text extraction quality gate failed")
        assert quality_log["quality_reason"] == "docx_fallback_extraction_not_meaningful"
        assert quality_log["docx_extractor"] == "docx_bad_zip_fallback"
    from app.schemas.integrations import GeneratedNoteResult, NoteRetrievalResult, ProviderExtractionResult

    source_asset = type(
        "SourceAssetStub",
        (),
        {"id": 123, "file_path": "uploads/sources/lesson.txt", "file_type": "text"},
    )()
    normalized = ProviderExtractionResult(
        text="这是规范化后的原文摘录，不应出现在最终主笔记中。",
        metadata={"normalization_mode": "plain_text_cleanup"},
    )
    retrieval = NoteRetrievalResult(
        query_text="牛顿第二定律",
        matched_note_ids=[1],
        matched_paths=["notes/physics/prior-note.md"],
        snippets=["先前笔记片段"],
        similarity_scores=[0.92],
        retrieval_context="这是检索命中的上下文摘要，不应进入最终主笔记。",
        provider_model="demo-embed",
    )
    generated_note = GeneratedNoteResult(
        title="牛顿第二定律",
        subject="物理",
        markdown_body="## 摘要\n\n- 力等于质量乘以加速度。",
        warnings=["请结合课本例题复习单位换算。"],
        confidence=0.88,
        summary="介绍牛顿第二定律的核心内容。",
        raw_text="raw",
    )

    markdown = NoteGenerationService._build_markdown(
        source_asset=source_asset,
        normalized=normalized,
        retrieval=retrieval,
        generated_note=generated_note,
        subject_slug="physics",
        relative_path="notes/generated/physics/newton-second-law.md",
    )

    assert "title: 牛顿第二定律" in markdown
    assert "subject: 物理" in markdown
    assert "subject_slug: physics" in markdown
    assert "source_type: text" in markdown
    assert "## 摘要" in markdown
    assert "力等于质量乘以加速度" in markdown
    assert "## 使用提醒" in markdown
    assert "请结合课本例题复习单位换算" in markdown

    assert "AI 整理笔记" not in markdown
    assert "retrieval_summary:" not in markdown
    assert "relative_path:" not in markdown
    assert "source_asset_id:" not in markdown
    assert "source_path:" not in markdown
    assert "extracted_text_preview" not in markdown
    assert "extraction_metadata" not in markdown
    assert "## 检索上下文摘要" not in markdown
    assert "## 规范化文本摘录" not in markdown
    assert "这是检索命中的上下文摘要，不应进入最终主笔记。" not in markdown
    assert "这是规范化后的原文摘录，不应出现在最终主笔记中。" not in markdown


def test_assess_extraction_quality_distinguishes_business_statuses():
    from app.models.enums import SourceFileType

    failed = NoteGenerationService._assess_extraction_quality(
        source_type=SourceFileType.IMAGE,
        normalized=type("Normalized", (), {"text": "x", "metadata": {}})(),
    )
    assert failed.business_status == "failed"
    assert failed.should_fail is True

    degraded = NoteGenerationService._assess_extraction_quality(
        source_type=SourceFileType.AUDIO,
        normalized=type("Normalized", (), {"text": "牛顿第二定律", "metadata": {}})(),
    )
    assert degraded.business_status == "degraded"
    assert degraded.should_fail is False


@pytest.mark.asyncio
async def test_generate_note_pdf_placeholder_extraction_fails_quality_gate(client, workspace_root, auth_headers, session_factory):
    async with session_factory() as session:
        session.add(
            AIProviderConfig(
                provider_type=ProviderType.OCR.value,
                base_url="https://example.com/v1",
                api_key_encrypted="sk-test",
                model_name="demo-ocr",
                extra_json={},
                is_enabled=True,
            )
        )
        await session.commit()

    class MockResponse:
        def __init__(self, payload, *, is_success=True):
            self._payload = payload
            self.is_success = is_success

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.startswith("https://example.com") and url.endswith("/chat/completions"):
            messages = kwargs.get("json", {}).get("messages", [])
            if messages and isinstance(messages[0].get("content"), list):
                return MockResponse({}, is_success=False)
            return MockResponse({"choices": [{"message": {"content": "should not reach llm"}}]})
        return await original_post(self, url, *args, **kwargs)

    pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type /Catalog>>endobj\n2 0 obj<</Type /Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type /Page/Parent 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"

    with patch("httpx.AsyncClient.post", new=fake_post):
        upload_response = await client.post(
            "/api/v1/sources/upload",
            files={"file": ("scan.pdf", pdf_bytes, "application/pdf")},
            data={"upload_dir": "uploads/sources"},
            headers=auth_headers,
        )
        assert upload_response.status_code == 200
        asset_id = upload_response.json()["data"]["id"]

        with pytest.raises(ValueError, match="占位/回退文本"):
            await client.post(
                "/api/v1/notes/generate",
                json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
                headers=auth_headers,
            )

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        assert job.status == "failed"
        assert "占位/回退文本" in (job.error_message or "")
        assert any(log["message"] == "pdf extraction quality gate failed" for log in (job.logs_json or []))
        assert not (Path(workspace_root) / "notes/generated/scan.md").exists()


@pytest.mark.asyncio
async def test_generate_note_pipeline_logs_and_multimedia_path(client, auth_headers, session_factory):
    from app.models.ai_provider_config import AIProviderConfig
    from app.models.enums import ProviderType

    async with session_factory() as session:
        session.add_all(
            [
                AIProviderConfig(
                    provider_type=ProviderType.LLM.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-test",
                    model_name="demo-model",
                    extra_json={},
                    is_enabled=True,
                ),
                AIProviderConfig(
                    provider_type=ProviderType.STT.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-test",
                    model_name="demo-stt",
                    extra_json={},
                    is_enabled=True,
                ),
                AIProviderConfig(
                    provider_type=ProviderType.EMBEDDING.value,
                    base_url="https://example.com/v1",
                    api_key_encrypted="sk-embed",
                    model_name="demo-embed",
                    extra_json={},
                    is_enabled=True,
                ),
            ]
        )
        await session.commit()

    class MockResponse:
        def __init__(self, payload):
            self._payload = payload
            self.is_success = True

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.endswith("/audio/transcriptions"):
            return MockResponse({"text": "音频转写内容\n牛顿第二定律与功"})
        if isinstance(url, str) and url.endswith("/embeddings"):
            inputs = kwargs.get("json", {}).get("input", [])
            data = []
            for index, text in enumerate(inputs):
                if index == 0:
                    vector = [1.0, 0.0]
                elif "牛顿" in text:
                    vector = [0.9, 0.1]
                else:
                    vector = [0.1, 0.9]
                data.append({"index": index, "embedding": vector})
            return MockResponse({"model": "demo-embed", "data": data, "usage": {"prompt_tokens": 10, "total_tokens": 10}})
        if isinstance(url, str) and url.endswith("/chat/completions"):
            messages = kwargs.get("json", {}).get("messages", [])
            if messages and isinstance(messages[0].get("content"), list):
                return MockResponse({"choices": [{"message": {"content": [{"type": "text", "text": "图片OCR内容"}]}}]})
            prompt_text = "\n".join(str(message.get("content", "")) for message in messages)
            assert "current_datetime_utc" in prompt_text
            assert "source_metadata" in prompt_text
            assert "normalized_text" in prompt_text
            assert "retrieved_context" in prompt_text
            return MockResponse({
                "choices": [{"message": {"content": '{"title":"牛顿第二定律学习笔记","subject":"物理","markdown_body":"## 摘要\\n\\n- 讲解牛顿第二定律与功。","warnings":["音频转写可能存在局部误差"],"confidence":0.82}'}}]
            })
        return await original_post(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.post", new=fake_post):
        upload_response = await client.post(
            "/api/v1/sources/upload",
            files={"file": ("lecture.wav", b"RIFFdemo-wave", "audio/wav")},
            data={"upload_dir": "uploads/sources"},
            headers=auth_headers,
        )
        assert upload_response.status_code == 200
        asset_id = upload_response.json()["data"]["id"]

        generate_response = await client.post(
            "/api/v1/notes/generate",
            json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
            headers=auth_headers,
        )
        assert generate_response.status_code == 200
        payload = generate_response.json()["data"]
        assert len(payload["generated_note_ids"]) == 1

    async with session_factory() as session:
        job = (await session.execute(select(Job).order_by(Job.id.desc()))).scalars().first()
        assert job is not None
        stages = [log.get("stage") for log in (job.logs_json or []) if log.get("stage")]
        assert "ingest" in stages
        assert "extract" in stages
        assert "normalize" in stages
        assert "retrieve" in stages
        assert "generate" in stages
        assert "write" in stages
        assert any(log["message"] == "source text extracted" for log in job.logs_json)
        assert any(log["message"] == "extracted text normalized" for log in job.logs_json)
        assert any(log["message"] == "retrieval completed" for log in job.logs_json)
        assert any(log["message"] == "llm note generation completed" for log in job.logs_json)
        assert job.result_json["processed_assets"][0]["source_type"] == "audio"
        assert job.result_json["processed_assets"][0]["extraction_metadata"]["source_type"] == "audio"
        assert "retrieval_summary" in job.result_json["processed_assets"][0]
        assert job.result_json["processed_assets"][0]["generation_result"]["title"].startswith("牛顿第二定律学习笔记-")
        assert job.result_json["processed_assets"][0]["generation_result"]["subject"] == "物理"
        assert "/物理/" in job.result_json["processed_assets"][0]["relative_path"]


def test_note_naming_service_normalizes_subject_and_sanitizes_title():
    subject, subject_slug = NoteNamingService.normalize_subject("CS")
    assert subject == "计算机"
    assert subject_slug == "computer-science"

    sanitized = NoteNamingService.sanitize_title_base('  导数/极限:*?<>  ')
    assert sanitized == "导数-极限"


@pytest.mark.asyncio
async def test_note_naming_service_deduplicates_same_minute_paths(session_factory, workspace_root):
    from datetime import datetime, timezone

    fixed_dt = datetime(2026, 4, 20, 11, 22, tzinfo=timezone.utc)
    fixed_time = NoteNamingService._format_timestamp(fixed_dt)
    target_dir = workspace_root / "notes" / "subjects" / "数学"
    target_dir.mkdir(parents=True, exist_ok=True)
    existing = target_dir / f"函数-{fixed_time}.md"
    existing.write_text("existing", encoding="utf-8")

    async with session_factory() as session:
        resolved = await NoteNamingService.resolve_note_naming(
            session,
            raw_subject="高中数学",
            raw_title="函数",
            generated_at=fixed_dt,
            note_directory="notes/subjects",
        )

    assert resolved.subject == "数学"
    assert resolved.relative_path == f"notes/subjects/数学/函数-{fixed_time}-2.md"


def test_parse_generation_result_validates_required_fields_and_json():
    parsed = NoteGenerationService._parse_generation_result(
        '{"title":"集合论笔记","subject":"数学","markdown_body":"## 核心概念\\n\\n- 集合与元素","warnings":["存在少量噪声"],"confidence":0.9}'
    )
    assert parsed.title == "集合论笔记"
    assert parsed.subject == "数学"
    assert parsed.markdown_body.startswith("## 核心概念")
    assert parsed.warnings == ["存在少量噪声"]
    assert parsed.confidence == 0.9

    with pytest.raises(ValueError, match="not valid JSON"):
        NoteGenerationService._parse_generation_result("not json")

    with pytest.raises(ValueError, match="missing required fields"):
        NoteGenerationService._parse_generation_result('{"title":"","subject":"数学","markdown_body":"body"}')

    with pytest.raises(ValueError, match="between 0 and 1"):
        NoteGenerationService._parse_generation_result('{"title":"标题","subject":"数学","markdown_body":"body","confidence":1.2}')
