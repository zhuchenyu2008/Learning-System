import pytest
from sqlalchemy import insert, select

from app.models.enums import JobStatus, JobType
from app.models.job import Job


@pytest.mark.asyncio
async def test_job_model_uses_string_backed_enums_on_sqlite(session_factory):
    async with session_factory() as session:
        await session.execute(
            insert(Job).values(
                job_type=JobType.NOTE_GENERATION,
                status=JobStatus.PENDING,
                payload_json={"source_asset_ids": [1]},
                result_json={},
                logs_json=[],
            )
        )
        await session.commit()

        result = await session.execute(select(Job))
        job = result.scalar_one()

    assert job.job_type == JobType.NOTE_GENERATION
    assert job.status == JobStatus.PENDING
