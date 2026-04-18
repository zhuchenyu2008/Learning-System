from __future__ import annotations

import shutil
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.admin_entities import ObsidianSetting, UserActivitySnapshot
from app.models.ai_provider_config import AIProviderConfig
from app.models.enums import JobType, ProviderType
from app.models.login_event import LoginEvent
from app.models.review_log import ReviewLog
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.services.job_service import JobService


class SettingsAdminService:
    @staticmethod
    async def get_or_create_system_setting(session: AsyncSession) -> SystemSetting:
        result = await session.execute(select(SystemSetting).limit(1))
        setting = result.scalar_one_or_none()
        if setting is None:
            settings = get_settings()
            setting = SystemSetting(
                allow_registration=False,
                workspace_root=settings.workspace_root,
                timezone="UTC",
                review_retention_target=30,
            )
            session.add(setting)
            await session.commit()
            await session.refresh(setting)
        return setting

    @staticmethod
    async def update_system_setting(
        session: AsyncSession,
        *,
        allow_registration: bool,
        workspace_root: str,
        timezone: str,
        review_retention_target: str,
    ) -> SystemSetting:
        setting = await SettingsAdminService.get_or_create_system_setting(session)
        numeric_retention = int("".join(ch for ch in review_retention_target if ch.isdigit()) or review_retention_target)
        setting.allow_registration = allow_registration
        setting.workspace_root = workspace_root
        setting.timezone = timezone
        setting.review_retention_target = numeric_retention
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        runtime_settings = get_settings()
        runtime_settings.workspace_root = workspace_root
        return setting

    @staticmethod
    async def list_ai_providers(session: AsyncSession) -> list[AIProviderConfig]:
        result = await session.execute(select(AIProviderConfig).order_by(AIProviderConfig.provider_type.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def upsert_ai_providers(session: AsyncSession, providers: list[dict]) -> list[AIProviderConfig]:
        existing_result = await session.execute(select(AIProviderConfig))
        existing = {item.provider_type: item for item in existing_result.scalars().all()}

        for payload in providers:
            key = payload["provider_type"].value if isinstance(payload["provider_type"], ProviderType) else str(payload["provider_type"])
            item = existing.get(key)
            if item is None:
                item = AIProviderConfig(provider_type=key, base_url="", api_key_encrypted="", model_name="", extra_json={}, is_enabled=False)
            item.base_url = payload["base_url"]
            item.api_key_encrypted = payload.get("api_key") or item.api_key_encrypted or ""
            item.model_name = payload["model_name"]
            item.extra_json = payload.get("extra_json") or {}
            item.is_enabled = payload["is_enabled"]
            session.add(item)

        await session.commit()
        return await SettingsAdminService.list_ai_providers(session)

    @staticmethod
    async def get_or_create_obsidian_setting(session: AsyncSession) -> ObsidianSetting:
        result = await session.execute(select(ObsidianSetting).limit(1))
        setting = result.scalar_one_or_none()
        if setting is None:
            runtime = get_settings()
            setting = ObsidianSetting(
                enabled=False,
                vault_path=runtime.workspace_root,
                vault_name=runtime.obsidian_vault or "",
                vault_id="",
                obsidian_headless_path=runtime.obsidian_headless_path,
                config_dir=runtime.obsidian_config_dir or "",
                device_name=runtime.obsidian_device_name or "",
                sync_command="ob sync",
                extra_json={},
            )
            session.add(setting)
            await session.commit()
            await session.refresh(setting)
        return setting

    @staticmethod
    async def update_obsidian_setting(session: AsyncSession, payload: dict) -> ObsidianSetting:
        setting = await SettingsAdminService.get_or_create_obsidian_setting(session)
        for key, value in payload.items():
            setattr(setting, key, value)
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        runtime = get_settings()
        runtime.obsidian_headless_path = setting.obsidian_headless_path
        runtime.obsidian_vault = setting.vault_name or setting.vault_id or None
        runtime.obsidian_config_dir = setting.config_dir or None
        runtime.obsidian_device_name = setting.device_name or None
        if setting.vault_path:
            runtime.workspace_root = setting.vault_path
        return setting

    @staticmethod
    async def list_users(session: AsyncSession) -> list[User]:
        result = await session.execute(select(User).order_by(User.created_at.desc(), User.id.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def list_login_events(session: AsyncSession) -> list[LoginEvent]:
        result = await session.execute(select(LoginEvent).order_by(LoginEvent.created_at.desc(), LoginEvent.id.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def build_user_activity(session: AsyncSession) -> list[dict]:
        users = await SettingsAdminService.list_users(session)
        snapshots_result = await session.execute(select(UserActivitySnapshot))
        snapshots = {item.user_id: item for item in snapshots_result.scalars().all()}

        output: list[dict] = []
        for user in users:
            snapshot = snapshots.get(user.id)
            if snapshot is None:
                review_count_result = await session.execute(
                    select(ReviewLog).where(ReviewLog.user_id == user.id)
                )
                review_logs = list(review_count_result.scalars().all())
                total_watch_seconds = sum(item.duration_seconds for item in review_logs)
                review_count = len(review_logs)
                last_activity_at = max((item.created_at for item in review_logs), default=user.last_login_at)
                snapshot = UserActivitySnapshot(
                    user_id=user.id,
                    total_watch_seconds=total_watch_seconds,
                    review_watch_seconds=total_watch_seconds,
                    review_count=review_count,
                    page_view_count=0,
                    note_view_count=0,
                    last_activity_at=last_activity_at,
                    last_event_type="review_log" if review_logs else "login",
                )
                session.add(snapshot)
                await session.commit()
                await session.refresh(snapshot)
            output.append(
                {
                    "id": snapshot.id,
                    "user_id": user.id,
                    "username": user.username,
                    "total_watch_seconds": snapshot.total_watch_seconds,
                    "review_count": snapshot.review_count,
                    "page_view_count": snapshot.page_view_count,
                    "note_view_count": snapshot.note_view_count,
                    "review_watch_seconds": snapshot.review_watch_seconds,
                    "last_seen_at": snapshot.last_activity_at or user.last_login_at,
                    "last_activity_at": snapshot.last_activity_at,
                    "last_event_type": snapshot.last_event_type,
                }
            )
        return output

    @staticmethod
    async def record_login_event(
        session: AsyncSession,
        *,
        user: User,
        event_type: str = "login",
        ip_address: str | None = None,
    ) -> LoginEvent:
        created_at = user.last_login_at or datetime.now(timezone.utc)
        event = LoginEvent(
            user_id=user.id,
            username=user.username,
            event_type=event_type,
            ip_address=ip_address,
            created_at=created_at,
        )
        session.add(event)
        snapshot_result = await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == user.id))
        snapshot = snapshot_result.scalar_one_or_none()
        if snapshot is None:
            snapshot = UserActivitySnapshot(user_id=user.id)
        snapshot.last_activity_at = created_at
        snapshot.last_event_type = event_type
        session.add(snapshot)
        await session.commit()
        await session.refresh(event)
        return event

    @staticmethod
    def _backup_dir() -> Path:
        base = Path(get_settings().workspace_root).expanduser().resolve() / ".learning_system_admin"
        base.mkdir(parents=True, exist_ok=True)
        return base

    @staticmethod
    async def export_database(session: AsyncSession) -> dict:
        backup_dir = SettingsAdminService._backup_dir()
        job = await JobService.create_job(session, JobType.DATABASE_EXPORT, {"action": "database_export"})
        await JobService.mark_running(session, job)

        runtime = get_settings()
        db_url = runtime.database_url
        if not db_url.startswith("sqlite+aiosqlite:///"):
            raise ValueError("Database export currently supports sqlite only")
        db_path = Path(db_url.replace("sqlite+aiosqlite:///", "")).resolve()
        filename = f"learning-system-export-{job.id}.zip"
        archive_path = backup_dir / filename

        metadata = {
            "database_url": db_url,
            "workspace_root": runtime.workspace_root,
            "exported_job_id": job.id,
        }
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if db_path.exists():
                zf.write(db_path, arcname="database.sqlite3")
            import json
            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

        await JobService.mark_completed(session, job, {"path": str(archive_path), "filename": filename})
        return {"job_id": job.id, "path": str(archive_path), "filename": filename}

    @staticmethod
    async def import_database(session: AsyncSession, upload: UploadFile) -> dict:
        backup_dir = SettingsAdminService._backup_dir()
        job = await JobService.create_job(session, JobType.DATABASE_IMPORT, {"action": "database_import", "filename": upload.filename})
        await JobService.mark_running(session, job)

        temp_zip = backup_dir / f"import-{job.id}.zip"
        temp_zip.write_bytes(await upload.read())

        runtime = get_settings()
        db_url = runtime.database_url
        if not db_url.startswith("sqlite+aiosqlite:///"):
            raise ValueError("Database import currently supports sqlite only")
        db_path = Path(db_url.replace("sqlite+aiosqlite:///", "")).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as zf:
            members = set(zf.namelist())
            if "database.sqlite3" not in members:
                raise ValueError("Import archive missing database.sqlite3")
            extracted = backup_dir / f"import-{job.id}-database.sqlite3"
            with zf.open("database.sqlite3") as src, extracted.open("wb") as dst:
                shutil.copyfileobj(src, dst)

        await JobService.mark_completed(session, job, {"imported": True, "path": str(db_path)})
        await SettingsAdminService._merge_sqlite_database(source_path=extracted, target_path=db_path)
        return {"job_id": job.id, "imported": True, "path": str(db_path)}

    @staticmethod
    async def reset_activity_snapshots(session: AsyncSession) -> None:
        await session.execute(delete(UserActivitySnapshot))
        await session.commit()

    @staticmethod
    async def _merge_sqlite_database(*, source_path: Path, target_path: Path) -> None:
        if not source_path.exists():
            raise ValueError("Extracted sqlite database not found")

        with sqlite3.connect(target_path) as target_conn, sqlite3.connect(source_path) as source_conn:
            target_conn.execute("PRAGMA foreign_keys = OFF")
            source_tables = [
                row[0]
                for row in source_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
            ]
            for table in source_tables:
                target_conn.execute(f'DELETE FROM "{table}"')
                column_rows = source_conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                columns = [row[1] for row in column_rows]
                if not columns:
                    continue
                quoted_columns = ", ".join(f'"{column}"' for column in columns)
                placeholders = ", ".join("?" for _ in columns)
                rows = source_conn.execute(f'SELECT {quoted_columns} FROM "{table}"').fetchall()
                if rows:
                    target_conn.executemany(
                        f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
                        rows,
                    )
            target_conn.commit()
            target_conn.execute("PRAGMA foreign_keys = ON")
