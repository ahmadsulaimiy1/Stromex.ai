import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.quran import QuranPlan, QuranReviewLog, QuranRevisionItem
from app.services.spaced_repetition import SM2State, initial_state, review


def create_plan_with_items(db: Session, *, user_id: uuid.UUID, plan_data: dict) -> QuranPlan:
    """A new plan is seeded with one revision item per ayah-range chunk, sized by
    `daily_target_ayahs`, so the very first review batch is due immediately."""
    plan = QuranPlan(user_id=user_id, **plan_data)
    db.add(plan)
    db.flush()

    chunk = plan.daily_target_ayahs
    now = datetime.now(timezone.utc)

    if plan.surah_start == plan.surah_end:
        ayah = plan.ayah_start
        while ayah <= plan.ayah_end:
            end = min(ayah + chunk - 1, plan.ayah_end)
            db.add(
                QuranRevisionItem(
                    plan_id=plan.id,
                    surah=plan.surah_start,
                    ayah_start=ayah,
                    ayah_end=end,
                    ease_factor=initial_state().ease_factor,
                    interval_days=initial_state().interval_days,
                    repetitions=initial_state().repetitions,
                    due_at=now,
                )
            )
            ayah = end + 1
    else:
        # Multi-surah ranges: one item per surah touched, in this MVP pass —
        # fine-grained per-surah chunking is a Growth-phase refinement.
        db.add(
            QuranRevisionItem(
                plan_id=plan.id,
                surah=plan.surah_start,
                ayah_start=plan.ayah_start,
                ayah_end=plan.ayah_end,
                ease_factor=initial_state().ease_factor,
                interval_days=initial_state().interval_days,
                repetitions=initial_state().repetitions,
                due_at=now,
            )
        )

    db.commit()
    db.refresh(plan)
    return plan


def submit_review(db: Session, *, item: QuranRevisionItem, grade: int) -> QuranRevisionItem:
    current_state = SM2State(
        ease_factor=item.ease_factor, interval_days=item.interval_days, repetitions=item.repetitions
    )
    result = review(current_state, grade)

    log = QuranReviewLog(
        item_id=item.id,
        grade=grade,
        interval_before=item.interval_days,
        interval_after=result.state.interval_days,
        ease_factor_after=result.state.ease_factor,
    )
    db.add(log)

    item.ease_factor = result.state.ease_factor
    item.interval_days = result.state.interval_days
    item.repetitions = result.state.repetitions
    item.due_at = result.due_at
    item.last_reviewed_at = datetime.now(timezone.utc)
    item.last_grade = grade

    db.commit()
    db.refresh(item)
    return item


def get_due_items(db: Session, *, plan_id: uuid.UUID, now: datetime | None = None) -> list[QuranRevisionItem]:
    now = now or datetime.now(timezone.utc)
    return (
        db.query(QuranRevisionItem)
        .filter(QuranRevisionItem.plan_id == plan_id, QuranRevisionItem.due_at <= now)
        .order_by(QuranRevisionItem.due_at)
        .all()
    )


def compute_analytics(db: Session, *, plan_id: uuid.UUID) -> dict:
    now = datetime.now(timezone.utc)
    items = db.query(QuranRevisionItem).filter(QuranRevisionItem.plan_id == plan_id).all()
    total_items = len(items)
    due_today = sum(1 for item in items if item.due_at <= now)
    avg_ease = (
        sum(item.ease_factor for item in items) / total_items if total_items else 0.0
    )

    item_ids = [item.id for item in items]
    if item_ids:
        since_7 = now - timedelta(days=7)
        since_30 = now - timedelta(days=30)
        reviews_7 = (
            db.query(func.count(QuranReviewLog.id))
            .filter(QuranReviewLog.item_id.in_(item_ids), QuranReviewLog.created_at >= since_7)
            .scalar()
        ) or 0
        logs_30 = (
            db.query(QuranReviewLog)
            .filter(QuranReviewLog.item_id.in_(item_ids), QuranReviewLog.created_at >= since_30)
            .all()
        )
        reviews_30 = len(logs_30)
        retention_30 = (
            sum(1 for log in logs_30 if log.grade >= 3) / reviews_30 if reviews_30 else None
        )
    else:
        reviews_7 = 0
        reviews_30 = 0
        retention_30 = None

    return {
        "total_items": total_items,
        "due_today": due_today,
        "average_ease_factor": round(avg_ease, 3),
        "reviews_last_7_days": reviews_7,
        "reviews_last_30_days": reviews_30,
        "retention_rate_30_days": round(retention_30, 3) if retention_30 is not None else None,
    }
