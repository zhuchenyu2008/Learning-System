from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_generate_note_and_query_apis(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "lesson.txt").write_text("机器学习基础\n监督学习与无监督学习", encoding="utf-8")

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
    assert generate_response.status_code == 200
    generate_payload = generate_response.json()["data"]
    assert len(generate_payload["generated_note_ids"]) == 1
    assert generate_payload["written_paths"][0] == "notes/generated/lesson.md"

    note_path = Path(workspace_root) / "notes/generated/lesson.md"
    assert note_path.exists()
    assert "AI 整理笔记" in note_path.read_text(encoding="utf-8")

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
    assert detail["relative_path"] == "notes/generated/lesson.md"
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
