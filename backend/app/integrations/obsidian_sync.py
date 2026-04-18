from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.schemas.integrations import ObsidianSyncResult


class ObsidianHeadlessSyncService:
    @staticmethod
    def sync() -> ObsidianSyncResult:
        settings = get_settings()
        executable = getattr(settings, "obsidian_headless_path", "obsidian-headless")
        vault = getattr(settings, "obsidian_vault", None)
        config_dir = getattr(settings, "obsidian_config_dir", None)
        device_name = getattr(settings, "obsidian_device_name", None)

        if not vault or shutil.which(executable) is None:
            return ObsidianSyncResult(executed=False, command=None, stdout=None, stderr="obsidian-headless not configured")

        command = [executable, "sync", "--vault", vault]
        if config_dir:
            command.extend(["--config-dir", config_dir])
        if device_name:
            command.extend(["--device-name", device_name])

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return ObsidianSyncResult(
            executed=completed.returncode == 0,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
