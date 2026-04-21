from sqlalchemy import select

import pytest

from app.models.admin_entities import UserActivitySnapshot
from app.models.note import Note
from app.models.review_card import ReviewCard
from app.models.review_log import ReviewLog
from app.models.user import User
from app.services.review_service import ReviewService


@pytest.mark.asyncio
async def test_review_judge_endpoint_fallback_and_grade_persists_ai_metadata(client, session_factory, workspace_root, auth_headers):
    note_path = workspace_root / "notes/generated/review-judge-api.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# TCP 三次握手\n\nTCP 建立连接需要三次握手：SYN、SYN-ACK、ACK。", encoding="utf-8")

    async with session_factory() as session:
        note = Note(
            title="review-judge-api",
            relative_path="notes/generated/review-judge-api.md",
            note_type="source_note",
            content_hash="hash-review-judge-api",
            source_asset_id=None,
            frontmatter_json={"generated": False},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

    bootstrap_response = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [note.id], "all_notes": False},
        headers=auth_headers,
    )
    assert bootstrap_response.status_code == 200

    queue_response = await client.get("/api/v1/review/queue?limit=1&due_only=false", headers=auth_headers)
    assert queue_response.status_code == 200
    card_id = queue_response.json()["data"][0]["card_id"]

    judge_response = await client.post(
        f"/api/v1/review/session/{card_id}/judge",
        json={"answer": "SYN、SYN-ACK、ACK", "duration_seconds": 6},
        headers=auth_headers,
    )
    assert judge_response.status_code == 200
    judge_payload = judge_response.json()["data"]
    assert judge_payload["suggested_rating"] in {3, 4}
    assert judge_payload["judge_status"] == "fallback"
    assert judge_payload["expected_answer"]
    assert judge_payload["explanation"]

    grade_response = await client.post(
        f"/api/v1/review/session/{card_id}/grade",
        json={
            "rating": judge_payload["suggested_rating"],
            "duration_seconds": 6,
            "note": "judge fallback test",
            "answer": "SYN、SYN-ACK、ACK",
            "ai_judge": judge_payload,
        },
        headers=auth_headers,
    )
    assert grade_response.status_code == 200

    async with session_factory() as session:
        review_log = (
            await session.execute(select(ReviewLog).where(ReviewLog.review_card_id == card_id).order_by(ReviewLog.id.desc()))
        ).scalars().first()
        assert review_log is not None
        assert review_log.note is not None
        assert "answer=SYN、SYN-ACK、ACK" in review_log.note
        assert "ai_suggested_rating=" in review_log.note
        assert "ai_judge_status=fallback" in review_log.note
        assert "final_rating=" in review_log.note


@pytest.mark.asyncio
async def test_grade_card_uses_active_session_duration_when_client_reports_zero(session_factory, workspace_root):
    note_path = workspace_root / "notes/generated/review-session-service.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# Session Service Card\n\n用于验证 grade_card 会兜底使用服务端 session 时长。", encoding="utf-8")

    async with session_factory() as session:
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()
        note = Note(
            title="review-session-service",
            relative_path="notes/generated/review-session-service.md",
            note_type="source_note",
            content_hash="hash-review-session-service",
            source_asset_id=None,
            frontmatter_json={"generated": False},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

        bootstrap_result = await ReviewService.bootstrap_cards(session, note_ids=[note.id], all_notes=False)
        assert bootstrap_result["created_cards"] >= 1

        card = (
            await session.execute(
                select(ReviewCard)
                .join(ReviewCard.knowledge_point)
                .where(ReviewCard.knowledge_point.has(note_id=note.id))
                .order_by(ReviewCard.id.asc())
            )
        ).scalar_one()

        await ReviewService.start_review_session(session, card_id=card.id, user=admin_user)
        snapshot = (
            await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == admin_user.id))
        ).scalar_one()
        snapshot.active_review_session_seconds = 9
        session.add(snapshot)
        await session.commit()

        _, review_log = await ReviewService.grade_card(
            session,
            card_id=card.id,
            rating=3,
            duration_seconds=0,
            note="service fallback",
            user=admin_user,
        )

        assert review_log is not None
        assert review_log.duration_seconds >= 9

        persisted_log = (await session.execute(select(ReviewLog).where(ReviewLog.id == review_log.id))).scalar_one()
        assert persisted_log.duration_seconds >= 9

        refreshed_snapshot = (
            await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == admin_user.id))
        ).scalar_one()
        assert refreshed_snapshot.review_watch_seconds >= 9
        assert refreshed_snapshot.total_watch_seconds >= 9
        assert refreshed_snapshot.active_review_card_id is None


@pytest.mark.asyncio
async def test_review_session_endpoints_accumulate_watch_seconds(client, session_factory, workspace_root, auth_headers):
    note_path = workspace_root / "notes/generated/review-session-api.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("# Session Card\n\n用于验证 review session heartbeat/finalize。", encoding="utf-8")

    async with session_factory() as session:
        note = Note(
            title="review-session-api",
            relative_path="notes/generated/review-session-api.md",
            note_type="source_note",
            content_hash="hash-review-session-api",
            source_asset_id=None,
            frontmatter_json={"generated": False},
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)

    bootstrap_response = await client.post(
        "/api/v1/review/cards/bootstrap",
        json={"note_ids": [note.id], "all_notes": False},
        headers=auth_headers,
    )
    assert bootstrap_response.status_code == 200

    queue_response = await client.get("/api/v1/review/queue?limit=1&due_only=false", headers=auth_headers)
    assert queue_response.status_code == 200
    card_id = queue_response.json()["data"][0]["card_id"]

    start_response = await client.post(f"/api/v1/review/session/{card_id}/start", headers=auth_headers)
    assert start_response.status_code == 200
    assert start_response.json()["data"]["active_card_id"] == card_id

    async with session_factory() as session:
        admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalar_one()
        snapshot = (await session.execute(select(UserActivitySnapshot).where(UserActivitySnapshot.user_id == admin_user.id))).scalar_one()
        snapshot.active_review_session_seconds = 7
        session.add(snapshot)
        await session.commit()

    heartbeat_response = await client.post(f"/api/v1/review/session/{card_id}/heartbeat", headers=auth_headers)
    assert heartbeat_response.status_code == 200
    assert heartbeat_response.json()["data"]["accumulated_seconds"] >= 7

    finalize_response = await client.post(
        f"/api/v1/review/session/{card_id}/finalize",
        json={"duration_seconds": 11},
        headers=auth_headers,
    )
    assert finalize_response.status_code == 200
    assert finalize_response.json()["data"]["duration_seconds"] >= 11

    grade_response = await client.post(
        f"/api/v1/review/session/{card_id}/grade",
        json={"rating": 3, "duration_seconds": finalize_response.json()["data"]["duration_seconds"], "note": "api finalize"},
        headers=auth_headers,
    )
    assert grade_response.status_code == 200

    activity = await client.get("/api/v1/admin/user-activity", headers=auth_headers)
    assert activity.status_code == 200
    first = activity.json()["data"][0]
    assert first["review_watch_seconds"] >= 11
    assert first["total_watch_seconds"] >= 11
    assert first["review_count"] >= 1
