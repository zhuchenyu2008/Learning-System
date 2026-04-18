import zipfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models.enums import UserRole
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

    note_detail_response = await client.get(f"/api/v1/notes/{note_id}?watch_seconds=18", headers=auth_headers)
    assert note_detail_response.status_code == 200

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
    assert first["page_view_count"] >= 1
    assert first["note_view_count"] >= 1
    assert first["review_watch_seconds"] >= 42
    assert first["total_watch_seconds"] >= 60
    assert first["last_event_type"] in {"review_grade", "review_log", "note_view", "login"}


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

    ai_get = await client.get("/api/v1/settings/ai", headers=auth_headers)
    assert ai_get.status_code == 200
    assert ai_get.json()["data"]["providers"][0]["api_key"] == "sk-test"

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
