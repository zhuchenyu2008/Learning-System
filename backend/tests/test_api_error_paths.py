from pathlib import Path

import pytest


async def _prepare_generated_note(client, workspace_root, auth_headers) -> int:
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "lesson.txt").write_text("# 线性代数\n\n矩阵与向量是基础。", encoding="utf-8")

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
    return generate_response.json()["data"]["generated_note_ids"][0]


@pytest.mark.asyncio
async def test_sources_notes_jobs_error_paths_and_permissions(client, workspace_root, auth_headers, viewer_auth_headers):
    hidden_dir = Path(workspace_root) / "imports/.private"
    hidden_dir.mkdir(parents=True, exist_ok=True)
    (hidden_dir / "secret.txt").write_text("hidden", encoding="utf-8")

    scan_hidden = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports", "recursive": True, "include_hidden": False},
        headers=auth_headers,
    )
    assert scan_hidden.status_code == 200
    assert scan_hidden.json()["data"]["scanned_files"] == 0

    scan_include_hidden = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports", "recursive": True, "include_hidden": True},
        headers=auth_headers,
    )
    assert scan_include_hidden.status_code == 200
    assert scan_include_hidden.json()["data"]["scanned_files"] == 1

    viewer_sources = await client.get("/api/v1/sources", headers=viewer_auth_headers)
    assert viewer_sources.status_code == 403

    note_id = await _prepare_generated_note(client, workspace_root, auth_headers)

    viewer_note_list = await client.get("/api/v1/notes", headers=viewer_auth_headers)
    assert viewer_note_list.status_code == 200
    assert len(viewer_note_list.json()["data"]) >= 1

    missing_note = await client.get("/api/v1/notes/99999", headers=viewer_auth_headers)
    assert missing_note.status_code == 404
    assert missing_note.json()["detail"] == "Note not found"

    unauthenticated_generate = await client.post(
        "/api/v1/notes/generate",
        json={"source_asset_ids": [1], "note_directory": "notes/generated"},
    )
    assert unauthenticated_generate.status_code == 401

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    first_job_id = jobs_response.json()["data"][0]["id"]

    job_detail = await client.get(f"/api/v1/jobs/{first_job_id}", headers=auth_headers)
    assert job_detail.status_code == 200
    assert job_detail.json()["data"]["id"] == first_job_id

    missing_job = await client.get("/api/v1/jobs/99999", headers=auth_headers)
    assert missing_job.status_code == 404
    assert missing_job.json()["detail"] == "Job not found"

    viewer_jobs = await client.get("/api/v1/jobs", headers=viewer_auth_headers)
    assert viewer_jobs.status_code == 403

    note_detail = await client.get(f"/api/v1/notes/{note_id}", headers=viewer_auth_headers)
    assert note_detail.status_code == 200
    assert note_detail.json()["data"]["id"] == note_id

    note_watch = await client.post(
        f"/api/v1/notes/{note_id}/watch",
        json={"watch_seconds": 12},
        headers=viewer_auth_headers,
    )
    assert note_watch.status_code == 200
    assert note_watch.json()["data"]["watch_seconds"] == 12


@pytest.mark.asyncio
async def test_review_and_settings_error_paths(client, workspace_root, auth_headers, viewer_auth_headers, monkeypatch):
    note_id = await _prepare_generated_note(client, workspace_root, auth_headers)

    bootstrap_invalid = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [0], "all_notes": False},
        headers=viewer_auth_headers,
    )
    assert bootstrap_invalid.status_code == 422

    bootstrap_ok = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [note_id], "all_notes": False},
        headers=viewer_auth_headers,
    )
    assert bootstrap_ok.status_code == 200

    queue_response = await client.get("/api/v1/review/queue?limit=10&due_only=true", headers=viewer_auth_headers)
    assert queue_response.status_code == 200
    card_id = queue_response.json()["data"][0]["card_id"]

    invalid_grade = await client.post(
        f"/api/v1/review/session/{card_id}/grade",
        json={"rating": 5, "duration_seconds": 10},
        headers=viewer_auth_headers,
    )
    assert invalid_grade.status_code == 422

    missing_card_grade = await client.post(
        "/api/v1/review/session/99999/grade",
        json={"rating": 3, "duration_seconds": 10},
        headers=viewer_auth_headers,
    )
    assert missing_card_grade.status_code == 404
    assert missing_card_grade.json()["detail"] == "Review card not found"

    invalid_log = await client.post(
        "/api/v1/review/logs",
        json={"review_card_id": card_id, "rating": 0, "duration_seconds": 10},
        headers=viewer_auth_headers,
    )
    assert invalid_log.status_code == 422

    viewer_settings = await client.get("/api/v1/settings/system", headers=viewer_auth_headers)
    assert viewer_settings.status_code == 403

    async def fake_failed_provider(**kwargs):
        return {"status": "error", "message": f"{kwargs['model_name']} unavailable"}

    monkeypatch.setattr("app.services.provider_probe_service.ProviderProbeService.test_provider", fake_failed_provider)
    failed_provider = await client.post(
        "/api/v1/settings/test-provider",
        json={
            "provider_type": "llm",
            "base_url": "https://example.com/v1",
            "api_key": "sk-test",
            "model_name": "demo-model",
        },
        headers=auth_headers,
    )
    assert failed_provider.status_code == 502
    assert failed_provider.json()["detail"] == "demo-model unavailable"
