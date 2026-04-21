import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.models.enums import ArtifactType
from app.services.artifact_service import ArtifactService


@pytest.mark.parametrize(
    ("raw_body", "expected_body"),
    [
        ("mindmap\n  root((测试))", "mindmap\n  root((测试))"),
        ("```mermaid\nmindmap\n  root((测试))\n```", "mindmap\n  root((测试))"),
        ("```mermaid\n```mermaid\nmindmap\n  root((测试))\n```\n```", "mindmap\n  root((测试))"),
        ("mermaid\nmindmap\n  root((测试))", "mindmap\n  root((测试))"),
        ("这是解释\n\nmindmap\n  1. 核心概念\n    2. 关键步骤", "mindmap\n  root((核心概念))\n    关键步骤"),
    ],
)
def test_sanitize_mermaid_body_removes_nested_fences(raw_body, expected_body):
    assert ArtifactService._sanitize_mermaid_body(raw_body) == expected_body


def test_prepare_note_content_for_mindmap_removes_noise_sections():
    raw_content = """---
source_path: uploads/example.txt
---

# 线性代数

## AI 整理笔记

核心概念：向量空间、基、维数。

```mermaid
graph TD
  A-->B
```

## 待复习关键点
- [ ] 区分基与维数

## 原始提取摘录
这里是原始 OCR 内容
"""

    prepared = ArtifactService._prepare_note_content_for_artifact(raw_content, ArtifactType.MINDMAP)

    assert "source_path" not in prepared
    assert "```mermaid" not in prepared
    assert "原始提取摘录" not in prepared
    assert "核心概念：向量空间、基、维数。" in prepared
    assert "- 区分基与维数" in prepared


def test_trim_for_mindmap_prompt_prefers_clean_section_content():
    combined_source = """# 笔记A

title: metadata
source_path: uploads/a.txt

真正重点一
真正重点二

```python
print('ignore me')
```

## 原始提取摘录
很多噪声

# 笔记B

真正重点三
> 引用噪声
真正重点四
"""

    trimmed = ArtifactService._trim_for_mindmap_prompt(combined_source, per_section_limit=120, total_limit=200)

    assert "source_path" not in trimmed
    assert "print('ignore me')" not in trimmed
    assert "真正重点一" in trimmed
    assert "真正重点三" in trimmed


@pytest.mark.asyncio
async def test_note_generation_creates_separate_review_card_job(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "async-review.txt").write_text(
        "# 线性代数\n\n- 向量空间\n- 线性变换\n\n# 特征值\n\n特征值反映线性变换的伸缩性质。",
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

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()["data"]

    note_job = next(job for job in jobs if job["job_type"] == "note_generation")
    review_jobs = [job for job in jobs if job["job_type"] == "review_card_generation"]
    assert len(review_jobs) == 1

    review_job = review_jobs[0]
    assert review_job["status"] == "completed"
    assert review_job["payload_json"]["note_ids"] == [note_id]
    assert review_job["payload_json"]["parent_job_id"] == note_job["id"]
    assert review_job["payload_json"]["trigger"] == "note_generation"
    assert review_job["result_json"]["note_ids"] == [note_id]
    assert review_job["result_json"]["parent_job_id"] == note_job["id"]
    assert review_job["result_json"]["created_cards"] >= 1
    assert any(log["message"] == "review card generation pipeline started" for log in review_job["logs_json"])

    overview_response = await client.get("/api/v1/review/overview", headers=auth_headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert overview["total_cards"] >= 1


@pytest.mark.asyncio
async def test_review_card_generation_uses_ai_when_llm_available(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "ai-review.txt").write_text(
        "# 概率论\n\n条件概率表示在事件 A 已发生时事件 B 发生的概率。\n\n贝叶斯公式用于根据先验概率与条件概率反推后验概率。",
        encoding="utf-8",
    )

    scan_response = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports"},
        headers=auth_headers,
    )
    assert scan_response.status_code == 200
    asset_id = scan_response.json()["data"]["assets"][0]["id"]

    ai_note_payload = {
        "title": "概率论基础",
        "subject": "数学",
        "markdown_body": "# 概率论\n\n## 条件概率\n条件概率表示在事件 A 已发生时事件 B 发生的概率。\n\n## 贝叶斯公式\n贝叶斯公式用于根据先验概率与条件概率反推后验概率。",
    }
    ai_card_payload = {
        "items": [
            {
                "title": "条件概率",
                "question": "什么是条件概率？",
                "answer": "条件概率表示在事件 A 已发生时事件 B 发生的概率。",
                "card_kind": "short_answer",
                "tags": ["概率论", "条件概率"],
            },
            {
                "title": "贝叶斯公式",
                "question": "贝叶斯公式有什么作用？",
                "answer": "贝叶斯公式用于根据先验概率与条件概率反推后验概率。",
                "card_kind": "short_answer",
                "tags": ["概率论", "贝叶斯公式"],
            },
        ]
    }

    with patch("app.integrations.openai_compatible.OpenAICompatibleProviderAdapter.get_provider", new=AsyncMock(return_value=type("P", (), {"model_name": "test-llm"})())), patch(
        "app.integrations.openai_compatible.OpenAICompatibleProviderAdapter.chat",
        new=AsyncMock(side_effect=[type("R", (), {"content": json.dumps(ai_note_payload, ensure_ascii=False), "raw_response": {}})(), type("R", (), {"content": json.dumps(ai_card_payload, ensure_ascii=False), "raw_response": {}})()]),
    ):
        generate_response = await client.post(
            "/api/v1/notes/generate",
            json={"source_asset_ids": [asset_id], "note_directory": "notes/generated", "force_regenerate": True},
            headers=auth_headers,
        )

    assert generate_response.status_code == 200
    note_id = generate_response.json()["data"]["generated_note_ids"][0]

    jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()["data"]
    review_job = next(job for job in jobs if job["job_type"] == "review_card_generation")
    assert review_job["payload_json"]["note_ids"] == [note_id]
    assert review_job["result_json"]["generation_mode"] == "ai"
    assert review_job["result_json"]["ai_generated_knowledge_points"] == 2
    assert review_job["result_json"]["fallback_generated_knowledge_points"] == 0
    assert any(log["message"] == "review card ai generation started" for log in review_job["logs_json"])
    assert any(log["message"] == "review card ai generation completed" for log in review_job["logs_json"])
    assert any(log["message"] == "review card generation pipeline completed" for log in review_job["logs_json"])

    queue_response = await client.get("/api/v1/review/queue?limit=10&due_only=true", headers=auth_headers)
    assert queue_response.status_code == 200
    queue = queue_response.json()["data"]
    note_cards = [item for item in queue if item["note"]["id"] == note_id]
    assert len(note_cards) == 2
    assert {item["knowledge_point"]["title"] for item in note_cards} == {"条件概率", "贝叶斯公式"}
    assert all(item["knowledge_point"]["tags_json"]["source"] == "ai_review_card_generation" for item in note_cards)


@pytest.mark.asyncio
async def test_review_card_generation_falls_back_without_llm(session_factory, workspace_root):
    from app.models.note import Note

    note_path = workspace_root / "notes/generated/fallback-review.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        "# 线性代数\n\n向量空间是满足加法和数乘封闭性的集合。\n\n# 基\n\n基是能够张成整个向量空间且线性无关的一组向量。",
        encoding="utf-8",
    )

    async with session_factory() as session:
        note = Note(
            title="fallback-review",
            relative_path="notes/generated/fallback-review.md",
            note_type="source_note",
            content_hash="hash-fallback-review",
            source_asset_id=None,
            frontmatter_json={"generated": False},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

        with patch("app.integrations.openai_compatible.OpenAICompatibleProviderAdapter.get_provider", new=AsyncMock(return_value=None)):
            result = await __import__("app.services.review_service", fromlist=["ReviewService"]).ReviewService.bootstrap_cards(
                session,
                note_ids=[note.id],
                all_notes=False,
            )

        assert result["generation_mode"] == "fallback"
        assert result["ai_generated_knowledge_points"] == 0
        assert result["fallback_generated_knowledge_points"] >= 1


@pytest.mark.asyncio
async def test_review_generate_cards_queue_metadata_when_not_eager(client, auth_headers):
    from app.core.config import get_settings

    settings = get_settings()
    original_eager = settings.celery_task_always_eager
    settings.celery_task_always_eager = False

    try:
        with patch("app.api.v1.endpoints.review.generate_review_cards_task.delay") as delay_mock:
            delay_mock.return_value.id = "celery-review-001"
            response = await client.post(
                "/api/v1/review/cards/generate",
                json={"note_ids": [123], "all_notes": False},
                headers=auth_headers,
            )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["status"] == "queued"
        assert payload["celery_task_id"] == "celery-review-001"
        assert payload["created_cards"] == 0

        jobs_response = await client.get("/api/v1/jobs", headers=auth_headers)
        jobs = jobs_response.json()["data"]
        queued_job = next(job for job in jobs if job["id"] == payload["job_id"])
        assert queued_job["job_type"] == "review_card_generation"
        assert queued_job["status"] == "pending"
        assert queued_job["celery_task_id"] == "celery-review-001"
        assert queued_job["result_json"]["celery_task_id"] == "celery-review-001"
        assert any(log["message"] == "job dispatched to celery" for log in queued_job["logs_json"])
        assert any(log["message"] == "review card generation queued" for log in queued_job["logs_json"])
    finally:
        settings.celery_task_always_eager = original_eager


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
    assert bootstrap_data["note_ids"] == [note_id]
    assert bootstrap_data["created_knowledge_points"] >= 0
    assert bootstrap_data["created_cards"] >= 0

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
    mindmap_text = mindmap_path.read_text(encoding="utf-8")
    assert "```mermaid" in mindmap_text
    assert mindmap_text.count("```mermaid") == 1

    mindmaps_response = await client.get("/api/v1/mindmaps", headers=auth_headers)
    assert mindmaps_response.status_code == 200
    mindmaps = mindmaps_response.json()["data"]
    assert len(mindmaps) == 1
    assert mindmaps[0]["artifact_type"] == "mindmap"

    delete_summary_response = await client.delete(f"/api/v1/summaries/{summaries[0]['id']}", headers=auth_headers)
    assert delete_summary_response.status_code == 200
    delete_summary_data = delete_summary_response.json()["data"]
    assert delete_summary_data["artifact_id"] == summaries[0]["id"]
    assert delete_summary_data["deleted_note_id"] == summary_data["output_note_id"]
    assert delete_summary_data["deleted_relative_paths"] == [summary_data["relative_path"]]
    assert not summary_path.exists()

    summaries_after_delete = await client.get("/api/v1/summaries", headers=auth_headers)
    assert summaries_after_delete.status_code == 200
    assert summaries_after_delete.json()["data"] == []

    deleted_summary_note = await client.get(f"/api/v1/notes/{summary_data['output_note_id']}", headers=auth_headers)
    assert deleted_summary_note.status_code == 404

    delete_mindmap_response = await client.delete(f"/api/v1/mindmaps/{mindmaps[0]['id']}", headers=auth_headers)
    assert delete_mindmap_response.status_code == 200
    delete_mindmap_data = delete_mindmap_response.json()["data"]
    assert delete_mindmap_data["artifact_id"] == mindmaps[0]["id"]
    assert delete_mindmap_data["deleted_note_id"] == mindmap_data["output_note_id"]
    assert delete_mindmap_data["deleted_relative_paths"] == [mindmap_data["relative_path"]]
    assert not mindmap_path.exists()

    mindmaps_after_delete = await client.get("/api/v1/mindmaps", headers=auth_headers)
    assert mindmaps_after_delete.status_code == 200
    assert mindmaps_after_delete.json()["data"] == []

    deleted_mindmap_note = await client.get(f"/api/v1/notes/{mindmap_data['output_note_id']}", headers=auth_headers)
    assert deleted_mindmap_note.status_code == 404

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
        assert payload["artifact_id"] is None
        assert payload["output_note_id"] is None
        assert payload["relative_path"] is None

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
