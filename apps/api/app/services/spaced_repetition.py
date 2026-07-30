"""SM-2 spaced-repetition scheduling (SuperMemo 2, Wozniak 1987), applied to
Qur'an revision items. Pure functions — no I/O — so the algorithm itself is
exhaustively unit-testable independent of the database.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MIN_EASE_FACTOR = 1.3


@dataclass(frozen=True, slots=True)
class SM2State:
    ease_factor: float
    interval_days: int
    repetitions: int


@dataclass(frozen=True, slots=True)
class SM2Result:
    state: SM2State
    due_at: datetime


def review(state: SM2State, quality: int, *, now: datetime | None = None) -> SM2Result:
    """Apply one SM-2 review step.

    `quality` is the recall grade from 0 (complete blackout) to 5 (perfect
    recall). A quality below 3 resets the item to the beginning of the
    learning sequence — the ayah range was not actually retained and must be
    re-drilled from scratch, which is the entire point of spaced repetition:
    it schedules around real forgetting, not around wishful completion.
    """
    if not 0 <= quality <= 5:
        raise ValueError("quality must be between 0 and 5 inclusive")

    now = now or datetime.now(timezone.utc)

    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = state.repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = round(state.interval_days * state.ease_factor)

    ease_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    new_ease_factor = max(MIN_EASE_FACTOR, state.ease_factor + ease_delta)

    new_state = SM2State(
        ease_factor=round(new_ease_factor, 4),
        interval_days=max(1, new_interval),
        repetitions=new_repetitions,
    )
    due_at = now + timedelta(days=new_state.interval_days)
    return SM2Result(state=new_state, due_at=due_at)


def initial_state() -> SM2State:
    return SM2State(ease_factor=2.5, interval_days=0, repetitions=0)
