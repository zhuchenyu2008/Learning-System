from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_note_watch_reports_seconds_without_incrementing_view_counts(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "watch-only.txt").write_text("# Watch Only\n\n用于验证观看时长上报。", encoding="utf-8")

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

    detail_response = await client.get(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert detail_response.status_code == 200

    watch_response = await client.post(
        f"/api/v1/notes/{note_id}/watch",
        json={"watch_seconds": 15},
        headers=auth_headers,
    )
    assert watch_response.status_code == 200

    activity = await client.get("/api/v1/admin/user-activity", headers=auth_headers)
    assert activity.status_code == 200
    first = activity.json()["data"][0]
    assert first["page_view_count"] == 1
    assert first["note_view_count"] == 1
    assert first["total_watch_seconds"] == 15
    assert first["review_watch_seconds"] == 0
    assert first["last_event_type"] == "note_watch"
