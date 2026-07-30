from datetime import datetime, timezone

from app.services.spaced_repetition import SM2State, initial_state, review


def test_initial_state_defaults():
    state = initial_state()
    assert state.ease_factor == 2.5
    assert state.interval_days == 0
    assert state.repetitions == 0


def test_perfect_recall_sequence_grows_interval_geometrically():
    state = initial_state()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    r1 = review(state, 5, now=now)
    assert r1.state.interval_days == 1
    assert r1.state.repetitions == 1

    r2 = review(r1.state, 5, now=now)
    assert r2.state.interval_days == 6
    assert r2.state.repetitions == 2

    r3 = review(r2.state, 5, now=now)
    # interval = round(previous_interval * ease_factor)
    assert r3.state.interval_days == round(6 * r2.state.ease_factor)
    assert r3.state.repetitions == 3
    assert (r3.due_at - now).days == r3.state.interval_days


def test_failed_recall_resets_repetitions_and_interval():
    state = SM2State(ease_factor=2.8, interval_days=30, repetitions=4)
    result = review(state, 1)
    assert result.state.repetitions == 0
    assert result.state.interval_days == 1
    # ease factor still decreases on a failed review (SM-2 penalizes low quality
    # even when it resets the repetition counter)
    assert result.state.ease_factor < state.ease_factor


def test_ease_factor_never_drops_below_minimum():
    state = SM2State(ease_factor=1.3, interval_days=10, repetitions=3)
    result = review(state, 0)
    assert result.state.ease_factor >= 1.3


def test_due_at_is_now_plus_interval_days():
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    state = initial_state()
    result = review(state, 4, now=now)
    assert (result.due_at - now).days == result.state.interval_days


def test_quality_out_of_range_rejected():
    import pytest

    with pytest.raises(ValueError):
        review(initial_state(), 6)
    with pytest.raises(ValueError):
        review(initial_state(), -1)
