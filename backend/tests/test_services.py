from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.admin_entities import UserActivitySnapshot
from app.models.enums import JobType
from app.models.job import Job
from app.models.knowledge_point import KnowledgePoint
from app.models.note import Note
from app.models.review_card import ReviewCard
from app.models.review_log import ReviewLog
from app.models.user import User
from app.services.fsrs_scheduler_service import FsrsSchedulerService
from app.services.job_service import JobService
from app.services.review_service import ReviewService


@pytest.mark.asyncio
async def test_job_service_status_transitions(session_factory):
    async with session_factory() as session:
        job = await JobService.create_job(session, JobType.NOTE_GENERATION, {"source_asset_ids": [1]})
        assert job.status == "pending"
        assert any(log["message"] == "job created" for log in job.logs_json)

        job = await JobService.attach_celery_task(session, job, "celery-123")
        assert job.celery_task_id == "celery-123"
        assert job.result_json["celery_task_id"] == "celery-123"
        assert any(log["message"] == "job dispatched to celery" for log in job.logs_json)

        job = await JobService.mark_running(session, job)
        assert job.status == "running"
        assert job.started_at is not None
        assert any(log["message"] == "job running" for log in job.logs_json)

        job = await JobService.mark_completed(session, job, {"ok": True})
        assert job.status == "completed"
        assert job.result_json == {"ok": True}
        assert job.finished_at is not None
        assert any(log["message"] == "job completed" for log in job.logs_json)

        failed_job = await JobService.create_job(session, JobType.SUMMARY_GENERATION, {"scope": "manual"})
        failed_job = await JobService.mark_failed(session, failed_job, "boom")
        assert failed_job.status == "failed"
        assert failed_job.error_message == "boom"
        assert failed_job.finished_at is not None
        assert any(log["message"] == "job failed" for log in failed_job.logs_json)


@pytest.mark.asyncio
async def test_review_service_bootstrap_grade_and_activity(session_factory, workspace_root):
    note_path = workspace_root / "notes/generated/service-note.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        "# 概率论\n\n- 样本空间表示所有可能结果\n- 事件是样本空间的子集\n\n# 条件概率\n\n当已知事件 A 发生时，再看事件 B 的概率。",
        encoding="utf-8",
    )

    async with session_factory() as session:
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()
        note = Note(
            title="service-note",
            relative_path="notes/generated/service-note.md",
            note_type="source_note",
            content_hash="hash-service-note",
            source_asset_id=None,
            frontmatter_json={"generated": False},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

        bootstrap_result = await ReviewService.bootstrap_cards(session, note_ids=[note.id], all_notes=False)
        assert bootstrap_result["created_knowledge_points"] >= 2
        assert bootstrap_result["created_cards"] >= 2

        points = (await session.execute(select(KnowledgePoint).where(KnowledgePoint.note_id == note.id))).scalars().all()
        assert len(points) >= 2
        assert all(point.summary_text for point in points)
        assert all(point.source_anchor for point in points)

        cards = (await session.execute(select(ReviewCard).order_by(ReviewCard.id.asc()))).scalars().all()
        assert len(cards) >= 2

        first_card = cards[0]
        previous_due_at = first_card.due_at
        graded_card, review_log = await ReviewService.grade_card(
            session,
            card_id=first_card.id,
            rating=3,
            duration_seconds=25,
            note="理解更稳定",
            user=admin_user,
        )
        assert graded_card is not None
        assert review_log is not None
        assert graded_card.state_json["last_rating"] == 3
        assert graded_card.state_json["reps"] == 1
        assert graded_card.due_at > previous_due_at
        assert review_log.review_card_id == first_card.id

        created_log = await ReviewService.create_review_log(
            session,
            review_card_id=first_card.id,
            rating=2,
            duration_seconds=15,
            note="补充记录",
            user=admin_user,
        )
        assert created_log.review_card_id == first_card.id

        logs = await ReviewService.list_review_logs(session, limit=10)
        assert len(logs) >= 2
        assert logs[0].id >= logs[-1].id

        snapshot = (
            await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == admin_user.id))
        ).scalar_one()
        assert snapshot.review_count >= 2
        assert snapshot.review_watch_seconds >= 40
        assert snapshot.total_watch_seconds >= 40
        assert snapshot.last_event_type in {"review_grade", "review_log"}


def test_fsrs_scheduler_service_grade_variants():
    now = datetime(2026, 4, 18, tzinfo=timezone.utc)

    state_1, due_1 = FsrsSchedulerService.grade({}, rating=1, now=now)
    assert state_1["last_rating"] == 1
    assert state_1["lapses"] == 1
    assert state_1["interval_days"] == 0
    assert due_1 > now

    state_4, due_4 = FsrsSchedulerService.grade({}, rating=4, now=now)
    assert state_4["last_rating"] == 4
    assert state_4["reps"] == 1
    assert state_4["interval_days"] >= 2
    assert due_4 > now

    with pytest.raises(ValueError, match="rating must be between 1 and 4"):
        FsrsSchedulerService.grade({}, rating=0, now=now)
