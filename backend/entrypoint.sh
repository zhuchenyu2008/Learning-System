#!/bin/sh
set -eu

python - <<'PY'
import asyncio
import os
import subprocess
import sys
from urllib.parse import urlparse


def normalize_asyncpg_dsn(raw: str) -> str:
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw[len("postgresql+asyncpg://") :]
    return raw


async def prepare_alembic_state() -> None:
    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        return

    try:
        import asyncpg
    except Exception as exc:  # pragma: no cover - defensive startup fallback
        print(f"[entrypoint] skip alembic preparation: asyncpg unavailable ({exc})", file=sys.stderr)
        return

    dsn = normalize_asyncpg_dsn(raw_url)
    parsed = urlparse(dsn)
    database = (parsed.path or "/").lstrip("/")
    if not database:
        print("[entrypoint] skip alembic preparation: database name missing", file=sys.stderr)
        return

    conn = await asyncpg.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=database,
    )
    try:
        lock_key = 918_274_611
        await conn.execute("SELECT pg_advisory_lock($1)", lock_key)
        try:
            row = await conn.fetchrow(
                """
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'alembic_version'
                  AND column_name = 'version_num'
                """
            )
            current_length = row["character_maximum_length"] if row else None
            if current_length is not None and current_length < 255:
                await conn.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
                print(
                    f"[entrypoint] expanded alembic_version.version_num from varchar({current_length}) to varchar(255)",
                    file=sys.stderr,
                )

            has_version_table = current_length is not None
            if not has_version_table:
                known_tables = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                      AND table_type = 'BASE TABLE'
                      AND table_name IN (
                        'users',
                        'system_settings',
                        'ai_provider_configs',
                        'jobs',
                        'notes',
                        'review_cards',
                        'review_logs',
                        'generated_artifacts',
                        'knowledge_points',
                        'login_events',
                        'obsidian_settings',
                        'source_assets',
                        'user_activity_snapshots'
                      )
                    """
                )
                if known_tables:
                    completed = subprocess.run(["alembic", "-c", "alembic.ini", "stamp", "head"], check=False)
                    if completed.returncode != 0:
                        raise SystemExit(completed.returncode)
                    print(
                        "[entrypoint] detected existing schema without alembic_version; stamped current head for legacy volume",
                        file=sys.stderr,
                    )
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", lock_key)
    finally:
        await conn.close()


asyncio.run(prepare_alembic_state())
PY

python - <<'PY'
import asyncio
import os
import subprocess
import sys
from urllib.parse import urlparse


def normalize_asyncpg_dsn(raw: str) -> str:
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql://" + raw[len("postgresql+asyncpg://") :]
    return raw


async def run_locked_upgrade() -> int:
    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        completed = subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=False)
        return completed.returncode

    try:
        import asyncpg
    except Exception as exc:  # pragma: no cover - defensive startup fallback
        print(f"[entrypoint] migration lock unavailable (asyncpg import failed: {exc}); running direct upgrade", file=sys.stderr)
        completed = subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=False)
        return completed.returncode

    parsed = urlparse(normalize_asyncpg_dsn(raw_url))
    database = (parsed.path or "/").lstrip("/")
    if not database:
        print("[entrypoint] migration lock unavailable: database name missing; running direct upgrade", file=sys.stderr)
        completed = subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=False)
        return completed.returncode

    conn = await asyncpg.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=database,
    )
    try:
        lock_key = 918_274_611
        await conn.execute("SELECT pg_advisory_lock($1)", lock_key)
        try:
            completed = subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=False)
            return completed.returncode
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", lock_key)
    finally:
        await conn.close()


raise SystemExit(asyncio.run(run_locked_upgrade()))
PY

if [ "$#" -gt 0 ] && [ "$1" = "uvicorn" ]; then
  python -m app.scripts.seed_admin
fi

exec "$@"
