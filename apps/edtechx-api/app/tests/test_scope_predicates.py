"""Scopes as data-access boundaries, attacked rather than demonstrated.

A correct permission with an incorrect predicate is still a breach. So this
suite spends most of its length not on "does the authorized person see their
rows" but on the question underneath it: *can anybody learn something they were
not granted?* — through a count, a page total, a search, an aggregate, an id
probe, or the difference between two error responses.

The institution below is built to make every scope kind meaningful at once:

    Faculty of Science ─── Department of Biology ─── BSc Biology ─ Y1 ─ 1A, 1B
                       └── Department of Physics ─── BSc Physics ─ P1 ─ P1A
    Faculty of Arts    ─── Department of History ─── BA History  ─ H1 ─ H1A

Six students spread across it, a teacher allocated to 1A only, a head of the
Biology department, a head of the whole Science faculty, a guardian with one
child, and a student who is their own subject. Every assertion below is about
one of them being able — or unable — to reach the others.
"""

from __future__ import annotations

import uuid as _uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.context import Grant, Principal
from app.main import app
from app.modules.academics.models import (
    AcademicYear,
    ClassGroup,
    Level,
    TeachingAllocation,
)
from app.modules.academics.structure import AcademicUnit, Cohort, Programme
from app.modules.authz.predicates import (
    ScopePlanError,
    SystemAccessRefused,
    predicate_for,
    scoped_count,
    scoped_get,
    scoped_select,
    system_access,
)
from app.modules.authz.scopes import Scope, ScopeKind, ScopeSet, scopes_for
from app.modules.people import scopes as plans
from app.modules.people import service as people
from app.modules.people.models import Person, StudentRelationship
from app.modules.people.service import Placement
from app.tests.conftest import TenantFixture, requires_db, session_for
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db

READ = "people.student.read"


# --- the institution -------------------------------------------------------


@dataclass
class World:
    """Every id the assertions below need, built once."""

    school: TenantFixture
    faculty_science: _uuid.UUID
    faculty_arts: _uuid.UUID
    dept_biology: _uuid.UUID
    dept_physics: _uuid.UUID
    dept_history: _uuid.UUID
    prog_biology: _uuid.UUID
    prog_physics: _uuid.UUID
    prog_history: _uuid.UUID
    level_biology: _uuid.UUID
    level_physics: _uuid.UUID
    level_history: _uuid.UUID
    class_1a: _uuid.UUID
    class_1b: _uuid.UUID
    class_p1a: _uuid.UUID
    class_h1a: _uuid.UUID
    cohort_2026: _uuid.UUID
    students: dict[str, _uuid.UUID]        # name -> student_relationship id
    people_ids: dict[str, _uuid.UUID]      # name -> person id
    teacher_membership: _uuid.UUID
    guardian_user: _uuid.UUID
    student_user: _uuid.UUID

    def session(self) -> Session:
        return self.school.session()


def _build(school: TenantFixture) -> World:
    session = school.session()
    try:
        def unit(code, name, kind, parent=None):
            row = AcademicUnit(code=code, name=name, kind_label=kind, parent_id=parent)
            session.add(row)
            session.flush()
            return row

        science = unit("sci", "Faculty of Science", "Faculty")
        arts = unit("art", "Faculty of Arts", "Faculty")
        biology = unit("bio", "Department of Biology", "Department", science.id)
        physics = unit("phy", "Department of Physics", "Department", science.id)
        history = unit("his", "Department of History", "Department", arts.id)

        def programme(code, name, unit_id):
            row = Programme(code=code, name=name, academic_unit_id=unit_id)
            session.add(row)
            session.flush()
            return row

        bsc_bio = programme("bsc-bio", "BSc Biology", biology.id)
        bsc_phy = programme("bsc-phy", "BSc Physics", physics.id)
        ba_his = programme("ba-his", "BA History", history.id)

        def level(code, name, programme_id, sequence):
            row = Level(code=code, name=name, programme_id=programme_id, sequence=sequence)
            session.add(row)
            session.flush()
            return row

        y1 = level("y1", "Year 1", bsc_bio.id, 0)
        p1 = level("p1", "Year 1", bsc_phy.id, 0)
        h1 = level("h1", "Year 1", ba_his.id, 0)

        year = AcademicYear(
            name="2026", code="2026", starts_on=date(2026, 9, 1),
            ends_on=date(2027, 7, 31), is_current=True,
        )
        session.add(year)
        session.flush()

        cohort = Cohort(code="c2026", name="2026 Intake", programme_id=bsc_bio.id,
                        academic_year_id=year.id)
        session.add(cohort)
        session.flush()

        def group(code, name, level_id, cohort_id=None):
            row = ClassGroup(code=code, name=name, level_id=level_id,
                             academic_year_id=year.id, cohort_id=cohort_id)
            session.add(row)
            session.flush()
            return row

        one_a = group("1a", "1A", y1.id, cohort.id)
        one_b = group("1b", "1B", y1.id)
        p1a = group("p1a", "P1A", p1.id)
        h1a = group("h1a", "H1A", h1.id)

        students: dict[str, _uuid.UUID] = {}
        person_ids: dict[str, _uuid.UUID] = {}

        def enrol(name, level_id, class_id, programme_id, cohort_id=None):
            person = people.record_person(session, full_name=name)
            student = people.register_student(session, person, reference=f"REF-{name[:6]}")
            placement = people.admit(
                session, student, on=date(2026, 9, 1),
                placement=Placement(
                    academic_year_id=year.id, programme_id=programme_id,
                    level_id=level_id, class_group_id=class_id, cohort_id=cohort_id,
                ),
            )
            people.enrol(session, placement, on=date(2026, 9, 1))
            students[name] = student.id
            person_ids[name] = person.id
            return person, student

        enrol("Bio One A", y1.id, one_a.id, bsc_bio.id, cohort.id)
        enrol("Bio Two A", y1.id, one_a.id, bsc_bio.id, cohort.id)
        enrol("Bio Three B", y1.id, one_b.id, bsc_bio.id)
        enrol("Phys One", p1.id, p1a.id, bsc_phy.id)
        enrol("Hist One", h1.id, h1a.id, ba_his.id)
        enrol("Self Student", y1.id, one_b.id, bsc_bio.id)

        # A student with no placement at all: admitted, never enrolled. Reached
        # by nobody's structural scope, which is the correct and easily-missed
        # answer.
        floating_person = people.record_person(session, full_name="Unplaced Applicant")
        floating = people.register_student(session, floating_person, reference="REF-FLOAT")
        students["Unplaced Applicant"] = floating.id
        person_ids["Unplaced Applicant"] = floating_person.id

        session.commit()
        return {
            "science": science.id, "arts": arts.id, "biology": biology.id,
            "physics": physics.id, "history": history.id,
            "bsc_bio": bsc_bio.id, "bsc_phy": bsc_phy.id, "ba_his": ba_his.id,
            "y1": y1.id, "p1": p1.id, "h1": h1.id,
            "1a": one_a.id, "1b": one_b.id, "p1a": p1a.id, "h1a": h1a.id,
            "cohort": cohort.id, "students": students, "people": person_ids,
        }
    finally:
        session.close()


def _identities(school: TenantFixture, built: dict) -> tuple[_uuid.UUID, _uuid.UUID, _uuid.UUID]:
    """A teacher membership, a guardian identity, and a student identity."""
    from app.modules.identity.models import Membership, MembershipStatus, User

    session = school.session()
    try:
        def account(email: str, name: str) -> User:
            user = User(email=email, full_name=name)
            session.add(user)
            session.flush()
            membership = Membership(
                user_id=user.id, status=MembershipStatus.active, display_name=name
            )
            session.add(membership)
            session.flush()
            return user, membership

        teacher_user, teacher_membership = account(
            f"teacher-{_uuid.uuid4().hex[:6]}@scope.test", "A Teacher"
        )
        teacher_person = people.record_person(
            session, full_name="A Teacher", user_id=teacher_user.id
        )
        people.register_staff(
            session, teacher_person, kind_label="Lecturer", is_teaching=True
        )
        session.add(
            TeachingAllocation(
                membership_id=teacher_membership.id,
                class_group_id=built["1a"],
                academic_year_id=None,
            )
        )

        guardian_user, _ = account(
            f"guardian-{_uuid.uuid4().hex[:6]}@scope.test", "A Guardian"
        )
        guardian_person = people.record_person(
            session, full_name="A Guardian", user_id=guardian_user.id
        )
        people.link_guardian(
            session,
            guardian=guardian_person,
            student=session.get(Person, built["people"]["Bio Three B"]),
            relationship_label="Mother",
        )

        student_user, _ = account(
            f"self-{_uuid.uuid4().hex[:6]}@scope.test", "Self Student"
        )
        own = session.get(Person, built["people"]["Self Student"])
        own.user_id = student_user.id

        session.commit()
        return teacher_membership.id, guardian_user.id, student_user.id
    finally:
        session.close()


@pytest.fixture(scope="module")
def world() -> World:
    school = _provision("scope-school")
    built = _build(school)
    teacher_membership, guardian_user, student_user = _identities(school, built)
    return World(
        school=school,
        faculty_science=built["science"], faculty_arts=built["arts"],
        dept_biology=built["biology"], dept_physics=built["physics"],
        dept_history=built["history"],
        prog_biology=built["bsc_bio"], prog_physics=built["bsc_phy"],
        prog_history=built["ba_his"],
        level_biology=built["y1"], level_physics=built["p1"], level_history=built["h1"],
        class_1a=built["1a"], class_1b=built["1b"], class_p1a=built["p1a"],
        class_h1a=built["h1a"], cohort_2026=built["cohort"],
        students=built["students"], people_ids=built["people"],
        teacher_membership=teacher_membership,
        guardian_user=guardian_user, student_user=student_user,
    )


def actor(
    *grants: tuple[str, ScopeKind, tuple[_uuid.UUID, ...]],
    user_id: _uuid.UUID | None = None,
    membership_id: _uuid.UUID | None = None,
    tenant_id: _uuid.UUID | None = None,
) -> Principal:
    """A principal holding exactly these grants and nothing else."""
    return Principal(
        user_id=user_id or _uuid.uuid4(),
        membership_id=membership_id or _uuid.uuid4(),
        tenant_id=tenant_id or _uuid.uuid4(),
        permissions=frozenset({permission for permission, _kind, _ids in grants}),
        grants=tuple(
            Grant(permissions=frozenset({permission}), scope_kind=kind.value,
                  scope_ids=ids)
            for permission, kind, ids in grants
        ),
        session_id=_uuid.uuid4(),
        authenticated_at=datetime.now(UTC).timestamp(),
    )


def visible(db: Session, principal: Principal | None, permission: str = READ) -> set[str]:
    """The names of the students this principal may read. The unit of every test."""
    rows = db.execute(
        scoped_select(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=db, principal=principal, permission=permission,
        )
    ).scalars().all()
    return {
        db.get(Person, row.person_id).full_name
        for row in rows
        if db.get(Person, row.person_id) is not None
    }


EVERYBODY = {
    "Bio One A", "Bio Two A", "Bio Three B", "Phys One", "Hist One",
    "Self Student", "Unplaced Applicant",
}


# --- fail closed ------------------------------------------------------------


def test_no_principal_sees_nothing(world: World) -> None:
    """A background job that forgot its context reads nothing, not everything.

    The single most important assertion in this file. Every other test is about
    a boundary being in the right place; this one is about the default when
    there is no boundary to place.
    """
    session = world.session()
    try:
        assert visible(session, None) == set()
    finally:
        session.close()


def test_a_principal_with_no_relevant_grant_sees_nothing(world: World) -> None:
    """Permission for something else is not permission scoped to nothing."""
    session = world.session()
    try:
        elsewhere = actor(
            ("communication.announcement.read", ScopeKind.tenant, ()),
        )
        assert visible(session, elsewhere) == set()
    finally:
        session.close()


def test_an_empty_scope_set_compiles_to_false(world: World) -> None:
    session = world.session()
    try:
        predicate = predicate_for(
            plans.STUDENT_RELATIONSHIPS, db=session,
            principal=actor(), permission=READ,
        )
        assert "false" in str(predicate).lower()
    finally:
        session.close()


def test_a_scope_kind_the_resource_never_learned_reaches_nothing(
    world: World
) -> None:
    """`subject` is not in the student plan, and that is the whole point.

    "May edit the Chemistry syllabus" must not become "may read every chemistry
    student's record". A scope kind absent from a plan contributes no rows
    rather than no restriction.
    """
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.subject, (_uuid.uuid4(),)))
        assert visible(session, holder) == set()
    finally:
        session.close()


# --- each scope kind reaches exactly what it names -------------------------


def test_institution_wide_scope_sees_everybody(world: World) -> None:
    session = world.session()
    try:
        assert visible(session, actor((READ, ScopeKind.tenant, ()))) == EVERYBODY
    finally:
        session.close()


def test_class_group_scope(world: World) -> None:
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.klass, (world.class_1a,)))
        assert visible(session, holder) == {"Bio One A", "Bio Two A"}
    finally:
        session.close()


def test_level_scope_reaches_both_classes_of_that_level(world: World) -> None:
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.level, (world.level_biology,)))
        assert visible(session, holder) == {
            "Bio One A", "Bio Two A", "Bio Three B", "Self Student"
        }
    finally:
        session.close()


def test_programme_scope(world: World) -> None:
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.programme, (world.prog_physics,)))
        assert visible(session, holder) == {"Phys One"}
    finally:
        session.close()


def test_cohort_scope(world: World) -> None:
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.cohort, (world.cohort_2026,)))
        assert visible(session, holder) == {"Bio One A", "Bio Two A"}
    finally:
        session.close()


def test_department_scope(world: World) -> None:
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.department, (world.dept_biology,)))
        assert visible(session, holder) == {
            "Bio One A", "Bio Two A", "Bio Three B", "Self Student"
        }
    finally:
        session.close()


def test_a_faculty_scope_reaches_the_departments_inside_it(world: World) -> None:
    """The nested case. A head of faculty who could not see its departments
    holds a scope that means nothing, so the walk is recursive — and it stops
    at the faculty boundary rather than spilling into the other one."""
    session = world.session()
    try:
        science = actor((READ, ScopeKind.department, (world.faculty_science,)))
        assert visible(session, science) == {
            "Bio One A", "Bio Two A", "Bio Three B", "Self Student", "Phys One"
        }
        assert "Hist One" not in visible(session, science)

        arts = actor((READ, ScopeKind.academic_unit, (world.faculty_arts,)))
        assert visible(session, arts) == {"Hist One"}
    finally:
        session.close()


def test_taught_by_self(world: World) -> None:
    """The teacher is allocated to 1A and reaches 1A. Not 1B, not the faculty."""
    session = world.session()
    try:
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        assert visible(session, teacher) == {"Bio One A", "Bio Two A"}
    finally:
        session.close()


def test_own_children(world: World) -> None:
    session = world.session()
    try:
        guardian = actor(
            (READ, ScopeKind.own_children, ()), user_id=world.guardian_user
        )
        assert visible(session, guardian) == {"Bio Three B"}
    finally:
        session.close()


def test_self_only(world: World) -> None:
    session = world.session()
    try:
        student = actor((READ, ScopeKind.self_only, ()), user_id=world.student_user)
        assert visible(session, student) == {"Self Student"}
    finally:
        session.close()


def test_a_student_with_no_placement_is_reached_by_no_structural_scope(
    world: World
) -> None:
    """The case a scope model quietly gets wrong in either direction.

    An applicant with no enrolment belongs to no class, level, programme or
    department — so a departmental scope must not reach them, and an
    institution-wide one must.
    """
    session = world.session()
    try:
        for kind, ids in (
            (ScopeKind.klass, (world.class_1a,)),
            (ScopeKind.level, (world.level_biology,)),
            (ScopeKind.programme, (world.prog_biology,)),
            (ScopeKind.department, (world.faculty_science,)),
        ):
            assert "Unplaced Applicant" not in visible(
                session, actor((READ, kind, ids))
            ), kind
        assert "Unplaced Applicant" in visible(
            session, actor((READ, ScopeKind.tenant, ()))
        )
    finally:
        session.close()


def test_a_scope_naming_something_that_does_not_exist_reaches_nothing(
    world: World
) -> None:
    """An empty result, not an error and not everything."""
    session = world.session()
    try:
        holder = actor((READ, ScopeKind.klass, (_uuid.uuid4(),)))
        assert visible(session, holder) == set()
    finally:
        session.close()


def test_a_scope_over_an_ended_placement_no_longer_reaches_the_student(
    world: World
) -> None:
    """Reach follows the *open* placement. A transfer moves it, immediately."""
    session = world.session()
    try:
        person = people.record_person(session, full_name="Moves Away")
        student = people.register_student(session, person, reference="REF-MOVES")
        placement = people.admit(
            session, student, on=date(2026, 9, 1),
            placement=Placement(level_id=world.level_biology,
                                class_group_id=world.class_1a,
                                programme_id=world.prog_biology),
        )
        people.enrol(session, placement, on=date(2026, 9, 1))
        session.commit()

        in_1a = actor((READ, ScopeKind.klass, (world.class_1a,)))
        in_h1a = actor((READ, ScopeKind.klass, (world.class_h1a,)))
        assert "Moves Away" in visible(session, in_1a)
        assert "Moves Away" not in visible(session, in_h1a)

        people.transfer(
            session, placement,
            to=Placement(level_id=world.level_history,
                         class_group_id=world.class_h1a,
                         programme_id=world.prog_history),
            on=date(2027, 1, 10),
        )
        session.commit()

        assert "Moves Away" not in visible(session, in_1a), (
            "a teacher still reaches a student who left their class"
        )
        assert "Moves Away" in visible(session, in_h1a)
    finally:
        session.close()


# --- composition ------------------------------------------------------------


def test_two_scopes_for_one_permission_union(world: World) -> None:
    """A head of two departments reaches both. The established semantic."""
    session = world.session()
    try:
        both = Principal(
            user_id=_uuid.uuid4(), membership_id=_uuid.uuid4(),
            tenant_id=_uuid.uuid4(), permissions=frozenset({READ}),
            grants=(
                Grant(frozenset({READ}), ScopeKind.department.value,
                      (world.dept_physics,)),
                Grant(frozenset({READ}), ScopeKind.department.value,
                      (world.dept_history,)),
            ),
            session_id=_uuid.uuid4(),
            authenticated_at=datetime.now(UTC).timestamp(),
        )
        seen = visible(session, both)
        # Stated as the property rather than as an exact roster, so a later test
        # adding somebody to one of these departments does not make this one
        # fail for a reason that has nothing to do with what it checks.
        assert {"Phys One", "Hist One"} <= seen
        assert not seen & {"Bio One A", "Bio Two A", "Bio Three B", "Self Student"}
    finally:
        session.close()


def test_a_broad_scope_on_one_permission_does_not_widen_another(
    world: World
) -> None:
    """The defect this design exists to prevent, asserted directly.

    A teacher who is also the communications officer holds a school-wide scope
    — for announcements. Reading that as "this person is unrestricted" would
    hand them every student record in the institution on the strength of a
    permission to write notices. Before scopes were resolved per permission,
    that is exactly what happened.
    """
    session = world.session()
    try:
        both_hats = Principal(
            user_id=_uuid.uuid4(), membership_id=world.teacher_membership,
            tenant_id=_uuid.uuid4(),
            permissions=frozenset({READ, "communication.announcement.publish"}),
            grants=(
                Grant(frozenset({READ}), ScopeKind.taught_by_self.value, ()),
                Grant(frozenset({"communication.announcement.publish"}),
                      ScopeKind.tenant.value, ()),
            ),
            session_id=_uuid.uuid4(),
            authenticated_at=datetime.now(UTC).timestamp(),
        )
        assert visible(session, both_hats) == {"Bio One A", "Bio Two A"}, (
            "an unrelated school-wide grant widened the student scope"
        )
        # And the announcement permission genuinely is school-wide, so the
        # separation is doing work rather than simply denying everything.
        wide = scopes_for(both_hats, "communication.announcement.publish")
        assert wide.is_unrestricted
        assert not scopes_for(both_hats, READ).is_unrestricted
    finally:
        session.close()


def test_manage_confers_read_and_carries_its_scope(world: World) -> None:
    """`people.student.manage` implies `read`, so its scope must apply to a read."""
    session = world.session()
    try:
        manager = actor(("people.student.manage", ScopeKind.klass, (world.class_1b,)))
        assert visible(session, manager) == {"Bio Three B", "Self Student"}
    finally:
        session.close()


def test_a_caller_filter_can_only_narrow(world: World) -> None:
    """Anything the caller adds is `AND`-ed on top and cannot loosen the scope."""
    session = world.session()
    try:
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        statement = scoped_select(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=session, principal=teacher, permission=READ,
        ).where(StudentRelationship.reference.like("REF-%"))
        rows = session.execute(statement).scalars().all()
        assert {session.get(Person, r.person_id).full_name for r in rows} == {
            "Bio One A", "Bio Two A"
        }
    finally:
        session.close()


def test_a_plan_that_tries_to_widen_is_refused(world: World) -> None:
    """A clause narrows. Only an explicit tenant scope removes the restriction."""
    from sqlalchemy import true

    from app.modules.authz.predicates import ScopePlan, compile_scope_set

    reckless = ScopePlan(
        resource="reckless",
        clauses={ScopeKind.klass: lambda _c: true()},
    )
    session = world.session()
    try:
        with pytest.raises(ScopePlanError):
            compile_scope_set(
                reckless,
                ScopeSet.of([Scope(ScopeKind.klass, frozenset({_uuid.uuid4()}))]),
                db=session,
                principal=actor(),
            )
    finally:
        session.close()


# --- leakage ----------------------------------------------------------------


def test_a_count_reveals_only_what_the_caller_may_read(world: World) -> None:
    """The endpoint that quietly answers the question the list refused to.

    A count over the table tells an unauthorized caller exactly how many records
    they cannot see, which is most of what they wanted to know.
    """
    session = world.session()
    try:
        everything = session.execute(
            select(func.count()).select_from(StudentRelationship)
        ).scalar_one()
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        mine = scoped_count(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=session, principal=teacher, permission=READ,
        )
        assert mine == 2
        assert mine < everything, "the fixture no longer proves anything"

        assert (
            scoped_count(
                StudentRelationship, plans.STUDENT_RELATIONSHIPS,
                db=session, principal=None, permission=READ,
            )
            == 0
        )
    finally:
        session.close()


def test_an_aggregate_cannot_be_used_to_probe(world: World) -> None:
    """The same predicate, under a different aggregate.

    A minimum, a maximum or an average over an unscoped set is an oracle with
    better manners than a list. `scoped_select` composes, so an aggregate built
    on it inherits the boundary.
    """
    session = world.session()
    try:
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        statement = scoped_select(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=session, principal=teacher, permission=READ,
        ).with_only_columns(func.min(StudentRelationship.reference))
        assert session.execute(statement).scalar_one() == "REF-Bio On"

        empty = scoped_select(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=session, principal=None, permission=READ,
        ).with_only_columns(func.min(StudentRelationship.reference))
        assert session.execute(empty).scalar_one() is None
    finally:
        session.close()


def test_fetching_an_out_of_scope_id_is_indistinguishable_from_a_missing_one(
    world: World
) -> None:
    """`None` for both, so the response cannot confirm the record exists."""
    session = world.session()
    try:
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        real_but_elsewhere = world.students["Hist One"]
        invented = _uuid.uuid4()
        for identifier in (real_but_elsewhere, invented):
            assert (
                scoped_get(
                    StudentRelationship, identifier, plans.STUDENT_RELATIONSHIPS,
                    db=session, principal=teacher, permission=READ,
                )
                is None
            )
    finally:
        session.close()


def test_pagination_cannot_walk_past_the_scope(world: World) -> None:
    """Paging is applied to an already-narrowed statement, not to the table."""
    session = world.session()
    try:
        teacher = actor(
            (READ, ScopeKind.taught_by_self, ()),
            membership_id=world.teacher_membership,
        )
        statement = scoped_select(
            StudentRelationship, plans.STUDENT_RELATIONSHIPS,
            db=session, principal=teacher, permission=READ,
        ).order_by(StudentRelationship.reference)
        seen: list[str] = []
        for offset in range(0, 20, 1):
            rows = session.execute(statement.limit(1).offset(offset)).scalars().all()
            if not rows:
                break
            seen.append(session.get(Person, rows[0].person_id).full_name)
        assert set(seen) == {"Bio One A", "Bio Two A"}
    finally:
        session.close()


# --- the tenant boundary is still the tenant boundary ----------------------


def test_a_scope_naming_another_schools_class_reaches_nothing() -> None:
    """A valid permission in School A is not authorization in School B.

    Two layers refuse this independently. The scope names an id the querying
    tenant cannot see, so the subquery is empty; and row-level security would
    have excluded the rows even if it were not.
    """
    other = _provision("scope-other")
    built = _build(other)

    victim = _provision("scope-victim")
    victim_built = _build(victim)

    session = session_for(victim.tenant_id)
    try:
        # The attacker holds a legitimate class scope — for a class in the
        # *other* school. Same shape of id, same permission, no reach.
        trespasser = actor((READ, ScopeKind.klass, (built["1a"],)))
        assert visible(session, trespasser) == set()

        # And the same principal with the victim's own class id does reach it,
        # so the refusal above is about the tenant and not about the query
        # being broken.
        legitimate = actor((READ, ScopeKind.klass, (victim_built["1a"],)))
        assert visible(session, legitimate) == {"Bio One A", "Bio Two A"}
    finally:
        session.close()


def test_a_guardian_at_one_school_reaches_no_children_at_another(
    world: World
) -> None:
    """The guardian's identity is global; their guardianships are not.

    `own_children` resolves through *this* institution's record of the person,
    so the same human at a second school reaches nothing there — which is
    ADR-027's separation doing authorization work.
    """
    elsewhere = _provision("scope-elsewhere")
    _build(elsewhere)
    session = session_for(elsewhere.tenant_id)
    try:
        guardian = actor(
            (READ, ScopeKind.own_children, ()), user_id=world.guardian_user
        )
        assert visible(session, guardian) == set()
    finally:
        session.close()


# --- background jobs and elevation -----------------------------------------


def test_a_job_without_elevation_reads_nothing(world: World) -> None:
    """Visible on the first run, rather than invisible forever."""
    session = world.session()
    try:
        assert (
            scoped_count(
                StudentRelationship, plans.STUDENT_RELATIONSHIPS,
                db=session, principal=None, permission=READ,
            )
            == 0
        )
    finally:
        session.close()


def test_elevation_is_explicit_tenant_bound_and_audited(world: World) -> None:
    from app.core.context import tenant_context
    from app.modules.audit.models import SecurityEvent, SecurityEventKind

    session = world.session()
    try:
        with tenant_context(world.school.tenant_id), system_access(
            reason="nightly attendance digest"
        ):
            assert EVERYBODY <= visible(session, None)
        # And the elevation ends with the block.
        assert visible(session, None) == set()
    finally:
        session.close()

    platform = session_for(None)
    try:
        events = platform.execute(
            select(SecurityEvent).where(
                SecurityEventKind.system_access == SecurityEvent.kind,
                SecurityEvent.tenant_id == world.school.tenant_id,
            )
        ).scalars().all()
        assert events, "elevated access left no record"
        assert any(
            "nightly attendance digest" in str(e.detail.values()) for e in events
        )
    finally:
        platform.close()


def test_elevation_without_a_tenant_is_refused() -> None:
    """Elevation widens reach within one school. It is not a way across all of them."""
    from app.core.context import tenant_context

    with tenant_context(None), pytest.raises(SystemAccessRefused):
        with system_access(reason="anything"):
            pass


def test_elevation_without_a_reason_is_refused(world: World) -> None:
    from app.core.context import tenant_context

    with tenant_context(world.school.tenant_id), pytest.raises(SystemAccessRefused):
        with system_access(reason="   "):
            pass


# --- through HTTP, which is how it will actually be attacked ---------------


def _sign_in(client: TestClient, school: TenantFixture, email: str) -> str:
    from app.tests.conftest import OWNER_PASSWORD

    response = client.post(
        "/api/v1/auth/sign-in",
        json={"email": email, "password": OWNER_PASSWORD},
        headers={"host": school.hostname},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_the_list_endpoint_is_scoped_and_so_is_its_total(world: World) -> None:
    """The whole chain: token, grants, per-permission scopes, predicate, SQL."""
    from app.modules.authz import service as authz
    from app.modules.authz.scopes import Scope as ScopeValue

    session = world.session()
    try:
        # The owner's grant is school-wide; narrow a second membership instead.
        from app.modules.identity.models import Membership, MembershipStatus, User

        user = User(
            email=f"narrow-{_uuid.uuid4().hex[:6]}@scope.test",
            full_name="Narrow Reader",
        )
        from app.core.security import hash_password

        user.password_hash = hash_password("a-perfectly-fine-passphrase")
        from app.modules.identity.models import UserStatus

        user.status = UserStatus.active
        session.add(user)
        session.flush()
        membership = Membership(
            user_id=user.id, status=MembershipStatus.active, display_name="Narrow"
        )
        session.add(membership)
        session.flush()
        authz.grant_role(
            session,
            membership_id=membership.id,
            role_key="teacher",
            scope=ScopeValue(ScopeKind.klass, frozenset({world.class_1a})),
        )
        session.commit()
        email = user.email
    finally:
        session.close()

    with TestClient(app) as client:
        token = _sign_in(client, world.school, email)
        headers = {"host": world.school.hostname, "authorization": f"Bearer {token}"}

        listing = client.get("/api/v1/students", headers=headers)
        assert listing.status_code == 200, listing.text
        body = listing.json()
        assert {item["full_name"] for item in body["items"]} == {
            "Bio One A", "Bio Two A"
        }
        assert body["total"] == 2, "the page total counted rows the caller cannot read"

        # A student in another class: 404, identical to an id that never existed.
        out_of_scope = client.get(
            f"/api/v1/students/{world.students['Hist One']}", headers=headers
        )
        invented = client.get(
            f"/api/v1/students/{_uuid.uuid4()}", headers=headers
        )
        assert out_of_scope.status_code == 404
        assert invented.status_code == 404
        assert out_of_scope.json() == invented.json(), (
            "the two responses differ, so the difference is the answer"
        )

        # Searching for somebody outside the scope finds nothing and says so
        # exactly as it would for a name nobody has.
        real_elsewhere = client.get(
            "/api/v1/students", params={"search": "Hist"}, headers=headers
        ).json()
        nonsense = client.get(
            "/api/v1/students", params={"search": "Zzzzqqq"}, headers=headers
        ).json()
        assert real_elsewhere["items"] == [] and real_elsewhere["total"] == 0
        assert nonsense["items"] == [] and nonsense["total"] == 0

        # And paging past the end reveals nothing beyond it.
        beyond = client.get(
            "/api/v1/students", params={"offset": 2}, headers=headers
        ).json()
        assert beyond["items"] == []
        assert beyond["total"] == 2


def test_the_list_endpoint_refuses_an_unbounded_page(world: World) -> None:
    """An unbounded page size turns any list into an export."""
    with TestClient(app) as client:
        token = _sign_in(client, world.school, f"owner@{world.school.tenant.slug}.test")
        headers = {"host": world.school.hostname, "authorization": f"Bearer {token}"}
        assert client.get(
            "/api/v1/students", params={"limit": 10_000}, headers=headers
        ).status_code == 422


def test_the_owner_sees_the_whole_school_through_http(world: World) -> None:
    """The other end of the range, so the scope is not simply denying everything."""
    with TestClient(app) as client:
        token = _sign_in(client, world.school, f"owner@{world.school.tenant.slug}.test")
        headers = {"host": world.school.hostname, "authorization": f"Bearer {token}"}
        body = client.get(
            "/api/v1/students", params={"limit": 100}, headers=headers
        ).json()
        assert body["total"] >= len(EVERYBODY)
        assert "Hist One" in {item["full_name"] for item in body["items"]}


def test_students_of_one_school_are_invisible_at_another_over_http(
    world: World
) -> None:
    """A genuinely valid token, a genuinely held permission, another school's id."""
    other = _provision("scope-http-other")
    built = _build(other)

    with TestClient(app) as client:
        token = _sign_in(client, world.school, f"owner@{world.school.tenant.slug}.test")
        headers = {"host": world.school.hostname, "authorization": f"Bearer {token}"}
        response = client.get(
            f"/api/v1/students/{built['students']['Bio One A']}", headers=headers
        )
        assert response.status_code == 404
