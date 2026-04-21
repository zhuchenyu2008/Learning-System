from pathlib import Path

import pytest

from app.services.source_upload_service import SourceUploadService


class FakeUploadFile:
    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self._data = data
        self._offset = 0
        self.closed = False

    async def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = len(self._data) - self._offset
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_save_upload_streams_large_file_to_workspace(session_factory, workspace_root):
    payload = b"a" * (1024 * 1024 + 123) + b"tail"
    upload = FakeUploadFile("large.wav", payload)

    async with session_factory() as session:
        asset = await SourceUploadService.save_upload(session, upload, upload_dir="uploads/sources")

    saved_path = Path(workspace_root) / asset.file_path
    assert saved_path.exists()
    assert saved_path.read_bytes() == payload
    assert asset.file_type == "audio"
    assert asset.metadata_json["size_bytes"] == len(payload)
    assert upload.closed is True
