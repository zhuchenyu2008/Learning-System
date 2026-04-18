"""sa12a enrich jobs metadata and logs

Revision ID: 0005_sa12a_job_runtime_visibility
Revises: 0004_sa10_settings_admin
Create Date: 2026-04-18 10:58:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_sa12a_job_runtime_visibility"
down_revision: Union[str, None] = "0004_sa10_settings_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("logs_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.add_column("jobs", sa.Column("celery_task_id", sa.String(length=255), nullable=True))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_jobs_celery_task_id", "jobs", ["celery_task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_celery_task_id", table_name="jobs")
    op.drop_column("jobs", "finished_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("jobs", "celery_task_id")
    op.drop_column("jobs", "logs_json")
