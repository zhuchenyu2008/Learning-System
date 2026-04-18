from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    health,
    jobs,
    mindmaps,
    notes,
    review,
    scheduler,
    settings,
    sources,
    summaries,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(review.router, prefix="/review", tags=["review"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(mindmaps.router, prefix="/mindmaps", tags=["mindmaps"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
