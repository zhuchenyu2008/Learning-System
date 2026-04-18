from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.deps.auth import require_admin
from app.models.job import Job
from app.models.user import User
from app.schemas.ingestion import JobRead

router = APIRouter()


@router.get("")
async def list_jobs(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await session.execute(select(Job).order_by(Job.created_at.desc(), Job.id.desc()))
    jobs = [JobRead.model_validate(job).model_dump() for job in result.scalars().all()]
    return success_response(jobs)


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return success_response(JobRead.model_validate(job).model_dump())
