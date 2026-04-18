from __future__ import annotations

from datetime import datetime, timedelta, timezone


class FsrsSchedulerService:
    DEFAULT_STATE = {
        "stability": 1.0,
        "difficulty": 5.0,
        "reps": 0,
        "lapses": 0,
        "last_rating": None,
        "interval_days": 0,
    }

    @classmethod
    def initial_state(cls) -> dict:
        return dict(cls.DEFAULT_STATE)

    @classmethod
    def initial_due_at(cls) -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def grade(cls, state: dict | None, rating: int, now: datetime | None = None) -> tuple[dict, datetime]:
        current = dict(cls.DEFAULT_STATE)
        if state:
            current.update(state)

        now = now or datetime.now(timezone.utc)
        reps = int(current.get("reps", 0))
        lapses = int(current.get("lapses", 0))
        difficulty = float(current.get("difficulty", 5.0))
        stability = float(current.get("stability", 1.0))

        if rating == 1:
            lapses += 1
            reps += 1
            difficulty = min(10.0, difficulty + 0.6)
            stability = max(0.5, stability * 0.7)
            interval_days = 0
            due_at = now + timedelta(minutes=10)
        elif rating == 2:
            reps += 1
            difficulty = min(10.0, difficulty + 0.2)
            stability = stability * 1.1
            interval_days = max(1, round(stability))
            due_at = now + timedelta(days=interval_days)
        elif rating == 3:
            reps += 1
            difficulty = max(1.0, difficulty - 0.1)
            stability = stability * 1.8 + 0.5
            interval_days = max(1, round(stability * 1.5))
            due_at = now + timedelta(days=interval_days)
        elif rating == 4:
            reps += 1
            difficulty = max(1.0, difficulty - 0.3)
            stability = stability * 2.4 + 1.0
            interval_days = max(2, round(stability * 2.0))
            due_at = now + timedelta(days=interval_days)
        else:
            raise ValueError("rating must be between 1 and 4")

        next_state = {
            "stability": round(stability, 4),
            "difficulty": round(difficulty, 4),
            "reps": reps,
            "lapses": lapses,
            "last_rating": rating,
            "interval_days": interval_days,
        }
        return next_state, due_at
