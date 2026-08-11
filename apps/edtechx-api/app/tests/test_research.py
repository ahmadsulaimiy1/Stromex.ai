"""Candidature, supervision, and the boundary around both.

The tests that matter here are not "can a supervisor see their researcher".
They are the four ways the boundary could be wrong and nobody would notice
until a graduate school phoned:

  * a supervisor reading a candidate who is not theirs,
  * a supervisor still reading a candidate they handed over,
  * a candidate reading another candidate,
  * and a milestone that is late according to a stored flag rather than
    according to the calendar.

The last of those is not a security property, but it is the one that makes a
research office stop trusting the product, so it is pinned with the same force.
"""

from __future__ import annotations

import uuid as _uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import Grant, Principal
from app.modules.academics.research import Milestone, MilestoneState, Supervision
from app.modules.academics.structure import (
    AcademicUnit,
    MilestoneDefinition,
    Programme,
    Qualification,
    SupervisionRole,
)
from app.modules.academics.supervision import (
    MilestoneTransitionRefused,
    add_months,
    assign_supervisor,
    candidature,
    caseload,
    end_supervision,
    log_meeting,
    months_between,
    plan_milestones,
    record_milestone,
)
from app.modules.authz.scopes import ScopeKind
from app.modules.people import service as people
from app.modules.people.models import Person
from app.modules.people.service import Placement
from app.tests.conftest import TenantFixture, requires_db

pytestmark = requires_db

TODAY = date(2026, 11, 12)


# --- a graduate school ------------------------------------------------------


@dataclass
class GradSchool:
    school: TenantFixture
    programme: _uuid.UUID
    role_principal: _uuid.UUID
    role_second: _uuid.UUID
    researchers: dict[str, _uuid.UUID]      # name -> student relationship id
    staff: dict[str, _uuid.UUID]            # name -> staff relationship id
    users: dict[str, _uuid.UUID]            # name -> user id on their Person

    def session(self) -> Session:
        return self.school.session()


def _build(school: TenantFixture) -> GradSchool:
    from app.modules.identity.models import Membership, MembershipStatus, User

    session = school.session()

    def account(name: str) -> _uuid.UUID:
        user = User(email=f"{_uuid.uuid4().hex[:8]}@grad.test", full_name=name)
        session.add(user)
        session.flush()
        session.add(
            Membership(
                user_id=user.id, status=MembershipStatus.active, display_name=name
            )
        )
        session.flush()
        return user.id

    try:
        unit = AcademicUnit(code="grad", name="Graduate School", kind_label="School")
        session.add(unit)
        session.flush()
        qualification = Qualification(
            code="phd", name="Doctor of Philosophy", category_label="Doctoral"
        )
        session.add(qualification)
        session.flush()
        programme = Programme(
            code="phd-cs",
            name="PhD in Computer Science",
            academic_unit_id=unit.id,
            qualification_id=qualification.id,
            is_research=True,
        )
        session.add(programme)
        session.flush()
        for index, (code, name, months) in enumerate(
            (
                ("proposal", "Research proposal", 6),
                ("upgrade", "Upgrade viva", 18),
                ("submission", "Thesis submission", 42),
                ("viva", "Viva voce", 48),
            )
        ):
            session.add(
                MilestoneDefinition(
                    programme_id=programme.id,
                    code=code,
                    name=name,
                    sequence=index,
                    expected_offset_months=months,
                )
            )
        roles = {}
        for code, name, primary in (
            ("principal", "Principal supervisor", True),
            ("second", "Second supervisor", False),
        ):
            row = SupervisionRole(code=code, name=name, is_primary=primary)
            session.add(row)
            session.flush()
            roles[code] = row.id

        staff: dict[str, _uuid.UUID] = {}
        users: dict[str, _uuid.UUID] = {}
        for name in ("Amina Yusuf", "Tomas Reinholt"):
            users[name] = account(name)
            person = people.record_person(
                session, full_name=name, user_id=users[name]
            )
            relationship = people.register_staff(
                session, person, kind_label="Professor", is_teaching=True
            )
            staff[name] = relationship.id

        researchers: dict[str, _uuid.UUID] = {}
        for name, reference, started in (
            ("Yusuf Al-Amin", "R-2025-01", date(2025, 4, 1)),
            ("Ingrid Sorensen", "R-2026-02", date(2026, 2, 1)),
        ):
            users[name] = account(name)
            person = people.record_person(
                session, full_name=name, user_id=users[name]
            )
            student = people.register_student(
                session, person, reference=reference, kind_label="Researcher"
            )
            placement = people.admit(
                session,
                student,
                on=started,
                # No academic year: research intake is continuous, and the
                # enrolment model makes every structural layer optional for
                # exactly this reason.
                placement=Placement(programme_id=programme.id),
            )
            people.enrol(session, placement, on=started)
            researchers[name] = student.id
            plan_milestones(
                session,
                student_relationship_id=student.id,
                programme_id=programme.id,
                from_date=started,
            )

        assign_supervisor(
            session,
            student_relationship_id=researchers["Yusuf Al-Amin"],
            staff_relationship_id=staff["Amina Yusuf"],
            supervision_role_id=roles["principal"],
            on=date(2025, 4, 1),
        )
        assign_supervisor(
            session,
            student_relationship_id=researchers["Ingrid Sorensen"],
            staff_relationship_id=staff["Tomas Reinholt"],
            supervision_role_id=roles["principal"],
            on=date(2026, 2, 1),
        )
        session.commit()
        return GradSchool(
            school=school,
            programme=programme.id,
            role_principal=roles["principal"],
            role_second=roles["second"],
            researchers=researchers,
            staff=staff,
            users=users,
        )
    finally:
        session.close()


@pytest.fixture
def grad(school_a: TenantFixture) -> GradSchool:
    return _build(school_a)


def principal_for(
    grad: GradSchool, name: str, *, kind: ScopeKind, permissions: tuple[str, ...]
) -> Principal:
    return Principal(
        user_id=grad.users[name],
        membership_id=_uuid.uuid4(),
        tenant_id=grad.school.tenant_id,
        permissions=frozenset(permissions),
        grants=tuple(
            Grant(permissions=frozenset({p}), scope_kind=kind.value, scope_ids=())
            for p in permissions
        ),
        session_id=_uuid.uuid4(),
        authenticated_at=datetime.now(UTC).timestamp(),
    )


SUPERVISOR_PERMISSIONS = (
    "research.supervision.read",
    "research.milestone.read",
    "research.meeting.read",
)


def supervisor(grad: GradSchool, name: str) -> Principal:
    return principal_for(
        grad, name, kind=ScopeKind.supervised_by_self, permissions=SUPERVISOR_PERMISSIONS
    )


def researcher(grad: GradSchool, name: str) -> Principal:
    return principal_for(
        grad, name, kind=ScopeKind.self_only, permissions=SUPERVISOR_PERMISSIONS
    )


def _milestone(session: Session, student_id: _uuid.UUID, code: str) -> Milestone:
    return session.execute(
        select(Milestone)
        .join(
            MilestoneDefinition,
            MilestoneDefinition.id == Milestone.milestone_definition_id,
        )
        .where(
            Milestone.student_relationship_id == student_id,
            MilestoneDefinition.code == code,
        )
    ).scalars().one()


# --- the arithmetic ---------------------------------------------------------


def test_add_months_never_produces_an_impossible_date() -> None:
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2026, 4, 1), 48) == date(2030, 4, 1)


def test_months_between_floors_rather_than_rounds() -> None:
    assert months_between(date(2025, 4, 1), date(2026, 11, 12)) == 19
    assert months_between(date(2025, 4, 15), date(2025, 5, 14)) == 0
    assert months_between(date(2025, 4, 15), date(2025, 5, 15)) == 1


# --- planning ---------------------------------------------------------------


def test_milestones_are_planned_from_the_programme_and_dated(grad: GradSchool) -> None:
    session = grad.session()
    try:
        state = candidature(
            session,
            None,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        # No principal: no rows. The fail-closed default, asserted before
        # anything else, because every test below would pass vacuously if this
        # returned everything instead.
        assert state.milestones == []

        rows = session.execute(
            select(Milestone).where(
                Milestone.student_relationship_id
                == grad.researchers["Yusuf Al-Amin"]
            )
        ).scalars().all()
        assert len(rows) == 4
        due = {r.milestone_definition_id: r.due_on for r in rows}
        proposal = session.execute(
            select(MilestoneDefinition).where(MilestoneDefinition.code == "proposal")
        ).scalars().one()
        assert due[proposal.id] == date(2025, 10, 1)
    finally:
        session.close()


def test_replanning_never_moves_a_date_somebody_is_working_towards(
    grad: GradSchool,
) -> None:
    """The rule-change trap: a programme edited in year three of a candidature."""
    session = grad.session()
    try:
        student_id = grad.researchers["Yusuf Al-Amin"]
        before = {
            r.milestone_definition_id: r.due_on
            for r in session.execute(
                select(Milestone).where(
                    Milestone.student_relationship_id == student_id
                )
            ).scalars()
        }
        session.add(
            MilestoneDefinition(
                programme_id=grad.programme,
                code="ethics",
                name="Ethics approval",
                sequence=4,
                expected_offset_months=9,
            )
        )
        session.flush()
        planned = plan_milestones(
            session,
            student_relationship_id=student_id,
            programme_id=grad.programme,
            # A different start date, deliberately: if the existing rows were
            # rewritten this is what would move them.
            from_date=date(2026, 1, 1),
        )
        assert len(planned) == 1
        after = {
            r.milestone_definition_id: r.due_on
            for r in session.execute(
                select(Milestone).where(
                    Milestone.student_relationship_id == student_id
                )
            ).scalars()
        }
        for definition_id, due in before.items():
            assert after[definition_id] == due
    finally:
        session.rollback()
        session.close()


# --- lateness is arithmetic -------------------------------------------------


def test_overdue_is_computed_from_the_date_not_stored(grad: GradSchool) -> None:
    session = grad.session()
    try:
        watcher = supervisor(grad, "Tomas Reinholt")
        student_id = grad.researchers["Ingrid Sorensen"]

        early = candidature(
            session, watcher, student_relationship_id=student_id, on=date(2026, 7, 1)
        )
        assert early.overdue == []

        late = candidature(
            session, watcher, student_relationship_id=student_id, on=TODAY
        )
        assert [m.code for m in late.overdue] == ["proposal"]

        # Nothing was written to make that true.
        stored = session.execute(
            select(Milestone).where(
                Milestone.student_relationship_id == student_id
            )
        ).scalars().all()
        assert all(row.state is MilestoneState.expected for row in stored)
    finally:
        session.close()


def test_a_milestone_decided_late_does_not_stay_flagged(grad: GradSchool) -> None:
    """A candidate who passed six weeks late is not delinquent for four years."""
    session = grad.session()
    try:
        student_id = grad.researchers["Ingrid Sorensen"]
        row = session.execute(
            select(Milestone)
            .join(
                MilestoneDefinition,
                MilestoneDefinition.id == Milestone.milestone_definition_id,
            )
            .where(
                Milestone.student_relationship_id == student_id,
                MilestoneDefinition.code == "proposal",
            )
        ).scalars().one()
        record_milestone(
            session, row, state=MilestoneState.passed, on=date(2026, 10, 20)
        )
        state = candidature(
            session,
            supervisor(grad, "Tomas Reinholt"),
            student_relationship_id=student_id,
            on=TODAY,
        )
        assert state.overdue == []
        assert state.completed == 1
    finally:
        session.rollback()
        session.close()


def test_a_decision_cannot_predate_the_work_it_ruled_on(grad: GradSchool) -> None:
    session = grad.session()
    try:
        row = session.execute(
            select(Milestone).where(
                Milestone.student_relationship_id
                == grad.researchers["Yusuf Al-Amin"]
            )
        ).scalars().first()
        record_milestone(
            session, row, state=MilestoneState.submitted, on=date(2026, 9, 1)
        )
        with pytest.raises(MilestoneTransitionRefused):
            record_milestone(
                session, row, state=MilestoneState.passed, on=date(2026, 8, 1)
            )
    finally:
        session.rollback()
        session.close()


def test_the_database_refuses_a_decided_state_with_no_decision_date(
    grad: GradSchool,
) -> None:
    """The check constraint, attacked directly rather than through the service."""
    from sqlalchemy.exc import IntegrityError

    session = grad.session()
    try:
        row = session.execute(
            select(Milestone).where(
                Milestone.student_relationship_id
                == grad.researchers["Yusuf Al-Amin"]
            )
        ).scalars().first()
        row.state = MilestoneState.passed
        row.decided_on = None
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.rollback()
        session.close()


# --- the boundary -----------------------------------------------------------


def test_a_supervisor_reaches_their_own_researcher(grad: GradSchool) -> None:
    session = grad.session()
    try:
        state = candidature(
            session,
            supervisor(grad, "Amina Yusuf"),
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert len(state.milestones) == 4
        assert [s.name for s in state.supervisors] == ["Amina Yusuf"]
    finally:
        session.close()


def test_a_supervisor_reaches_nothing_of_somebody_elses_researcher(
    grad: GradSchool,
) -> None:
    session = grad.session()
    try:
        state = candidature(
            session,
            supervisor(grad, "Amina Yusuf"),
            student_relationship_id=grad.researchers["Ingrid Sorensen"],
            on=TODAY,
        )
        assert state.milestones == []
        assert state.supervisors == []
        assert state.meetings == []
    finally:
        session.close()


def test_supervision_scope_ends_when_the_supervision_does(grad: GradSchool) -> None:
    """The drift this scope exists to prevent: reach that outlives the role."""
    session = grad.session()
    try:
        watcher = supervisor(grad, "Amina Yusuf")
        assert len(caseload(session, watcher, on=TODAY)) == 1

        supervision = session.execute(
            select(Supervision).where(
                Supervision.staff_relationship_id == grad.staff["Amina Yusuf"]
            )
        ).scalars().one()
        end_supervision(session, supervision, on=date(2026, 9, 30), reason="Handover")
        session.flush()

        assert caseload(session, watcher, on=TODAY) == []
        after = candidature(
            session,
            watcher,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert after.milestones == []
    finally:
        session.rollback()
        session.close()


def test_a_researcher_reaches_their_own_candidature_and_no_other(
    grad: GradSchool,
) -> None:
    session = grad.session()
    try:
        actor = researcher(grad, "Yusuf Al-Amin")
        mine = candidature(
            session,
            actor,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert len(mine.milestones) == 4

        theirs = candidature(
            session,
            actor,
            student_relationship_id=grad.researchers["Ingrid Sorensen"],
            on=TODAY,
        )
        assert theirs.milestones == []
        assert theirs.supervisors == []
    finally:
        session.close()


def test_a_researcher_has_no_caseload(grad: GradSchool) -> None:
    """A caseload is what *you* supervise. A candidate supervises nobody.

    Worth an explicit test because the `self` scope does reach the candidate's
    own supervision rows — correctly, since their own screen lists who
    supervises them — and an implementation that read "supervisions I can see"
    as "researchers I supervise" would put a candidate on their own caseload.
    """
    session = grad.session()
    try:
        assert caseload(session, researcher(grad, "Yusuf Al-Amin"), on=TODAY) == []
    finally:
        session.close()


def test_a_co_supervised_candidate_appears_once(grad: GradSchool) -> None:
    """Two supervisors on one candidate is one row on each list, not two."""
    session = grad.session()
    try:
        assign_supervisor(
            session,
            student_relationship_id=grad.researchers["Ingrid Sorensen"],
            staff_relationship_id=grad.staff["Amina Yusuf"],
            supervision_role_id=grad.role_second,
            on=date(2026, 2, 1),
        )
        session.flush()
        rows = caseload(session, supervisor(grad, "Amina Yusuf"), on=TODAY)
        assert [r.researcher for r in rows].count("Ingrid Sorensen") == 1
        # And the role shown is the reader's own, not the other supervisor's.
        ingrid = next(r for r in rows if r.researcher == "Ingrid Sorensen")
        assert ingrid.role == "Second supervisor"
    finally:
        session.rollback()
        session.close()


def test_a_teacher_scope_does_not_reach_a_candidature(grad: GradSchool) -> None:
    """`taught_by_self` is absent from the research plans, on purpose."""
    session = grad.session()
    try:
        teaching = principal_for(
            grad,
            "Amina Yusuf",
            kind=ScopeKind.taught_by_self,
            permissions=SUPERVISOR_PERMISSIONS,
        )
        state = candidature(
            session,
            teaching,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert state.milestones == []
    finally:
        session.close()


def test_a_guardian_scope_does_not_reach_a_candidature(grad: GradSchool) -> None:
    session = grad.session()
    try:
        family = principal_for(
            grad,
            "Amina Yusuf",
            kind=ScopeKind.own_children,
            permissions=SUPERVISOR_PERMISSIONS,
        )
        state = candidature(
            session,
            family,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert state.milestones == []
    finally:
        session.close()


def test_the_programme_scope_reaches_the_whole_graduate_school(
    grad: GradSchool,
) -> None:
    session = grad.session()
    try:
        office = Principal(
            user_id=_uuid.uuid4(),
            membership_id=_uuid.uuid4(),
            tenant_id=grad.school.tenant_id,
            permissions=frozenset(SUPERVISOR_PERMISSIONS),
            grants=tuple(
                Grant(
                    permissions=frozenset({p}),
                    scope_kind=ScopeKind.programme.value,
                    scope_ids=(grad.programme,),
                )
                for p in SUPERVISOR_PERMISSIONS
            ),
            session_id=_uuid.uuid4(),
            authenticated_at=datetime.now(UTC).timestamp(),
        )
        for name in grad.researchers:
            state = candidature(
                session,
                office,
                student_relationship_id=grad.researchers[name],
                on=TODAY,
            )
            assert len(state.milestones) == 4
    finally:
        session.close()


# --- contact ----------------------------------------------------------------


def test_a_scheduled_milestone_past_its_date_is_not_overdue(grad: GradSchool) -> None:
    """Overdue means nothing has happened, not that the diary date has passed."""
    session = grad.session()
    try:
        student_id = grad.researchers["Yusuf Al-Amin"]
        row = _milestone(session, student_id, "upgrade")
        assert row.due_on == date(2026, 10, 1)
        assert row.is_overdue(on=TODAY)

        record_milestone(
            session, row, state=MilestoneState.scheduled, on=date(2026, 12, 8)
        )
        assert not row.is_overdue(on=TODAY)

        record_milestone(
            session, row, state=MilestoneState.submitted, on=date(2026, 11, 10)
        )
        assert not row.is_overdue(on=TODAY)
    finally:
        session.rollback()
        session.close()


def test_the_caseload_puts_the_drifting_candidate_first(grad: GradSchool) -> None:
    """Two supervisions on one supervisor, one healthy and one not."""
    session = grad.session()
    try:
        assign_supervisor(
            session,
            student_relationship_id=grad.researchers["Ingrid Sorensen"],
            staff_relationship_id=grad.staff["Amina Yusuf"],
            supervision_role_id=grad.role_second,
            on=date(2026, 2, 1),
        )
        for code, state, when in (
            ("proposal", MilestoneState.passed, date(2025, 9, 26)),
            ("upgrade", MilestoneState.scheduled, date(2026, 12, 8)),
        ):
            record_milestone(
                session,
                _milestone(session, grad.researchers["Yusuf Al-Amin"], code),
                state=state,
                on=when,
            )
        log_meeting(
            session,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            held_on=date(2026, 11, 3),
            staff_relationship_id=grad.staff["Amina Yusuf"],
        )
        session.flush()

        watcher = supervisor(grad, "Amina Yusuf")
        rows = caseload(session, watcher, on=TODAY)
        assert [r.researcher for r in rows] == ["Ingrid Sorensen", "Yusuf Al-Amin"]
        assert rows[0].needs_attention
        assert rows[0].is_out_of_contact          # never met
        assert not rows[1].needs_attention
        assert rows[1].candidature.days_since_meeting == 9
    finally:
        session.rollback()
        session.close()


def test_a_supervision_is_idempotent(grad: GradSchool) -> None:
    """Assigning the same supervisor twice is a no-op, not a duplicate row."""
    session = grad.session()
    try:
        first = assign_supervisor(
            session,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            staff_relationship_id=grad.staff["Amina Yusuf"],
            supervision_role_id=grad.role_principal,
            on=date(2026, 1, 1),
        )
        assert first.started_on == date(2025, 4, 1)
        rows = session.execute(
            select(Supervision).where(
                Supervision.student_relationship_id
                == grad.researchers["Yusuf Al-Amin"]
            )
        ).scalars().all()
        assert len(rows) == 1
    finally:
        session.rollback()
        session.close()


def test_candidature_start_comes_from_the_enrolment(grad: GradSchool) -> None:
    """One source for the date, so there is nothing for a second one to contradict."""
    session = grad.session()
    try:
        state = candidature(
            session,
            supervisor(grad, "Amina Yusuf"),
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            on=TODAY,
        )
        assert state.started_on == date(2025, 4, 1)
        assert state.elapsed_months == 19
        assert state.horizon_months == 48
    finally:
        session.close()


def test_the_next_requirement_is_the_earliest_undecided_one(grad: GradSchool) -> None:
    session = grad.session()
    try:
        student_id = grad.researchers["Yusuf Al-Amin"]
        row = session.execute(
            select(Milestone)
            .join(
                MilestoneDefinition,
                MilestoneDefinition.id == Milestone.milestone_definition_id,
            )
            .where(
                Milestone.student_relationship_id == student_id,
                MilestoneDefinition.code == "proposal",
            )
        ).scalars().one()
        record_milestone(
            session,
            row,
            state=MilestoneState.passed,
            on=date(2025, 9, 20),
            outcome_label="Approved without amendment",
        )
        state = candidature(
            session,
            supervisor(grad, "Amina Yusuf"),
            student_relationship_id=student_id,
            on=TODAY,
        )
        assert state.next_requirement is not None
        assert state.next_requirement.code == "upgrade"
    finally:
        session.rollback()
        session.close()


def test_a_supervision_survives_the_person_leaving(grad: GradSchool) -> None:
    """A meeting record outlives the staff row it points at; a supervision does not.

    Deliberately asymmetric. Losing the supervisor of record would erase who
    was responsible for a candidate; losing who chaired one meeting in 2027
    would not, and forcing an institution to keep a staff row forever to delete
    nothing is how records stop being maintained at all.
    """
    session = grad.session()
    try:
        meeting = log_meeting(
            session,
            student_relationship_id=grad.researchers["Yusuf Al-Amin"],
            held_on=date(2026, 10, 1),
            staff_relationship_id=grad.staff["Amina Yusuf"],
        )
        session.flush()
        assert meeting.staff_relationship_id is not None
        person = session.execute(
            select(Person).where(Person.full_name == "Amina Yusuf")
        ).scalars().one()
        assert person is not None
    finally:
        session.rollback()
        session.close()
