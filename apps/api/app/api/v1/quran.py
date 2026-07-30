import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models.quran import QuranPlan, QuranRevisionItem
from app.db.models.user import User
from app.schemas.quran import (
    QuranAnalytics,
    QuranPlanCreate,
    QuranPlanRead,
    QuranRevisionItemRead,
    QuranReviewSubmit,
)
from app.services import quran_service

router = APIRouter(prefix="/quran", tags=["quran"])


def _get_owned_plan(db: Session, user: User, plan_id: uuid.UUID) -> QuranPlan:
    plan = db.get(QuranPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.post("/plans", response_model=QuranPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: QuranPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuranPlan:
    return quran_service.create_plan_with_items(db, user_id=user.id, plan_data=payload.model_dump())


@router.get("/plans", response_model=list[QuranPlanRead])
def list_plans(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[QuranPlan]:
    return (
        db.query(QuranPlan)
        .filter(QuranPlan.user_id == user.id, QuranPlan.is_active.is_(True))
        .order_by(QuranPlan.created_at.desc())
        .all()
    )


@router.get("/plans/{plan_id}/due", response_model=list[QuranRevisionItemRead])
def due_items(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[QuranRevisionItem]:
    _get_owned_plan(db, user, plan_id)
    return quran_service.get_due_items(db, plan_id=plan_id)


@router.get("/plans/{plan_id}/analytics", response_model=QuranAnalytics)
def analytics(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    _get_owned_plan(db, user, plan_id)
    return quran_service.compute_analytics(db, plan_id=plan_id)


@router.post("/review", response_model=QuranRevisionItemRead)
def submit_review(
    payload: QuranReviewSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuranRevisionItem:
    item = db.get(QuranRevisionItem, payload.item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision item not found")
    _get_owned_plan(db, user, item.plan_id)
    return quran_service.submit_review(db, item=item, grade=payload.grade)
