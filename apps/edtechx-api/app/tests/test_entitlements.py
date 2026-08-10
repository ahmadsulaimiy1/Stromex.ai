"""Entitlement, and the seven things it must not be confused with.

The brief names them: permission ≠ role ≠ scope ≠ entitlement ≠ plan ≠ feature
≠ usage limit. Most of this suite is about the two directions that must both
hold, and that a single boolean cannot express:

  a person may be entitled to do something their institution has not bought;
  an institution may buy something no person is permitted to use.

The rest is about the third answer nobody builds — the institution switched it
off — and about the difference between a limit (a standing quantity) and a meter
(a rate over a period), which look alike and behave differently.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core import errors
from app.modules.billing import catalogue
from app.modules.billing import service as billing
from app.modules.billing.models import SubscriptionStatus
from app.modules.billing.plans import PLANS
from app.tests.conftest import TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db


@pytest.fixture(scope="module")
def platform() -> None:
    """Seed the plans once. They are platform rows, not a school's."""
    from app.db.session import bind_tenant, get_session_factory

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        billing.seed_plans(session, PLANS)
        session.commit()
    finally:
        session.close()


@pytest.fixture
def free_school(platform: None) -> TenantFixture:
    school = _provision("plan-free")
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.free")
        session.commit()
    finally:
        session.close()
    return school


@pytest.fixture
def paid_school(platform: None) -> TenantFixture:
    school = _provision("plan-institution")
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")
        session.commit()
    finally:
        session.close()
    return school


# --- the catalogue ----------------------------------------------------------


def test_the_three_vocabularies_do_not_overlap() -> None:
    """A key that is both a feature and a limit is answerable two ways."""
    catalogue.validate_catalogue()


def test_a_plan_naming_something_outside_the_catalogue_is_refused(
    platform: None, free_school: TenantFixture
) -> None:
    """Fails when the plan is written, not when a school hits the feature."""
    session = free_school.session()
    try:
        with pytest.raises(catalogue.UnknownFeature):
            billing.seed_plans(
                session, {"broken": {"name": "Broken", "features": ("no.such.thing",)}}
            )
        with pytest.raises(catalogue.UnknownLimit):
            billing.seed_plans(
                session, {"broken2": {"name": "Broken", "limits": {"no.such.limit": 1}}}
            )
    finally:
        session.rollback()
        session.close()


def test_every_plan_in_the_definition_validates(platform: None) -> None:
    for definition in PLANS.values():
        for feature in definition.get("features", ()):
            catalogue.validate_feature(feature)
        for key in definition.get("limits", {}):
            assert key in catalogue.LIMITS or key in catalogue.METERS


# --- the two one-way rules --------------------------------------------------


def test_a_permission_is_not_an_entitlement(free_school: TenantFixture) -> None:
    """The owner may do everything. The school has not bought the studios."""
    session = free_school.session()
    try:
        assert not billing.feature(session, "customization.ai_design_studio")
        with pytest.raises(errors.EntitlementRequired) as caught:
            billing.require(session, "customization.ai_design_studio")
        assert caught.value.status_code == 402, "an unbought feature is not a 403"
    finally:
        session.close()


def test_an_entitlement_is_not_a_permission(paid_school: TenantFixture) -> None:
    """Buying the Design Studio does not make a teacher able to rebrand.

    The two checks are separate calls over separate state: the entitlement is
    satisfied and the permission is absent, and the entitlement engine has no
    opinion about the second — which is exactly right.
    """
    from app.modules.authz import permissions as perms
    from app.modules.authz.system_roles import SYSTEM_ROLES_BY_KEY

    session = paid_school.session()
    try:
        assert billing.feature(session, "customization.design_studio")
    finally:
        session.close()

    teacher = perms.expand(set(SYSTEM_ROLES_BY_KEY["teacher"].permissions))
    assert "customization.theme.publish" not in teacher
    assert "customization.theme.write" not in teacher


# --- four different negative answers ---------------------------------------


def test_a_school_with_no_subscription_is_told_so(platform: None) -> None:
    """Distinct from "your plan does not include it": there is no plan."""
    school = _provision("plan-none")
    session = school.session()
    try:
        result = billing.feature(session, "core.attendance")
        assert result.verdict is billing.Verdict.no_subscription
        assert not result
    finally:
        session.close()


def test_switching_a_feature_off_is_not_the_same_as_not_owning_it(
    paid_school: TenantFixture
) -> None:
    """The third answer, and the one that sends a teacher to the right person.

    "Your plan does not include this, here is how to upgrade" and "an
    administrator switched this off" are different sentences said to different
    people. A system with one boolean says the first when the second is true.
    """
    session = paid_school.session()
    try:
        assert billing.feature(session, "intelligence.assistants")
        billing.set_feature_enabled(
            session, "intelligence.assistants", enabled=False,
            note="Under review by the governors.",
        )
        session.commit()

        result = billing.feature(session, "intelligence.assistants")
        assert result.verdict is billing.Verdict.disabled_by_institution
        assert "governors" in (result.reason or "")

        with pytest.raises(errors.FeatureDisabled) as caught:
            billing.require(session, "intelligence.assistants")
        assert caught.value.status_code == 403, (
            "a school was told to upgrade a plan it already pays for"
        )
    finally:
        session.close()


def test_an_institution_cannot_switch_on_what_it_has_not_bought(
    free_school: TenantFixture
) -> None:
    """The asymmetry that keeps the entitlement boundary outside the tenant."""
    session = free_school.session()
    try:
        billing.set_feature_enabled(
            session, "customization.white_label", enabled=True, note="We would like this"
        )
        session.commit()
        result = billing.feature(session, "customization.white_label")
        assert result.verdict is billing.Verdict.not_in_plan, (
            "a school enabled a feature its plan does not include"
        )
    finally:
        session.close()


def test_the_reason_for_refusal_is_asked_in_the_right_order(
    free_school: TenantFixture
) -> None:
    """A school is never told it disabled something it could not have had."""
    session = free_school.session()
    try:
        billing.set_feature_enabled(
            session, "operations.sso", enabled=False, note="not wanted"
        )
        session.commit()
        assert (
            billing.feature(session, "operations.sso").verdict
            is billing.Verdict.not_in_plan
        )
    finally:
        session.close()


# --- limits and meters are different things --------------------------------


def test_unlimited_and_none_are_different_answers(
    free_school: TenantFixture, paid_school: TenantFixture
) -> None:
    """`None` is unlimited; `0` is genuinely none. A sentinel would confuse them."""
    free = free_school.session()
    paid = paid_school.session()
    try:
        assert billing.limit_for(free, "students.active") == 150
        assert billing.limit_for(free, "ai.tokens") == 0
        assert billing.limit_for(paid, "students.active") is None
        assert billing.limit_for(paid, "ai.tokens") == 20_000_000
    finally:
        free.close()
        paid.close()


def test_a_limit_the_plan_never_mentions_is_zero_not_unlimited(
    platform: None
) -> None:
    """Silence is not generosity.

    A plan that forgot to mention a meter must not hand out an uncapped one —
    which is the failure mode of every entitlement system that defaults to
    "allow" when it finds no row.
    """
    school = _provision("plan-silent")
    session = school.session()
    try:
        billing.seed_plans(
            session, {"plan.silent": {"name": "Silent", "tier": 1, "features": ()}}
        )
        billing.subscribe(session, plan_key="plan.silent")
        session.commit()
        assert billing.limit_for(session, "ai.tokens") == 0
        assert not billing.check_meter(session, "ai.tokens", additional=1)
    finally:
        session.close()


def test_a_standing_quantity_over_its_limit_does_not_lock_the_school_out(
    free_school: TenantFixture
) -> None:
    """Being over a limit is a state; it must not be a refusal of everything.

    A school with 400 students on a 150 plan is over its limit and must still be
    able to take a register. `check_limit` reports the position; what to do about
    it is a commercial workflow, not an authorization decision.
    """
    session = free_school.session()
    try:
        over = billing.check_limit(session, "students.active", current=400)
        assert over.verdict is billing.Verdict.limit_reached
        assert over.limit == 150 and over.used == 400
        # And the core feature is untouched by it.
        assert billing.feature(session, "core.attendance")
    finally:
        session.close()


def test_a_meter_is_spent_and_then_refuses(paid_school: TenantFixture) -> None:
    session = paid_school.session()
    try:
        billing.grant_override(
            session, key="ai.requests", value=10, reason="test ceiling"
        )
        session.commit()

        assert billing.check_meter(session, "ai.requests", additional=1)
        for _ in range(10):
            billing.record_usage(session, "ai.requests", 1)
        session.commit()

        assert billing.usage(session, "ai.requests") == 10
        spent = billing.check_meter(session, "ai.requests", additional=1)
        assert spent.verdict is billing.Verdict.limit_reached
        assert spent.remaining == 0
        with pytest.raises(errors.QuotaExceeded) as caught:
            billing.require_meter(session, "ai.requests", additional=1)
        assert caught.value.status_code == 429, (
            "a spent period allowance is not a 402 — it resolves on its own"
        )
    finally:
        session.close()


def test_recording_usage_does_not_itself_refuse(paid_school: TenantFixture) -> None:
    """Asking and recording are separate moments.

    A caller checks before doing the expensive thing and records after it
    succeeded. Merging them would either bill for work that failed or refuse
    work already done.
    """
    session = paid_school.session()
    try:
        billing.grant_override(
            session, key="documents.rendered", value=1, reason="test ceiling"
        )
        billing.record_usage(session, "documents.rendered", 5)
        session.commit()
        assert billing.usage(session, "documents.rendered") == 5
        assert not billing.check_meter(session, "documents.rendered")
    finally:
        session.close()


def test_usage_is_summed_from_records_rather_than_from_a_counter(
    paid_school: TenantFixture
) -> None:
    """When a school disputes its bill, the answer has to be a list."""
    from sqlalchemy import select

    from app.modules.billing.models import UsageRecord

    session = paid_school.session()
    try:
        membership = _uuid.uuid4()
        billing.record_usage(
            session, "ai.tokens", 1200, membership_id=membership,
            feature_key="intelligence.assistants", model="a-model",
        )
        billing.record_usage(session, "ai.tokens", 800, membership_id=membership)
        session.commit()
        rows = session.execute(
            select(UsageRecord).where(UsageRecord.meter_key == "ai.tokens")
        ).scalars().all()
        assert len(rows) == 2
        assert billing.usage(session, "ai.tokens") == 2000
        assert rows[0].detail["model"] == "a-model"
    finally:
        session.close()


# --- overrides --------------------------------------------------------------


def test_an_override_grants_beyond_the_plan_and_says_why(
    free_school: TenantFixture
) -> None:
    session = free_school.session()
    try:
        assert not billing.feature(session, "operations.sso")
        billing.grant_override(
            session, key="operations.sso", enabled=True,
            reason="Pilot agreement, signed 12 May",
        )
        session.commit()
        result = billing.feature(session, "operations.sso")
        assert result
        assert result.verdict is billing.Verdict.included
    finally:
        session.close()


def test_an_expired_override_stops_granting(free_school: TenantFixture) -> None:
    """A grant nobody revisits becomes permanent by accident. This one does not."""
    session = free_school.session()
    try:
        billing.grant_override(
            session, key="learning.quizzes", enabled=True, reason="Trial",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        session.commit()
        assert not billing.feature(session, "learning.quizzes")
    finally:
        session.close()


def test_an_override_can_raise_a_ceiling_or_remove_it(
    free_school: TenantFixture
) -> None:
    session = free_school.session()
    try:
        billing.grant_override(
            session, key="students.active", value=500, reason="Migration in progress"
        )
        session.commit()
        assert billing.limit_for(session, "students.active") == 500

        billing.grant_override(
            session, key="students.active", is_unlimited=True,
            reason="Negotiated contract",
        )
        session.commit()
        assert billing.limit_for(session, "students.active") is None
    finally:
        session.close()


def test_an_override_without_a_reason_is_refused(free_school: TenantFixture) -> None:
    session = free_school.session()
    try:
        with pytest.raises(ValueError):
            billing.grant_override(session, key="operations.sso", enabled=True, reason=" ")
    finally:
        session.rollback()
        session.close()


# --- subscription states ----------------------------------------------------


def test_an_overdue_school_keeps_its_register(platform: None) -> None:
    """A card that expired must not lose a school the register on Monday.

    Dunning is a commercial workflow. Solving it by withholding a child's
    attendance record would be indefensible, so `past_due` still entitles.
    """
    school = _provision("plan-overdue")
    session = school.session()
    try:
        billing.subscribe(
            session, plan_key="plan.standard", status=SubscriptionStatus.past_due
        )
        session.commit()
        assert billing.feature(session, "core.attendance")
    finally:
        session.close()


def test_a_cancelled_subscription_entitles_nothing(platform: None) -> None:
    school = _provision("plan-cancelled")
    session = school.session()
    try:
        billing.subscribe(
            session, plan_key="plan.standard", status=SubscriptionStatus.canceled
        )
        session.commit()
        assert (
            billing.feature(session, "core.attendance").verdict
            is billing.Verdict.no_subscription
        )
    finally:
        session.close()


def test_free_is_genuinely_useful(free_school: TenantFixture) -> None:
    """A crippled free tier teaches a school that the product is poor.

    Every core operation is on it. What Free caps is scale, AI and
    customization depth — never the ability to run the school.
    """
    session = free_school.session()
    try:
        for capability in (
            "core.attendance", "core.assessment", "core.report_cards",
            "core.announcements", "core.bulk_import",
        ):
            assert billing.feature(session, capability), capability
    finally:
        session.close()


# --- isolation --------------------------------------------------------------


def test_one_schools_plan_does_not_entitle_another(
    free_school: TenantFixture, paid_school: TenantFixture
) -> None:
    free = free_school.session()
    paid = paid_school.session()
    try:
        assert billing.feature(paid, "customization.white_label")
        assert not billing.feature(free, "customization.white_label")
    finally:
        free.close()
        paid.close()


def test_an_override_does_not_cross_institutions(
    free_school: TenantFixture, platform: None
) -> None:
    """Overrides are tenant-owned, so row-level security carries the boundary."""
    other = _provision("plan-other-free")
    session = other.session()
    try:
        billing.subscribe(session, plan_key="plan.free")
        session.commit()
    finally:
        session.close()

    granting = free_school.session()
    try:
        billing.grant_override(
            granting, key="operations.sso", enabled=True, reason="Only this school"
        )
        granting.commit()
    finally:
        granting.close()

    stranger = other.session()
    try:
        assert not billing.feature(stranger, "operations.sso"), (
            "an override granted to one school entitled another"
        )
    finally:
        stranger.close()


def test_a_school_cannot_write_to_a_plan(free_school: TenantFixture) -> None:
    """Plans are platform rows. A school editing its own plan edits its own bill.

    Asserted structurally: `plans` is not tenant-owned, so it carries no policy
    — which means the protection is that no tenant-facing code path writes to
    it, and this test names that as the rule rather than leaving it to habit.
    """
    from app.db.base import TENANT_OWNED_MODELS
    from app.modules.billing.models import Plan, PlanFeature, PlanLimit

    owned = {model.__tablename__ for model in TENANT_OWNED_MODELS}
    for model in (Plan, PlanFeature, PlanLimit):
        assert model.__tablename__ not in owned, (
            f"{model.__tablename__} became tenant-owned, which would let a "
            "school hold its own copy of a plan"
        )
    for model in ("subscriptions", "subscription_overrides", "feature_settings",
                  "usage_records"):
        assert model in owned, f"{model} must be tenant-owned"


# --- through HTTP -----------------------------------------------------------


def test_the_route_dependency_answers_402_403_and_200(
    free_school: TenantFixture, paid_school: TenantFixture
) -> None:
    """One dependency, three answers, each sending the reader somewhere different."""
    from app.api.deps import RequireEntitlement

    for school, expected in (
        (paid_school, 200),
        (free_school, 402),
    ):
        session = school.session()
        try:
            dependency = RequireEntitlement("customization.design_studio")
            if expected == 200:
                dependency(session)
            else:
                with pytest.raises(errors.EntitlementRequired) as caught:
                    dependency(session)
                assert caught.value.status_code == 402
        finally:
            session.close()

    session = paid_school.session()
    try:
        billing.set_feature_enabled(
            session, "customization.design_studio", enabled=False, note="Off for now"
        )
        session.commit()
        with pytest.raises(errors.FeatureDisabled) as caught:
            RequireEntitlement("customization.design_studio")(session)
        assert caught.value.status_code == 403
    finally:
        session.close()


def test_a_route_naming_an_unknown_feature_fails_at_import(
    free_school: TenantFixture
) -> None:
    """A typo fails the boot, not a request on results day."""
    from app.api.deps import RequireEntitlement

    with pytest.raises(catalogue.UnknownFeature):
        RequireEntitlement("customization.ai_design_studioo")


def test_the_error_bodies_say_something_different(
    free_school: TenantFixture, paid_school: TenantFixture
) -> None:
    """Three codes, because the reader is three different people.

    Upgrade the plan (the person who signs cheques), ask your administrator (the
    person down the corridor), and wait for the period to roll (nobody).
    """
    assert errors.EntitlementRequired("x").to_body()["error"]["code"] == (
        "entitlement_required"
    )
    assert errors.FeatureDisabled("x").to_body()["error"]["code"] == "feature_disabled"
    assert errors.QuotaExceeded("x").to_body()["error"]["code"] == "quota_exceeded"
    assert (
        len(
            {
                errors.EntitlementRequired("x").status_code,
                errors.FeatureDisabled("x").status_code,
                errors.QuotaExceeded("x").status_code,
            }
        )
        == 3
    ), "two of the three answers are indistinguishable to a client"


def test_no_plan_name_appears_outside_the_billing_module() -> None:
    """`EDTECHX_BILLING.md` §1: a grep for a plan name elsewhere is a defect."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        if "tests" in path.parts or "billing" in path.parts:
            continue
        text = path.read_text().lower()
        # Exact, because a plan key is prefixed `plan.` and nothing else is.
        # An approximate check flagged the `institution.*` permission module and
        # would have been deleted rather than obeyed.
        for name in ('"plan.', "'plan.", "plan_key="):
            if name in text:
                offenders.append(f"{path.relative_to(root)}: {name}")
    assert not offenders, (
        "A plan name or plan key appears outside the billing module:\n"
        + "\n".join(offenders)
    )
