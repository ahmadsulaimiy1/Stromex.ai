"""Journey 1: a teacher marks a register.

Two standards are being held at once here, and they pull in opposite
directions. The register has to be *fast* — a teacher with a room in front of
them, on a phone, marking thirty children — and it has to be *evidence*, because
an attendance record is quoted in safeguarding referrals, exclusion appeals and
funding audits years later.

So the suite tests speed as a property of the design (how many calls a full
register takes) and integrity as a property of the database (what happens to the
ledger when a mark changes), and refuses to trade either for the other.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.core.context import Grant, Principal
from app.core.security import hash_password
from app.main import app
from app.modules.academics.models import (
    AcademicYear,
    ClassGroup,
    Level,
    TeachingAllocation,
)
from app.modules.attendance import scopes as attendance_scopes
from app.modules.attendance import service as attendance
from app.modules.attendance.models import (
    AttendanceMark,
    AttendanceSession,
    MarkCategory,
    SessionStatus,
)
from app.modules.authz import service as authz
from app.modules.authz.predicates import scoped_count, scoped_select
from app.modules.authz.scopes import Scope, ScopeKind
from app.modules.billing import service as billing
from app.modules.billing.plans import PLANS
from app.modules.people import service as people
from app.modules.people.service import Placement
from app.tests.conftest import OWNER_PASSWORD, TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db

TODAY = date(2026, 9, 14)


@pytest.fixture(scope="module")
def platform() -> None:
    from app.db.session import bind_tenant, get_session_factory

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        billing.seed_plans(session, PLANS)
        session.commit()
    finally:
        session.close()


class School:
    def __init__(self, fixture: TenantFixture, **ids: object) -> None:
        self.fixture = fixture
        self.__dict__.update(ids)

    def session(self):
        return self.fixture.session()


@pytest.fixture(scope="module")
def school(platform: None) -> School:
    """A school with one class of four children and a teacher allocated to it."""
    from app.modules.academics.models import AcademicStage
    from app.modules.identity.models import (
        Membership,
        MembershipStatus,
        User,
        UserStatus,
    )

    fixture = _provision("register-school")
    session = fixture.session()
    try:
        billing.subscribe(session, plan_key="plan.standard")
        attendance.seed_codes(session)

        stage = AcademicStage(code="lower", name="Lower", sequence=0)
        session.add(stage)
        session.flush()
        level = Level(code="y3", name="Year 3", sequence=0, stage_id=stage.id)
        session.add(level)
        session.flush()
        year = AcademicYear(name="2026", code="2026", starts_on=date(2026, 9, 1),
                            ends_on=date(2027, 7, 31), is_current=True)
        session.add(year)
        session.flush()
        group = ClassGroup(code="3a", name="3A", level_id=level.id,
                           academic_year_id=year.id)
        other = ClassGroup(code="3b", name="3B", level_id=level.id,
                           academic_year_id=year.id)
        session.add_all([group, other])
        session.flush()

        students: dict[str, _uuid.UUID] = {}
        for name in ("Amara Diallo", "Ben Whitfield", "Chen Wei", "Dara O'Neill"):
            person = people.record_person(session, full_name=name)
            student = people.register_student(session, person, reference=f"R-{name[:3]}")
            placement = people.admit(
                session, student, on=date(2026, 9, 1),
                placement=Placement(academic_year_id=year.id, level_id=level.id,
                                    class_group_id=group.id),
            )
            people.enrol(session, placement, on=date(2026, 9, 1))
            students[name] = student.id

        # One child in the other class, so a scope has something to exclude.
        elsewhere_person = people.record_person(session, full_name="Elsewhere Child")
        elsewhere = people.register_student(session, elsewhere_person, reference="R-Els")
        placement = people.admit(
            session, elsewhere, on=date(2026, 9, 1),
            placement=Placement(academic_year_id=year.id, level_id=level.id,
                                class_group_id=other.id),
        )
        people.enrol(session, placement, on=date(2026, 9, 1))
        students["Elsewhere Child"] = elsewhere.id

        teacher_user = User(
            email=f"teacher-{_uuid.uuid4().hex[:6]}@register.test",
            full_name="A Teacher", status=UserStatus.active,
            password_hash=hash_password(OWNER_PASSWORD),
        )
        session.add(teacher_user)
        session.flush()
        teacher_membership = Membership(
            user_id=teacher_user.id, status=MembershipStatus.active,
            display_name="A Teacher",
        )
        session.add(teacher_membership)
        session.flush()
        authz.grant_role(
            session, membership_id=teacher_membership.id, role_key="teacher",
            scope=Scope(ScopeKind.taught_by_self),
        )
        session.add(
            TeachingAllocation(
                membership_id=teacher_membership.id, class_group_id=group.id
            )
        )
        session.commit()

        return School(
            fixture,
            class_id=group.id,
            other_class_id=other.id,
            level_id=level.id,
            year_id=year.id,
            students=students,
            teacher_membership=teacher_membership.id,
            teacher_email=teacher_user.email,
        )
    finally:
        session.close()


def teacher_principal(school: School) -> Principal:
    from app.modules.authz import permissions as perms
    from app.modules.authz.system_roles import SYSTEM_ROLES_BY_KEY

    template = SYSTEM_ROLES_BY_KEY["teacher"]
    return Principal(
        user_id=_uuid.uuid4(),
        membership_id=school.teacher_membership,
        tenant_id=school.fixture.tenant_id,
        permissions=perms.expand(set(template.permissions)),
        grants=(Grant(frozenset(template.permissions),
                      ScopeKind.taught_by_self.value, ()),),
        session_id=_uuid.uuid4(),
        authenticated_at=datetime.now(UTC).timestamp(),
    )


# --- the register itself ---------------------------------------------------


def test_the_register_arrives_complete(school: School) -> None:
    """Everybody in the room, in order, before a single tap.

    A teacher who has to search for names takes the register at lunchtime from
    memory instead, and that record is worth nothing.
    """
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=TODAY, class_group_id=school.class_id
        )
        current = attendance.register(session, register_session)
        assert [e.name for e in current.entries] == [
            "Amara Diallo", "Ben Whitfield", "Chen Wei", "Dara O'Neill"
        ]
        assert all(not e.is_marked for e in current.entries)
        assert not current.is_complete
        # And the child in the other class is not in this room.
        assert "Elsewhere Child" not in {e.name for e in current.entries}
        session.rollback()
    finally:
        session.close()


def test_membership_is_derived_from_the_enrolment_not_from_a_list(
    school: School
) -> None:
    """A child who transferred in appears without anybody rebuilding anything.

    And — the half that a stored list gets wrong — last week's register still
    shows last week's class.
    """
    session = school.session()
    try:
        person = people.record_person(session, full_name="Zoe Late-Joiner")
        student = people.register_student(session, person, reference="R-Zoe")
        placement = people.admit(
            session, student, on=date(2026, 9, 10),
            placement=Placement(academic_year_id=school.year_id,
                                level_id=school.level_id,
                                class_group_id=school.class_id),
        )
        people.enrol(session, placement, on=date(2026, 9, 10))
        session.commit()

        after = attendance.register(
            session,
            attendance.open_session(db=session, occurred_on=TODAY,
                                    class_group_id=school.class_id),
        )
        assert "Zoe Late-Joiner" in {e.name for e in after.entries}

        before = attendance.register(
            session,
            attendance.open_session(db=session, occurred_on=date(2026, 9, 3),
                                    class_group_id=school.class_id),
        )
        assert "Zoe Late-Joiner" not in {e.name for e in before.entries}, (
            "a register from before she joined has her in it"
        )
        session.commit()
    finally:
        session.close()


def test_marking_everybody_present_is_one_action(school: School) -> None:
    """The thirty-second path. Four children, one call."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 15), class_group_id=school.class_id
        )
        present = attendance.default_code(session)
        assert present is not None and present.code == "/"
        marked = attendance.mark_all(session, register_session, code_id=present.id)
        assert marked >= 4
        current = attendance.register(session, register_session)
        assert current.is_complete
        assert current.can_submit
        session.rollback()
    finally:
        session.close()


def test_marking_everybody_in_does_not_overwrite_somebody_already_marked(
    school: School
) -> None:
    """Somebody marked late does not become present because the room was marked in."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 16), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        amara = school.students["Amara Diallo"]
        attendance.set_marks(session, register_session, {amara: by_code["L"].id},
                             minutes_late={amara: 12})
        attendance.mark_all(session, register_session, code_id=by_code["/"].id)

        current = attendance.register(session, register_session)
        entry = next(e for e in current.entries if e.student_relationship_id == amara)
        assert entry.code == "L"
        assert entry.minutes_late == 12
        session.rollback()
    finally:
        session.close()


def test_a_part_marked_register_is_a_real_state(school: School) -> None:
    """A fire alarm at 09:04 must not lose the eleven marks already taken."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 17), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        attendance.set_marks(
            session, register_session,
            {school.students["Amara Diallo"]: by_code["/"].id},
        )
        session.commit()
    finally:
        session.close()

    later = school.session()
    try:
        reopened = attendance.open_session(
            db=later, occurred_on=date(2026, 9, 17), class_group_id=school.class_id
        )
        current = attendance.register(later, reopened)
        assert sum(1 for e in current.entries if e.is_marked) == 1
        assert current.status == SessionStatus.open.value
    finally:
        later.close()


def test_opening_the_same_register_twice_returns_one_register(
    school: School
) -> None:
    """A class covered by somebody else, or a page reloaded. Not two registers."""
    session = school.session()
    try:
        first = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 18), class_group_id=school.class_id
        )
        second = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 18), class_group_id=school.class_id
        )
        assert first.id == second.id
        session.rollback()
    finally:
        session.close()


def test_a_register_of_nobody_in_particular_is_refused(school: School) -> None:
    session = school.session()
    try:
        with pytest.raises(attendance.AttendanceError):
            attendance.open_session(db=session, occurred_on=TODAY)
    finally:
        session.rollback()
        session.close()


# --- the codes are the school's --------------------------------------------


def test_a_school_defines_its_own_codes(school: School) -> None:
    """Four seeded codes a school may rename, recolour, extend or delete."""
    from app.modules.attendance.models import AttendanceCode

    session = school.session()
    try:
        session.add(
            AttendanceCode(
                code="V", label="Educational visit", category=MarkCategory.other,
                counts_as_present=True, sequence=9,
            )
        )
        session.flush()
        available = {c.code: c for c in attendance.codes(session)}
        assert "V" in available
        # `other` with `counts_as_present` — the combination a category alone
        # could not express, and the reason the two columns are separate.
        assert available["V"].category is MarkCategory.other
        assert available["V"].counts_as_present
        session.rollback()
    finally:
        session.close()


def test_a_code_from_another_institution_is_refused(school: School) -> None:
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 19), class_group_id=school.class_id
        )
        with pytest.raises(attendance.AttendanceError):
            attendance.set_marks(
                session, register_session,
                {school.students["Amara Diallo"]: _uuid.uuid4()},
            )
    finally:
        session.rollback()
        session.close()


# --- the absence workflow ---------------------------------------------------


def test_a_register_will_not_submit_while_somebody_is_unmarked(
    school: School
) -> None:
    """An incomplete register says nothing about the people missing from it."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 21), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        attendance.set_marks(
            session, register_session,
            {school.students["Amara Diallo"]: by_code["/"].id},
        )
        with pytest.raises(attendance.AttendanceError) as caught:
            attendance.submit(session, register_session)
        assert "no mark" in str(caught.value)
    finally:
        session.rollback()
        session.close()


def test_an_unexplained_absence_holds_the_register_open(school: School) -> None:
    """The code that demands a reason is the one somebody will need it for."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 22), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        attendance.mark_all(session, register_session, code_id=by_code["/"].id)
        attendance.set_marks(
            session, register_session,
            {school.students["Ben Whitfield"]: by_code["A"].id},
        )
        current = attendance.register(session, register_session)
        assert current.is_complete
        assert not current.can_submit
        assert school.students["Ben Whitfield"] in current.unanswered

        with pytest.raises(attendance.AttendanceError):
            attendance.submit(session, register_session)

        attendance.set_marks(
            session, register_session,
            {school.students["Ben Whitfield"]: by_code["A"].id},
            reasons={school.students["Ben Whitfield"]: "No contact from home"},
        )
        assert attendance.register(session, register_session).can_submit
        attendance.submit(session, register_session)
        assert register_session.status is SessionStatus.submitted
        session.rollback()
    finally:
        session.close()


# --- corrections are evidence ----------------------------------------------


def test_correcting_a_mark_records_who_changed_it_and_why(school: School) -> None:
    """The child who arrived at half past nine was absent at nine.

    The register was right both times. What must survive is that it changed.
    """
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 23), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        attendance.mark_all(session, register_session, code_id=by_code["/"].id)
        chen = school.students["Chen Wei"]
        attendance.set_marks(
            session, register_session, {chen: by_code["A"].id},
            reasons={chen: "Not seen"},
        )
        attendance.submit(session, register_session)
        session.commit()

        mark = session.execute(
            AttendanceMark.__table__.select().where(
                AttendanceMark.session_id == register_session.id,
                AttendanceMark.student_relationship_id == chen,
            )
        ).one()

        attendance.set_marks(
            session, register_session, {chen: by_code["L"].id},
            reasons={chen: "Arrived 09:35, medical appointment"},
            amendment_reason="Parent produced an appointment letter",
            membership_id=school.teacher_membership,
        )
        session.commit()

        history = attendance.amendments_for(session, mark.id)
        assert history, "a corrected mark left no trace of the correction"
        latest = history[-1]
        assert latest.previous_code_id == by_code["A"].id
        assert latest.new_code_id == by_code["L"].id
        assert "appointment letter" in latest.reason
        assert latest.previous_reason == "Not seen"
        # And the register itself records that it is no longer the original.
        assert register_session.status is SessionStatus.amended
    finally:
        session.close()


def test_changing_a_submitted_register_needs_a_reason(school: School) -> None:
    """The first correction finishes the job. The second changes a relied-on record."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 9, 24), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        attendance.mark_all(session, register_session, code_id=by_code["/"].id)
        attendance.submit(session, register_session)
        with pytest.raises(attendance.AttendanceError) as caught:
            attendance.set_marks(
                session, register_session,
                {school.students["Amara Diallo"]: by_code["L"].id},
            )
        assert "reason" in str(caught.value)
    finally:
        session.rollback()
        session.close()


def test_the_amendment_ledger_cannot_be_rewritten(school: School) -> None:
    """Append-only at the database, like the audit log and the enrolment ledger."""
    session = school.session()
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("UPDATE attendance_amendments SET reason = 'x'"))
        session.rollback()
        with pytest.raises(ProgrammingError):
            session.execute(text("DELETE FROM attendance_amendments"))
        session.rollback()
    finally:
        session.close()


# --- the figure -------------------------------------------------------------


def test_no_record_is_not_the_same_as_no_attendance(school: School) -> None:
    """`None`, not zero — and a progression rule would hold a child back for zero."""
    session = school.session()
    try:
        summary = attendance.summarise(session, _uuid.uuid4())
        assert summary.sessions == 0
        assert summary.rate is None
    finally:
        session.close()


def test_the_figure_counts_what_the_school_says_counts(school: School) -> None:
    """A school that counts a late arrival as present gets a figure that does."""
    session = school.session()
    try:
        register_session = attendance.open_session(
            db=session, occurred_on=date(2026, 10, 5), class_group_id=school.class_id
        )
        by_code = {c.code: c for c in attendance.codes(session)}
        dara = school.students["Dara O'Neill"]
        attendance.mark_all(session, register_session, code_id=by_code["/"].id)
        attendance.set_marks(session, register_session, {dara: by_code["L"].id})
        session.commit()

        summary = attendance.summarise(
            session, dara, since=date(2026, 10, 1), until=date(2026, 10, 31)
        )
        assert summary.sessions == 1
        assert summary.late == 1
        # "L" counts as present in this school, so the figure is 1.0 — not a
        # penalty for arriving.
        assert summary.rate == 1.0
    finally:
        session.close()


# --- scope: a register is a list of named children -------------------------


def test_a_teacher_reaches_only_the_registers_of_classes_they_teach(
    school: School
) -> None:
    session = school.session()
    try:
        mine = attendance.open_session(
            db=session, occurred_on=date(2026, 11, 2), class_group_id=school.class_id
        )
        theirs = attendance.open_session(
            db=session, occurred_on=date(2026, 11, 2),
            class_group_id=school.other_class_id,
        )
        session.commit()

        teacher = teacher_principal(school)
        visible = session.execute(
            scoped_select(
                AttendanceSession, attendance_scopes.SESSIONS,
                db=session, principal=teacher, permission="attendance.mark.read",
            )
        ).scalars().all()
        ids = {s.id for s in visible}
        assert mine.id in ids
        assert theirs.id not in ids, "a teacher reached another class's register"
    finally:
        session.close()


def test_a_register_is_invisible_without_a_principal(school: School) -> None:
    """A background job that forgot its context reads no children's names."""
    session = school.session()
    try:
        assert (
            scoped_count(
                AttendanceSession, attendance_scopes.SESSIONS,
                db=session, principal=None, permission="attendance.mark.read",
            )
            == 0
        )
    finally:
        session.close()


def test_a_guardian_reaches_marks_but_never_a_whole_register(school: School) -> None:
    """A parent who could open a register would be reading other people's children.

    That is precisely what a register is, so the sessions plan has no
    `own_children` clause at all — and the marks plan composes the *people*
    module's clause rather than writing its own, so the two cannot drift.
    """
    from app.modules.authz.scopes import ScopeKind as Kind

    assert Kind.own_children not in attendance_scopes.SESSIONS.clauses
    assert Kind.own_children in attendance_scopes.MARKS.clauses
    assert Kind.self_only not in attendance_scopes.SESSIONS.clauses


# --- through HTTP, in three calls ------------------------------------------


def test_a_full_register_takes_three_requests(school: School) -> None:
    """Open, mark, submit. The design target, asserted as a count.

    Not a benchmark — a benchmark on this machine says nothing about a phone on
    a school's connection. What *is* meaningful is the number of round trips,
    because that is what the network multiplies.
    """
    with TestClient(app) as client:
        host = school.fixture.hostname
        token = client.post(
            "/api/v1/auth/sign-in",
            json={"email": school.teacher_email, "password": OWNER_PASSWORD},
            headers={"host": host},
        )
        assert token.status_code == 200, token.text
        headers = {"host": host,
                   "authorization": f"Bearer {token.json()['access_token']}"}

        opened = client.post(
            "/api/v1/attendance/register",
            params={"class_group_id": str(school.class_id),
                    "occurred_on": "2026-12-01"},
            headers=headers,
        )
        assert opened.status_code == 200, opened.text
        body = opened.json()
        assert body["total"] >= 4
        assert body["marked"] == 0
        assert body["default_code_id"]
        assert not body["can_submit"]
        # Everything needed to render the whole screen came back in this one
        # call: the people, their marks, the codes and the default.
        assert {c["code"] for c in body["codes"]} >= {"/", "L", "A", "E"}

        present = body["default_code_id"]
        marked = client.post(
            f"/api/v1/attendance/register/{body['session_id']}/marks",
            json={"marks": [
                {"student_relationship_id": e["student_relationship_id"],
                 "code_id": present}
                for e in body["entries"]
            ]},
            headers=headers,
        )
        assert marked.status_code == 200, marked.text
        assert marked.json()["marked"] == body["total"]
        assert marked.json()["can_submit"]

        done = client.post(
            f"/api/v1/attendance/register/{body['session_id']}/submit",
            headers=headers,
        )
        assert done.status_code == 200, done.text
        assert done.json()["status"] == "submitted"


def test_another_classs_register_is_a_404_over_http(school: School) -> None:
    """Identical to an id that was never issued."""
    session = school.session()
    try:
        theirs = attendance.open_session(
            db=session, occurred_on=date(2026, 12, 2),
            class_group_id=school.other_class_id,
        )
        session.commit()
        foreign_id = theirs.id
    finally:
        session.close()

    with TestClient(app) as client:
        host = school.fixture.hostname
        token = client.post(
            "/api/v1/auth/sign-in",
            json={"email": school.teacher_email, "password": OWNER_PASSWORD},
            headers={"host": host},
        ).json()["access_token"]
        headers = {"host": host, "authorization": f"Bearer {token}"}
        real = client.post(
            f"/api/v1/attendance/register/{foreign_id}/marks",
            json={"marks": []}, headers=headers,
        )
        invented = client.post(
            f"/api/v1/attendance/register/{_uuid.uuid4()}/marks",
            json={"marks": []}, headers=headers,
        )
        assert real.status_code == 404
        assert invented.status_code == 404
        assert real.json() == invented.json()


def test_a_school_without_the_feature_cannot_take_a_register(platform: None) -> None:
    """Entitlement and permission are separate, and both are declared."""
    from app.modules.billing.models import SubscriptionStatus

    fixture = _provision("register-unentitled")
    session = fixture.session()
    try:
        billing.subscribe(session, plan_key="plan.free",
                          status=SubscriptionStatus.canceled)
        session.commit()
    finally:
        session.close()

    with TestClient(app) as client:
        host = fixture.hostname
        token = client.post(
            "/api/v1/auth/sign-in",
            json={"email": f"owner@{fixture.tenant.slug}.test",
                  "password": OWNER_PASSWORD},
            headers={"host": host},
        ).json()["access_token"]
        response = client.post(
            "/api/v1/attendance/register",
            params={"class_group_id": str(_uuid.uuid4())},
            headers={"host": host, "authorization": f"Bearer {token}"},
        )
        assert response.status_code == 402, response.text
        assert response.json()["error"]["code"] == "entitlement_required"
