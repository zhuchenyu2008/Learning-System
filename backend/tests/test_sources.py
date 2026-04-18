from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_scan_sources_and_list(client, workspace_root, auth_headers):
    sample_dir = Path(workspace_root) / "imports"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "sample.txt").write_text("hello woven recall", encoding="utf-8")
    (sample_dir / "doc.md").write_text("# title", encoding="utf-8")

    response = await client.post(
        "/api/v1/sources/scan",
        json={"root_path": "imports", "recursive": True, "include_hidden": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["scanned_files"] == 2
    assert len(payload["data"]["assets"]) == 2

    list_response = await client.get("/api/v1/sources", headers=auth_headers)
    assert list_response.status_code == 200
    listed = list_response.json()["data"]
    assert len(listed) == 2
    assert {item["file_type"] for item in listed} == {"text", "markdown"}
