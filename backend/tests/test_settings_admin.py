import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.admin_entities import UserActivitySnapshot
from app.models.ai_provider_config import AIProviderConfig
from app.models.enums import NoteType, ProviderType, UserRole
from app.models.note import Note
from app.models.review_card import ReviewCard
from app.models.review_log import ReviewLog
from app.models.knowledge_point import KnowledgePoint
from app.models.user import User


@pytest.fixture
async def viewer_client(tmp_path: Path):
    settings = get_settings()
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'viewer_test.db'}"
    settings.database_url = db_url
    settings.workspace_root = str(tmp_path / "workspace")

    engine = create_async_engine(db_url, future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        session.add_all(
            [
                User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=get_password_hash("ChangeMe123!"),
                    role=UserRole.ADMIN,
                    is_active=True,
                ),
                User(
                    username="viewer",
                    email="viewer@example.com",
                    password_hash=get_password_hash("ChangeMe123!"),
                    role=UserRole.VIEWER,
                    is_active=True,
                ),
            ]
        )
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client

    await engine.dispose()


@pytest.mark.asyncio
async def test_existing_snapshot_is_backfilled_from_review_logs(client, session_factory):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with session_factory() as session:
        admin = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()
        note = Note(
            title="legacy note",
            relative_path="notes/legacy.md",
            note_type=NoteType.SUMMARY,
            content_hash="legacy-hash",
            frontmatter_json={},
        )
        session.add(note)
        await session.flush()

        point = KnowledgePoint(
            note_id=note.id,
            title="legacy point",
            content_md="legacy content",
            embedding_vector=None,
            tags_json={},
            summary_text="legacy summary",
            source_anchor="legacy-point",
        )
        session.add(point)
        await session.flush()

        card = ReviewCard(
            knowledge_point_id=point.id,
            state_json={},
            due_at=datetime.now(timezone.utc),
            last_reviewed_at=None,
            suspended=False,
        )
        session.add(card)
        await session.flush()

        review_log = ReviewLog(
            user_id=admin.id,
            review_card_id=card.id,
            rating=3,
            duration_seconds=42,
            note="legacy review",
        )
        session.add(review_log)
        await session.flush()

        existing_snapshot = (
            await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == admin.id))
        ).scalar_one()
        existing_snapshot.total_watch_seconds = 0
        existing_snapshot.review_count = 0
        existing_snapshot.page_view_count = 0
        existing_snapshot.note_view_count = 0
        existing_snapshot.review_watch_seconds = 0
        existing_snapshot.last_activity_at = admin.last_login_at
        existing_snapshot.last_event_type = "login"
        await session.commit()

    activity = await client.get("/api/v1/admin/user-activity", headers=headers)
    assert activity.status_code == 200
    first = activity.json()["data"][0]
    assert first["review_count"] == 1
    assert first["review_watch_seconds"] == 42
    assert first["total_watch_seconds"] == 42
    assert first["last_event_type"] in {"login", "review_log"}


@pytest.mark.asyncio
async def test_user_activity_is_sorted_by_recent_non_zero_activity(client, session_factory):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with session_factory() as session:
        users = []
        for index in range(1, 8):
            user = User(
                username=f"viewer-{index}",
                email=f"viewer-{index}@example.com",
                password_hash=get_password_hash("ChangeMe123!"),
                role=UserRole.VIEWER,
                is_active=True,
                last_login_at=datetime(2026, 4, 18, 8, index, tzinfo=timezone.utc),
            )
            session.add(user)
            users.append(user)
        await session.flush()

        active_user = users[0]
        for user in users[1:]:
            snapshot = UserActivitySnapshot(
                user_id=user.id,
                total_watch_seconds=0,
                review_count=0,
                page_view_count=0,
                note_view_count=0,
                review_watch_seconds=0,
                last_activity_at=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc),
                last_event_type="login",
            )
            session.add(snapshot)

        active_snapshot = UserActivitySnapshot(
            user_id=active_user.id,
            total_watch_seconds=27,
            review_count=1,
            page_view_count=1,
            note_view_count=1,
            review_watch_seconds=12,
            last_activity_at=datetime(2026, 4, 19, 1, 0, tzinfo=timezone.utc),
            last_event_type="note_watch",
        )
        session.add(active_snapshot)
        await session.commit()

    activity = await client.get("/api/v1/admin/user-activity", headers=headers)
    assert activity.status_code == 200
    data = activity.json()["data"]
    active_index = next(index for index, item in enumerate(data) if item["username"] == "viewer-1")
    zero_viewer_indexes = [index for index, item in enumerate(data) if item["username"] in {f"viewer-{n}" for n in range(2, 8)}]
    assert active_index < min(zero_viewer_indexes)
    assert active_index < 6
    assert data[active_index]["total_watch_seconds"] == 27
    assert data[active_index]["last_event_type"] == "note_watch"


@pytest.mark.asyncio
async def test_user_activity_prefers_non_zero_rows_over_recent_login_only_rows(client, session_factory):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with session_factory() as session:
        active_user = User(
            username="active-viewer",
            email="active-viewer@example.com",
            password_hash=get_password_hash("ChangeMe123!"),
            role=UserRole.VIEWER,
            is_active=True,
            last_login_at=datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc),
        )
        session.add(active_user)
        await session.flush()
        session.add(
            UserActivitySnapshot(
                user_id=active_user.id,
                total_watch_seconds=14,
                review_count=1,
                page_view_count=1,
                note_view_count=1,
                review_watch_seconds=8,
                last_activity_at=datetime(2026, 4, 18, 8, 5, tzinfo=timezone.utc),
                last_event_type="note_watch",
            )
        )

        for index in range(1, 8):
            user = User(
                username=f"recent-zero-{index}",
                email=f"recent-zero-{index}@example.com",
                password_hash=get_password_hash("ChangeMe123!"),
                role=UserRole.VIEWER,
                is_active=True,
                last_login_at=datetime(2026, 4, 19, 9, index, tzinfo=timezone.utc),
            )
            session.add(user)
            await session.flush()
            session.add(
                UserActivitySnapshot(
                    user_id=user.id,
                    total_watch_seconds=0,
                    review_count=0,
                    page_view_count=0,
                    note_view_count=0,
                    review_watch_seconds=0,
                    last_activity_at=user.last_login_at,
                    last_event_type="login",
                )
            )

        await session.commit()

    activity = await client.get("/api/v1/admin/user-activity", headers=headers)
    assert activity.status_code == 200
    data = activity.json()["data"]
    active_index = next(index for index, item in enumerate(data) if item["username"] == "active-viewer")
    recent_zero_indexes = [index for index, item in enumerate(data) if str(item["username"]).startswith("recent-zero-")]
    assert active_index < min(recent_zero_indexes)
    assert active_index < 6
    assert data[active_index]["total_watch_seconds"] == 14
    assert data[active_index]["last_event_type"] == "note_watch"


@pytest.mark.asyncio
async def test_review_settings_activity_enrichment(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "knowledge.txt").write_text(
        "# 概率基础\n\n概率描述事件发生的可能性。\n\n- 样本空间表示所有可能结果\n- 事件是样本空间的子集\n\n# 概率基础\n\n概率描述事件发生的可能性。\n\n# 条件概率\n\n当已知事件 A 发生时，再看事件 B 发生的概率。",
        encoding="utf-8",
    )

    scan_response = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports"},
        headers=auth_headers,
    )
    asset_id = scan_response.json()["data"]["assets"][0]["id"]

    generate_response = await client.post(
        "/api/v1/notes/generate",
        json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
        headers=auth_headers,
    )
    note_id = generate_response.json()["data"]["generated_note_ids"][0]

    bootstrap_response = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [note_id], "all_notes": False},
        headers=auth_headers,
    )
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json()["data"]["created_knowledge_points"] >= 2

    note_detail_response = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert note_detail_response.status_code == 200

    note_watch_response = await client.post(
        f"/api/v1/notes/{note_id}/watch",
        json={"watch_seconds": 18},
        headers=auth_headers,
    )
    assert note_watch_response.status_code == 200

    queue_response = await client.get("/api/v1/review/queue?limit=10&due_only=true", headers=auth_headers)
    card_id = queue_response.json()["data"][0]["card_id"]
    knowledge_point = queue_response.json()["data"][0]["knowledge_point"]
    assert knowledge_point["summary_text"]
    assert knowledge_point["source_anchor"]
    assert isinstance(knowledge_point["tags_json"].get("tags"), list)
    assert knowledge_point["tags_json"].get("line_span")

    grade_response = await client.post(
        f"/api/v1/review/session/{card_id}/grade",
        json={"rating": 3, "duration_seconds": 42, "note": "理解更稳定"},
        headers=auth_headers,
    )
    assert grade_response.status_code == 200

    activity = await client.get("/api/v1/admin/user-activity", headers=auth_headers)
    assert activity.status_code == 200
    first = activity.json()["data"][0]
    assert first["page_view_count"] == 1
    assert first["note_view_count"] == 1
    assert first["review_watch_seconds"] >= 42
    assert first["total_watch_seconds"] >= 60
    assert first["last_event_type"] in {"review_grade", "review_log", "note_watch", "note_view", "login"}


@pytest.mark.asyncio
async def test_settings_and_admin_main_chain(client, auth_headers, tmp_path, monkeypatch):
    settings = get_settings()
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    settings.workspace_root = str(workspace_root)

    system_get = await client.get("/api/v1/settings/system", headers=auth_headers)
    assert system_get.status_code == 200
    assert system_get.json()["data"]["workspace_root"]

    system_put = await client.put(
        "/api/v1/settings/system",
        json={
            "allow_registration": True,
            "workspace_root": str(workspace_root),
            "timezone": "UTC",
            "review_retention_target": "90d",
        },
        headers=auth_headers,
    )
    assert system_put.status_code == 200
    assert system_put.json()["data"]["review_retention_target"] == "90"

    ai_put = await client.put(
        "/api/v1/settings/ai",
        json={
            "providers": [
                {
                    "provider_type": "llm",
                    "base_url": "https://example.com/v1",
                    "api_key": "sk-test",
                    "model_name": "demo-model",
                    "extra_json": "{\"temperature\":0.2}",
                    "is_enabled": True,
                }
            ]
        },
        headers=auth_headers,
    )
    assert ai_put.status_code == 200
    assert ai_put.json()["data"]["providers"][0]["provider_type"] == "llm"
    assert ai_put.json()["data"]["providers"][0]["api_key"] == ""
    assert ai_put.json()["data"]["providers"][0]["has_api_key"] is True
    assert "sk-test" not in ai_put.text

    ai_get = await client.get("/api/v1/settings/ai", headers=auth_headers)
    assert ai_get.status_code == 200
    assert ai_get.json()["data"]["providers"][0]["api_key"] == ""
    assert ai_get.json()["data"]["providers"][0]["has_api_key"] is True
    assert ai_get.json()["data"]["providers"][0]["api_key_masked"]
    assert ai_get.json()["data"]["providers"][0]["api_key_masked"] != "sk-test"
    assert "*" in ai_get.json()["data"]["providers"][0]["api_key_masked"]
    assert "sk-test" not in ai_get.text

    obsidian_put = await client.put(
        "/api/v1/settings/obsidian",
        json={
            "enabled": True,
            "vault_path": str(workspace_root),
            "vault_name": "vault-main",
            "vault_id": "",
            "obsidian_headless_path": "/usr/local/bin/obsidian-headless",
            "config_dir": "/tmp/obsidian-config",
            "device_name": "server-a",
            "sync_command": "ob sync",
        },
        headers=auth_headers,
    )
    assert obsidian_put.status_code == 200
    assert obsidian_put.json()["data"]["enabled"] is True

    async def fake_test_provider(**kwargs):
        return {"status": "ok", "message": f"{kwargs['provider_type'].value} provider reachable"}

    monkeypatch.setattr("app.services.provider_probe_service.ProviderProbeService.test_provider", fake_test_provider)
    provider_test = await client.post(
        "/api/v1/settings/test-provider",
        json={
            "provider_type": "llm",
            "base_url": "https://example.com/v1",
            "api_key": "sk-test",
            "model_name": "demo-model",
        },
        headers=auth_headers,
    )
    assert provider_test.status_code == 200
    assert provider_test.json()["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_ai_settings_update_preserves_old_key_and_replaces_when_new_key_provided(client, auth_headers, session_factory):
    initial_put = await client.put(
        "/api/v1/settings/ai",
        json={
            "providers": [
                {
                    "provider_type": "embedding",
                    "base_url": "https://example.com/v1",
                    "api_key": "sk-old-secret",
                    "model_name": "text-embedding-demo",
                    "extra_json": {},
                    "is_enabled": True,
                }
            ]
        },
        headers=auth_headers,
    )
    assert initial_put.status_code == 200

    preserve_put = await client.put(
        "/api/v1/settings/ai",
        json={
            "providers": [
                {
                    "provider_type": "embedding",
                    "base_url": "https://example.com/v2",
                    "api_key": "",
                    "model_name": "text-embedding-demo-2",
                    "extra_json": {"dimensions": 1024},
                    "is_enabled": True,
                }
            ]
        },
        headers=auth_headers,
    )
    assert preserve_put.status_code == 200
    assert "sk-old-secret" not in preserve_put.text

    async with session_factory() as session:
        embedding = (
            await session.execute(select(AIProviderConfig).where(AIProviderConfig.provider_type == ProviderType.EMBEDDING.value))
        ).scalar_one()
        assert embedding.base_url == "https://example.com/v2"
        assert embedding.model_name == "text-embedding-demo-2"
        assert embedding.api_key_encrypted == "sk-old-secret"
        assert embedding.extra_json == {"dimensions": 1024}

    replace_put = await client.put(
        "/api/v1/settings/ai",
        json={
            "providers": [
                {
                    "provider_type": "embedding",
                    "base_url": "https://example.com/v3",
                    "api_key": "sk-new-secret",
                    "model_name": "text-embedding-demo-3",
                    "extra_json": {},
                    "is_enabled": False,
                }
            ]
        },
        headers=auth_headers,
    )
    assert replace_put.status_code == 200
    assert replace_put.json()["data"]["providers"][0]["api_key"] == ""
    assert replace_put.json()["data"]["providers"][0]["has_api_key"] is True
    assert "sk-new-secret" not in replace_put.text

    async with session_factory() as session:
        embedding = (
            await session.execute(select(AIProviderConfig).where(AIProviderConfig.provider_type == ProviderType.EMBEDDING.value))
        ).scalar_one()
        assert embedding.base_url == "https://example.com/v3"
        assert embedding.model_name == "text-embedding-demo-3"
        assert embedding.api_key_encrypted == "sk-new-secret"
        assert embedding.is_enabled is False


@pytest.mark.asyncio
async def test_provider_test_supports_stt_and_ocr(client, auth_headers, monkeypatch):
    calls: list[tuple[str, str]] = []

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url.startswith("https://api.siliconflow.cn/"):
            calls.append((url, "json" if "json" in kwargs else "multipart"))

            class Response:
                status_code = 200
                is_success = True

            return Response()
        return await original_post(self, url, *args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    stt_response = await client.post(
        "/api/v1/settings/test-provider",
        json={
            "provider_type": "stt",
            "base_url": "https://api.siliconflow.cn/v1",
            "api_key": "sk-test",
            "model_name": "FunAudioLLM/SenseVoiceSmall",
        },
        headers=auth_headers,
    )
    assert stt_response.status_code == 200

    ocr_response = await client.post(
        "/api/v1/settings/test-provider",
        json={
            "provider_type": "ocr",
            "base_url": "https://api.siliconflow.cn/v1",
            "api_key": "sk-test",
            "model_name": "deepseek-ai/DeepSeek-OCR",
        },
        headers=auth_headers,
    )
    assert ocr_response.status_code == 200

    assert calls[0][0] == "https://api.siliconflow.cn/v1/audio/transcriptions"
    assert calls[0][1] == "multipart"
    assert calls[1][0] == "https://api.siliconflow.cn/v1/chat/completions"
    assert calls[1][1] == "json"


@pytest.mark.asyncio
async def test_text_markdown_and_docx_uploads_can_generate_note(client, workspace_root, auth_headers, session_factory, monkeypatch):
    def make_docx_bytes(text: str) -> bytes:
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
                f"""<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>""",
            )
        return buffer.getvalue()

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

    class MockChatResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": '{"title":"结构化总结","subject":"未分类","markdown_body":"## 结构化总结\\n\\n- 关键知识点已提取","warnings":[],"confidence":0.8,"summary":"关键知识点已提取"}'}
                            ]
                        }
                    }
                ]
            }

    original_post = AsyncClient.post

    async def fake_post(self, url, *args, **kwargs):  # noqa: ANN001
        if isinstance(url, str) and url == "https://example.com/v1/chat/completions":
            return MockChatResponse()
        if isinstance(url, str) and url == "https://example.com/v1/embeddings":
            inputs = kwargs.get("json", {}).get("input", [])
            data = [{"index": idx, "embedding": [1.0, 0.0]} for idx, _ in enumerate(inputs)]
            class MockEmbeddingResponse:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"model": "demo-embed", "data": data, "usage": {"prompt_tokens": 1, "total_tokens": 1}}
            return MockEmbeddingResponse()
        return await original_post(self, url, *args, **kwargs)

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    txt_upload_response = await client.post(
        "/api/v1/sources/upload",
        files={
            "file": (
                "lesson.txt",
                "TXT 学习资料\n监督学习与无监督学习".encode("utf-8"),
                "text/plain",
            )
        },
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert txt_upload_response.status_code == 200
    txt_asset = txt_upload_response.json()["data"]
    assert txt_asset["file_type"] == "text"

    md_upload_response = await client.post(
        "/api/v1/sources/upload",
        files={
            "file": (
                "lesson.md",
                "# Markdown 学习资料\n\n矩阵分解与降维".encode("utf-8"),
                "text/markdown",
            )
        },
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert md_upload_response.status_code == 200
    md_asset = md_upload_response.json()["data"]
    assert md_asset["file_type"] == "markdown"

    docx_upload_response = await client.post(
        "/api/v1/sources/upload",
        files={
            "file": (
                "lesson.docx",
                make_docx_bytes("DOCX 学习资料\n线性代数与概率论"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert docx_upload_response.status_code == 200
    docx_asset = docx_upload_response.json()["data"]
    assert docx_asset["file_type"] == "text"

    generate_response = await client.post(
        "/api/v1/notes/generate",
        json={"source_asset_ids": [txt_asset["id"], md_asset["id"], docx_asset["id"]], "note_directory": "notes/generated"},
        headers=auth_headers,
    )
    assert generate_response.status_code == 200
    written_paths = generate_response.json()["data"]["written_paths"]
    assert len(written_paths) == 3

    for written_path in written_paths:
        note_path = Path(workspace_root) / written_path
        assert note_path.exists()
        content = note_path.read_text(encoding="utf-8")
        if written_path.endswith(".md") and "lesson" in Path(written_path).name:
            assert "AI 整理笔记" in content

    txt_content = (Path(workspace_root) / written_paths[0]).read_text(encoding="utf-8")
    md_content = (Path(workspace_root) / written_paths[1]).read_text(encoding="utf-8")
    docx_content = (Path(workspace_root) / written_paths[2]).read_text(encoding="utf-8")
    combined_content = "\n".join([txt_content, md_content, docx_content])
    assert "TXT 学习资料" in combined_content
    assert "监督学习与无监督学习" in combined_content
    assert "Markdown 学习资料" in combined_content
    assert "矩阵分解与降维" in combined_content
    assert "DOCX 学习资料" in combined_content
    assert "线性代数与概率论" in combined_content
    assert "规范化文本摘录" in combined_content

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    note_jobs = [job for job in jobs_response.json()["data"] if job["job_type"] == "note_generation"]
    assert note_jobs
    latest_job = note_jobs[0]
    stages = {log.get("stage") for log in latest_job["logs_json"] if log.get("stage")}
    assert {"ingest", "extract", "normalize", "generate", "write"}.issubset(stages)

    users = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert users.status_code == 200
    assert len(users.json()["data"]) >= 1

    login_events = await client.get("/api/v1/admin/login-events", headers=auth_headers)
    assert login_events.status_code == 200
    assert len(login_events.json()["data"]) >= 1
    assert login_events.json()["data"][0]["event_type"] == "login"

    activity = await client.get("/api/v1/admin/user-activity", headers=auth_headers)
    assert activity.status_code == 200
    assert activity.json()["data"][0]["username"] == "admin"

    export_response = await client.post("/api/v1/admin/database/export", headers=auth_headers)
    assert export_response.status_code == 200
    export_path = Path(export_response.json()["data"]["path"])
    assert export_path.exists()
    with zipfile.ZipFile(export_path, "r") as zf:
        assert "database.sqlite3" in zf.namelist()
        assert "metadata.json" in zf.namelist()

    import_bytes = export_path.read_bytes()
    import_response = await client.post(
        "/api/v1/admin/database/import",
        files={"file": ("backup.zip", import_bytes, "application/zip")},
        headers={k: v for k, v in auth_headers.items() if k.lower() != "content-type"},
    )
    assert import_response.status_code == 200
    assert import_response.json()["data"]["imported"] is True

    class SyncResult:
        def __init__(self):
            self.executed = True
            self.command = ["obsidian-headless", "sync"]
            self.stdout = "done"
            self.stderr = ""

        def model_dump(self):
            return {
                "executed": self.executed,
                "command": self.command,
                "stdout": self.stdout,
                "stderr": self.stderr,
            }

    monkeypatch.setattr("app.integrations.obsidian_sync.ObsidianHeadlessSyncService.sync", lambda: SyncResult())
    sync_response = await client.post("/api/v1/admin/obsidian/sync", headers=auth_headers)
    assert sync_response.status_code == 200
    assert sync_response.json()["data"]["executed"] is True


@pytest.mark.asyncio
async def test_admin_settings_forbidden_for_viewer(viewer_client):
    login_response = await viewer_client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "ChangeMe123!"},
    )
    token = login_response.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for method, path, kwargs in [
        ("get", "/api/v1/settings/system", {}),
        ("put", "/api/v1/settings/system", {"json": {"allow_registration": False, "workspace_root": "/tmp", "timezone": "UTC", "review_retention_target": "30d"}}),
        ("get", "/api/v1/admin/users", {}),
        ("post", "/api/v1/admin/database/export", {}),
    ]:
        response = await getattr(viewer_client, method)(path, headers=headers, **kwargs)
        assert response.status_code == 403
