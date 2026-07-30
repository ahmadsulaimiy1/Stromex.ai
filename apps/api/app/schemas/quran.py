import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.quran import QuranPlanType


class QuranPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    plan_type: QuranPlanType
    surah_start: int = Field(ge=1, le=114)
    ayah_start: int = Field(ge=1)
    surah_end: int = Field(ge=1, le=114)
    ayah_end: int = Field(ge=1)
    daily_target_ayahs: int = Field(default=5, ge=1, le=200)

    @model_validator(mode="after")
    def check_range(self) -> "QuranPlanCreate":
        if (self.surah_end, self.ayah_end) < (self.surah_start, self.ayah_start):
            raise ValueError("plan range end must not precede the start")
        return self


class QuranPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    plan_type: QuranPlanType
    surah_start: int
    ayah_start: int
    surah_end: int
    ayah_end: int
    daily_target_ayahs: int
    is_active: bool
    created_at: datetime


class QuranRevisionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    surah: int
    ayah_start: int
    ayah_end: int
    ease_factor: float
    interval_days: int
    repetitions: int
    due_at: datetime
    last_reviewed_at: datetime | None
    last_grade: int | None


class QuranReviewSubmit(BaseModel):
    item_id: uuid.UUID
    grade: int = Field(ge=0, le=5, description="SM-2 recall quality: 0 (blackout) to 5 (perfect)")


class QuranAnalytics(BaseModel):
    total_items: int
    due_today: int
    average_ease_factor: float
    reviews_last_7_days: int
    reviews_last_30_days: int
    retention_rate_30_days: float | None
