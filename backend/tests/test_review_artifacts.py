from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_review_summary_mindmap_main_chain(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "lesson.txt").write_text(
        "# 机器学习基础\n\n监督学习用于从标注数据学习映射。\n\n# 模型评估\n\n准确率、召回率、F1 是常见指标。",
        encoding="utf-8",
    )

    scan_response = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports"},
        headers=auth_headers,
    )
    assert scan_response.status_code == 200
    asset_id = scan_response.json()["data"]["assets"][0]["id"]

    generate_response = await client.post(
        "/api/v1/notes/generate",
        json={"source_asset_ids": [asset_id], "note_directory": "notes/generated"},
        headers=auth_headers,
    )
    assert generate_response.status_code == 200
    note_id = generate_response.json()["data"]["generated_note_ids"][0]

    bootstrap_response = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [note_id], "all_notes": False},
        headers=auth_headers,
    )
    assert bootstrap_response.status_code == 200
    bootstrap_data = bootstrap_response.json()["data"]
    assert bootstrap_data["created_knowledge_points"] >= 1
    assert bootstrap_data["created_cards"] >= 1

    overview_response = await client.get("/api/v1/review/overview", headers=auth_headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert overview["total_cards"] >= 1
    assert overview["due_today_count"] >= 1

    queue_response = await client.get("/api/v1/review/queue?limit=10&due_only=true", headers=auth_headers)
    assert queue_response.status_code == 200
    queue = queue_response.json()["data"]
    assert len(queue) >= 1
    card_id = queue[0]["card_id"]
    assert queue[0]["knowledge_point"]["title"]
    assert queue[0]["note"]["id"] == note_id

    grade_response = await client.post(
        f"/api/v1/review/session/{card_id}/grade",
        json={"rating": 3, "duration_seconds": 45, "note": "掌握较好"},
        headers=auth_headers,
    )
    assert grade_response.status_code == 200
    graded = grade_response.json()["data"]
    assert graded["card"]["state_json"]["last_rating"] == 3
    assert graded["review_log"]["review_card_id"] == card_id

    create_log_response = await client.post(
        "/api/v1/review/logs",
        json={"review_card_id": card_id, "rating": 2, "duration_seconds": 30, "note": "补充记录"},
        headers=auth_headers,
    )
    assert create_log_response.status_code == 200

    logs_response = await client.get("/api/v1/review/logs?limit=10", headers=auth_headers)
    assert logs_response.status_code == 200
    logs = logs_response.json()["data"]
    assert len(logs) >= 2

    summary_response = await client.post(
        "/api/v1/summaries/generate",
        json={"scope": "manual", "note_ids": [note_id], "prompt_extra": "面向期末复习"},
        headers=auth_headers,
    )
    assert summary_response.status_code == 200
    summary_data = summary_response.json()["data"]
    assert summary_data["status"] == "completed"
    summary_path = Path(workspace_root) / summary_data["relative_path"]
    assert summary_path.exists()
    assert "机器学习基础" in summary_path.read_text(encoding="utf-8")

    summaries_response = await client.get("/api/v1/summaries", headers=auth_headers)
    assert summaries_response.status_code == 200
    summaries = summaries_response.json()["data"]
    assert len(summaries) == 1
    assert summaries[0]["artifact_type"] == "summary"

    mindmap_response = await client.post(
        "/api/v1/mindmaps/generate",
        json={"scope": "manual", "note_ids": [note_id], "prompt_extra": "按章节组织"},
        headers=auth_headers,
    )
    assert mindmap_response.status_code == 200
    mindmap_data = mindmap_response.json()["data"]
    assert mindmap_data["status"] == "completed"
    mindmap_path = Path(workspace_root) / mindmap_data["relative_path"]
    assert mindmap_path.exists()
    assert "```mermaid" in mindmap_path.read_text(encoding="utf-8")

    mindmaps_response = await client.get("/api/v1/mindmaps", headers=auth_headers)
    assert mindmaps_response.status_code == 200
    mindmaps = mindmaps_response.json()["data"]
    assert len(mindmaps) == 1
    assert mindmaps[0]["artifact_type"] == "mindmap"

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()["data"]
    assert len(jobs) >= 3
    artifact_jobs = [job for job in jobs if job["job_type"] in {"summary_generation", "mindmap_generation"}]
    assert artifact_jobs
    assert all(job["status"] == "completed" for job in artifact_jobs)
    assert all(job["started_at"] is not None for job in artifact_jobs)
    assert all(job["finished_at"] is not None for job in artifact_jobs)
    assert all(job["logs_json"] for job in artifact_jobs)

    scheduler_response = await client.get("/api/v1/scheduler/tasks", headers=auth_headers)
    assert scheduler_response.status_code == 200
    tasks = scheduler_response.json()["data"]
    assert len(tasks) >= 3
    assert any(task["name"] == "review.maintenance" for task in tasks)


@pytest.mark.asyncio
async def test_async_artifact_queue_metadata(client, auth_headers):
    from app.core.config import get_settings

    settings = get_settings()
    original_eager = settings.celery_task_always_eager
    settings.celery_task_always_eager = False

    try:
        with patch("app.api.v1.endpoints.summaries.generate_summary_task.delay") as delay_mock:
            delay_mock.return_value.id = "celery-summary-001"
            response = await client.post(
                "/api/v1/summaries/generate",
                json={"scope": "manual", "note_ids": [], "prompt_extra": "只测试排队"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["status"] == "queued"
        assert payload["celery_task_id"] == "celery-summary-001"

        jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
        jobs = jobs_response.json()["data"]
        queued_job = next(job for job in jobs if job["id"] == payload["job_id"])
        assert queued_job["status"] == "pending"
        assert queued_job["celery_task_id"] == "celery-summary-001"
        assert queued_job["result_json"]["celery_task_id"] == "celery-summary-001"
        assert any(log["message"] == "job dispatched to celery" for log in queued_job["logs_json"])
        assert any(log["message"] == "summary generation queued" for log in queued_job["logs_json"])
        assert queued_job["started_at"] is None
        assert queued_job["finished_at"] is None
    finally:
        settings.celery_task_always_eager = original_eager
