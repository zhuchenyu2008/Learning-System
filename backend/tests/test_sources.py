from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_upload_source_registers_asset(client, workspace_root, auth_headers):
    response = await client.post(
        "/api/v1/sources/upload",
        files={"file": ("lesson.pdf", b"fake-pdf-content", "application/pdf")},
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    asset = payload["data"]
    assert asset["file_type"] == "pdf"
    assert asset["file_path"].startswith("uploads/sources/lesson-")

    uploaded_path = Path(workspace_root) / asset["file_path"]
    assert uploaded_path.exists()
    assert uploaded_path.read_bytes() == b"fake-pdf-content"

    list_response = await client.get("/api/v1/sources", headers=auth_headers)
    assert list_response.status_code == 200
    listed = list_response.json()["data"]
    assert len(listed) == 1
    assert listed[0]["id"] == asset["id"]


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


@pytest.mark.asyncio
async def test_delete_source_removes_asset_and_file(client, workspace_root, auth_headers):
    upload_response = await client.post(
        "/api/v1/sources/upload",
        files={"file": ("lesson.pdf", b"fake-pdf-content", "application/pdf")},
        data={"upload_dir": "uploads/sources"},
        headers=auth_headers,
    )
    assert upload_response.status_code == 200
    asset = upload_response.json()["data"]
    uploaded_path = Path(workspace_root) / asset["file_path"]
    assert uploaded_path.exists()

    delete_response = await client.delete(f"/api/v1/sources/{asset['id']}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["data"] == {"id": asset["id"]}
    assert not uploaded_path.exists()

    list_response = await client.get("/api/v1/sources", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []
