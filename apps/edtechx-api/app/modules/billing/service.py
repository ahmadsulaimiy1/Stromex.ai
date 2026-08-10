"""The entitlement engine: what this institution has, as distinct from what this person may do.

Seven things are routinely collapsed into one boolean, and each collapse breaks
something specific:

| Concept | Question | Where it lives |
|---|---|---|
| Identity | Who is signing in? | `identity.User` |
| Role | Who is this person here? | `authz` role grants |
| Permission | May they perform this action at all? | `authz.permissions` |
| Scope | Over which records? | `authz.predicates` |
| Entitlement | Has the institution bought this? | here |
| Feature availability | Has the institution switched it on? | here, and *not* the same question |
| Usage limit | How much may be consumed? | here, and not the same question either |

The two directions are both one-way, and neither is negotiable:

  **A permission is not an entitlement.** A registrar may be entirely entitled
  to publish AI-drafted report comments, and the school may not have bought the
  assistants. The answer is 402 and an upgrade path, not 403.

  **An entitlement is not a permission.** Buying a feature must never grant
  anybody the right to use it. A school that purchases the Design Studio has not
  thereby made its teachers able to rebrand it.

So `require` and `RequirePermission` are separate calls, and the order is
permission first. That is a deliberate departure from the order originally
written down, for two reasons that point the same way: a permission check is a
set membership test and an entitlement check is a database read, so permission
first is cheaper; and answering 402 to somebody who could never use the feature
anyway tells them what their school has and has not paid for.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.billing import catalogue
from app.modules.billing.models import (
    FeatureSetting,
    Plan,
    PlanFeature,
    PlanLimit,
    Subscription,
    SubscriptionOverride,
    SubscriptionStatus,
    UsageRecord,
)


class Verdict(str, enum.Enum):
    """Why the answer is what it is.

    Five outcomes rather than a boolean, because the product says something
    different for each and a caller that can only distinguish yes from no ends
    up saying "upgrade your plan" to somebody whose administrator switched the
    feature off.
    """

    included = "included"
    no_subscription = "no_subscription"
    not_in_plan = "not_in_plan"
    disabled_by_institution = "disabled_by_institution"
    limit_reached = "limit_reached"


@dataclass(frozen=True, slots=True)
class Entitlement:
    verdict: Verdict
    key: str
    # Populated for a limit or meter: what the ceiling is and what has been used.
    limit: float | None = None
    used: float | None = None
    plan_key: str | None = None
    reason: str | None = None

    def __bool__(self) -> bool:
        return self.verdict is Verdict.included

    @property
    def is_unlimited(self) -> bool:
        return self.limit is None

    @property
    def remaining(self) -> float | None:
        if self.limit is None:
            return None
        return max(0.0, float(self.limit) - float(self.used or 0))


# --- reading the institution's position ------------------------------------


def current_subscription(db: Session) -> Subscription | None:
    """The subscription that entitles, if there is one.

    Ordered so a school that has re-subscribed after cancelling reads from the
    live row rather than from the corpse of the old one.
    """
    return db.execute(
        select(Subscription).order_by(Subscription.created_at.desc())
    ).scalars().first()


def _plan_of(db: Session, subscription: Subscription | None) -> Plan | None:
    if subscription is None:
        return None
    return db.get(Plan, subscription.plan_id)


def _live_override(db: Session, key: str) -> SubscriptionOverride | None:
    now = datetime.now(UTC)
    rows = db.execute(
        select(SubscriptionOverride)
        .where(SubscriptionOverride.key == key)
        .order_by(SubscriptionOverride.created_at.desc())
    ).scalars().all()
    return next((row for row in rows if row.is_live(now)), None)


# --- features ---------------------------------------------------------------


def feature(db: Session, key: str) -> Entitlement:
    """Whether this institution has this capability, and why not if not.

    Four negative answers, in the order they are asked. The order matters: an
    institution that switched a feature off has *not* been told its plan is
    inadequate, and one whose plan lacks the feature is not told its
    administrator disabled it.
    """
    catalogue.validate_feature(key)
    subscription = current_subscription(db)
    plan = _plan_of(db, subscription)
    plan_key = plan.key if plan else None

    override = _live_override(db, key)
    if override is not None and override.enabled is not None:
        allowed_by_plan = override.enabled
        source_reason = override.reason
    else:
        source_reason = None
        if subscription is None or not subscription.status.entitles:
            return Entitlement(
                Verdict.no_subscription, key, plan_key=plan_key,
                reason="This institution has no active subscription.",
            )
        row = db.execute(
            select(PlanFeature).where(
                PlanFeature.plan_id == subscription.plan_id,
                PlanFeature.feature_key == key,
            )
        ).scalars().first()
        allowed_by_plan = bool(row and row.enabled)

    if not allowed_by_plan:
        return Entitlement(
            Verdict.not_in_plan, key, plan_key=plan_key,
            reason=source_reason or f"{plan_key or 'This plan'} does not include this.",
        )

    # Only now the institution's own choice. Asked last so that "you turned this
    # off" is never said about something the institution could not have had.
    setting = db.execute(
        select(FeatureSetting).where(FeatureSetting.feature_key == key)
    ).scalars().first()
    if setting is not None and not setting.enabled:
        return Entitlement(
            Verdict.disabled_by_institution, key, plan_key=plan_key,
            reason=setting.note or "An administrator has switched this off.",
        )

    return Entitlement(Verdict.included, key, plan_key=plan_key)


def set_feature_enabled(
    db: Session,
    key: str,
    *,
    enabled: bool,
    membership_id: uuid.UUID | None = None,
    note: str | None = None,
) -> FeatureSetting:
    """An institution switching one of its own capabilities on or off.

    Can only ever *disable* something the plan includes; it cannot enable
    something the plan does not. That asymmetry is the whole reason this table
    is separate from the plan — putting the enabling side inside the tenant
    would move the entitlement boundary inside it too.
    """
    catalogue.validate_feature(key)
    setting = db.execute(
        select(FeatureSetting).where(FeatureSetting.feature_key == key)
    ).scalars().first()
    if setting is None:
        setting = FeatureSetting(feature_key=key, enabled=enabled, note=note)
        db.add(setting)
    else:
        setting.enabled = enabled
        setting.note = note
    setting.changed_by_membership_id = membership_id
    db.flush()
    return setting


# --- limits and meters ------------------------------------------------------


def limit_for(db: Session, key: str) -> float | None:
    """The ceiling, or `None` for unlimited.

    `None` and `0` are different answers and always have been: unlimited, and
    none at all. A sentinel number for "unlimited" is a number some school
    eventually reaches.
    """
    if key not in catalogue.LIMITS and key not in catalogue.METERS:
        raise catalogue.UnknownLimit(f"{key!r} is not a limit or a meter")

    override = _live_override(db, key)
    if override is not None and (override.value is not None or override.is_unlimited):
        return None if override.is_unlimited else float(override.value)

    subscription = current_subscription(db)
    if subscription is None:
        return 0.0
    row = db.execute(
        select(PlanLimit).where(
            PlanLimit.plan_id == subscription.plan_id, PlanLimit.limit_key == key
        )
    ).scalars().first()
    if row is None:
        # A limit the plan says nothing about is zero, not unlimited. Silence is
        # not generosity: a plan that forgot to mention a meter must not hand
        # out an uncapped one.
        return 0.0
    return None if row.value is None else float(row.value)


def usage(db: Session, meter: str, *, since: datetime | None = None) -> float:
    """What has been consumed this period. Summed, not counted from a total."""
    catalogue.validate_meter(meter)
    statement = select(func.coalesce(func.sum(UsageRecord.quantity), 0)).where(
        UsageRecord.meter_key == meter
    )
    if since is not None:
        statement = statement.where(UsageRecord.period_start >= since)
    else:
        subscription = current_subscription(db)
        if subscription is not None and subscription.current_period_start is not None:
            statement = statement.where(
                UsageRecord.period_start >= subscription.current_period_start
            )
    return float(db.execute(statement).scalar_one())


def check_meter(db: Session, meter: str, *, additional: float = 0.0) -> Entitlement:
    """Whether this much more may be consumed."""
    ceiling = limit_for(db, meter)
    spent = usage(db, meter)
    if ceiling is None:
        return Entitlement(Verdict.included, meter, limit=None, used=spent)
    if spent + additional > ceiling:
        return Entitlement(
            Verdict.limit_reached, meter, limit=ceiling, used=spent,
            reason=f"{spent:g} of {ceiling:g} used for this period.",
        )
    return Entitlement(Verdict.included, meter, limit=ceiling, used=spent)


def check_limit(db: Session, key: str, *, current: float) -> Entitlement:
    """Whether a standing quantity is within its ceiling.

    Takes the current count rather than measuring it, because *what* counts as
    an active student is the caller's question, not billing's — and billing
    reaching into `people` to decide would be exactly the coupling the module
    boundaries exist to prevent.
    """
    ceiling = limit_for(db, key)
    if ceiling is None:
        return Entitlement(Verdict.included, key, limit=None, used=current)
    if current > ceiling:
        return Entitlement(
            Verdict.limit_reached, key, limit=ceiling, used=current,
            reason=f"{current:g} of {ceiling:g} allowed.",
        )
    return Entitlement(Verdict.included, key, limit=ceiling, used=current)


def record_usage(
    db: Session,
    meter: str,
    quantity: float,
    *,
    membership_id: uuid.UUID | None = None,
    feature_key: str | None = None,
    **detail: object,
) -> UsageRecord:
    """Record consumption. Deliberately does **not** check the ceiling.

    Recording and permitting are separate calls because they answer different
    questions at different moments: a caller asks `check_meter` *before* doing
    the expensive thing and records *after* it succeeded. Merging them would
    either bill for work that failed or refuse work already done.
    """
    catalogue.validate_meter(meter)
    subscription = current_subscription(db)
    now = datetime.now(UTC)
    record = UsageRecord(
        meter_key=meter,
        quantity=quantity,
        period_start=(subscription.current_period_start if subscription else None) or now,
        period_end=(subscription.current_period_end if subscription else None) or now,
        membership_id=membership_id,
        feature_key=feature_key,
        detail={k: str(v) for k, v in detail.items()},
    )
    db.add(record)
    db.flush()
    return record


# --- raising, for the request path -----------------------------------------


def require(db: Session, key: str) -> Entitlement:
    """Assert a feature, or raise the error that says why not.

    Three different exceptions for three different sentences. A caller that
    could only raise one would tell a teacher to upgrade a plan when their own
    administrator had switched the feature off.
    """
    from app.core import errors

    result = feature(db, key)
    if result:
        return result
    if result.verdict is Verdict.disabled_by_institution:
        raise errors.FeatureDisabled(key, result.reason)
    raise errors.EntitlementRequired(key, result.reason)


def require_meter(db: Session, meter: str, *, additional: float = 0.0) -> Entitlement:
    from app.core import errors

    result = check_meter(db, meter, additional=additional)
    if result:
        return result
    raise errors.QuotaExceeded(meter, result.reason)


# --- seeding ----------------------------------------------------------------


def seed_plans(db: Session, definitions: dict[str, dict]) -> int:
    """Create or update the platform's plans from a definition.

    Idempotent, and validating: a plan naming a feature outside the catalogue
    fails here rather than producing a subscription that entitles nothing.
    """
    created = 0
    for key, definition in definitions.items():
        plan = db.execute(select(Plan).where(Plan.key == key)).scalars().first()
        if plan is None:
            plan = Plan(
                key=key,
                name=definition["name"],
                tier=definition.get("tier", 0),
                description=definition.get("description"),
                is_public=definition.get("is_public", True),
            )
            db.add(plan)
            db.flush()
            created += 1
        existing_features = {f.feature_key: f for f in plan.features}
        for feature_key in definition.get("features", ()):
            catalogue.validate_feature(feature_key)
            if feature_key in existing_features:
                existing_features[feature_key].enabled = True
            else:
                db.add(
                    PlanFeature(plan_id=plan.id, feature_key=feature_key, enabled=True)
                )
        existing_limits = {limit.limit_key: limit for limit in plan.limits}
        for limit_key, value in definition.get("limits", {}).items():
            if limit_key not in catalogue.LIMITS and limit_key not in catalogue.METERS:
                raise catalogue.UnknownLimit(f"{limit_key!r} is not a limit or meter")
            if limit_key in existing_limits:
                existing_limits[limit_key].value = value
            else:
                db.add(PlanLimit(plan_id=plan.id, limit_key=limit_key, value=value))
        db.flush()
    return created


def subscribe(
    db: Session,
    *,
    plan_key: str,
    status: SubscriptionStatus = SubscriptionStatus.active,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> Subscription:
    plan = db.execute(select(Plan).where(Plan.key == plan_key)).scalars().first()
    if plan is None:
        raise LookupError(f"No plan {plan_key!r}")
    subscription = Subscription(
        plan_id=plan.id,
        status=status,
        current_period_start=period_start or datetime.now(UTC),
        current_period_end=period_end,
    )
    db.add(subscription)
    db.flush()
    return subscription


def grant_override(
    db: Session,
    *,
    key: str,
    reason: str,
    enabled: bool | None = None,
    value: float | None = None,
    is_unlimited: bool = False,
    expires_at: datetime | None = None,
    granted_by_user_id: uuid.UUID | None = None,
) -> SubscriptionOverride:
    if not reason or not reason.strip():
        raise ValueError(
            "An override needs a reason. A grant nobody can explain becomes "
            "permanent by accident."
        )
    override = SubscriptionOverride(
        key=key,
        enabled=enabled,
        value=value,
        is_unlimited=is_unlimited,
        reason=reason.strip(),
        expires_at=expires_at,
        granted_by_user_id=granted_by_user_id,
    )
    db.add(override)
    db.flush()
    return override
