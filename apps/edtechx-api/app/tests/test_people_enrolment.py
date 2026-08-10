"""People and enrolment, proved against all nine institutions.

`EDIRASX_EDITORIAL_BIBLE.md` §8 promises one engine for the whole education
continuum. The academic structure suite proves that the *shape* of an
institution is configuration. This one asks the harder question: can the same
people-and-enrolment model carry a four-year-old in a class group, a doctoral
researcher on a programme with no class at all, and an apprentice on a rolling
intake with no academic year — through one code path, with no branch naming any
of them?

Four claims are tested:

  * **Identity, person and relationship are three things.** A person may have no
    login. One person may be a member of staff, a guardian and a learner at
    once, as one record. The same human at two institutions is one identity and
    two entirely separate person records.

  * **Enrolment is history.** Every placement is a row with a beginning and an
    end. A transfer, a promotion, a withdrawal and a readmission each *add*, and
    the previous row keeps the class group it always had. There is no
    `student.class_id` to overwrite — and a structural test asserts that no
    relationship table has grown one.

  * **Every academic layer stays optional.** The layers an institution does not
    use are null, not invented.

  * **None of it can be rewritten.** The ledger is append-only at the database,
    not by convention, and an enrolment cannot be deleted at all.
"""

from __future__ import annotations

import ast
import pathlib
import uuid as _uuid
from datetime import date

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from app.modules.academics.models import (
    AcademicYear,
    ClassGroup,
    Level,
    ProgressionOutcome,
    ProgressionRule,
)
from app.modules.academics.progression import compute_metrics, evaluate
from app.modules.academics.structure import Cohort, Programme, Qualification
from app.modules.people import service
from app.modules.people.enrolment import (
    Enrolment,
    EnrolmentEvent,
    EnrolmentEventKind,
    EnrolmentOutcome,
    EnrolmentStatus,
    QualificationAward,
)
from app.modules.people.models import (
    GuardianRelationship,
    Person,
    RelationshipStatus,
    StaffRelationship,
    StudentRelationship,
)
from app.modules.people.service import Placement
from app.tests.conftest import OWNER_PASSWORD, TenantFixture, requires_db, session_for
from app.tests.test_universal_education import (
    BRITISH,
    INSTITUTIONS,
    SHAPES,
    configure,
    configure_institution,
)

pytestmark = requires_db


# --- nine institutions, built once for the module -------------------------


def _provision(slug_prefix: str) -> TenantFixture:
    from app.modules.authz.models import Role
    from app.modules.identity.models import Membership, User
    from app.modules.tenancy.models import Tenant
    from app.modules.tenancy.service import provision_school

    slug = f"{slug_prefix}-{_uuid.uuid4().hex[:8]}"
    result = provision_school(
        slug=slug,
        name=slug_prefix.title(),
        owner_email=f"owner@{slug}.test",
        owner_name="Owner",
        owner_password=OWNER_PASSWORD,
        base_domain="edtechx.localhost",
    )
    scoped = session_for(result.tenant_id)
    try:
        return TenantFixture(
            scoped.get(Tenant, result.tenant_id),
            scoped.get(User, result.owner_user_id),
            scoped.get(Membership, result.owner_membership_id),
            scoped.execute(select(Role).where(Role.key == "owner")).scalar_one(),
        )
    finally:
        scoped.close()


@pytest.fixture(scope="module")
def nine() -> dict[str, TenantFixture]:
    """All nine configured institutions, in one database.

    Built once for the module because provisioning nine schools per test would
    make the suite too slow to run often — and a suite that is not run is not a
    guarantee. Every test below creates its own people, so nothing leaks
    between them.
    """
    built: dict[str, TenantFixture] = {}
    for shape in SHAPES:
        fixture = _provision(shape.key)
        configure(fixture, shape)
        built[f"school:{shape.key}"] = fixture
    for shape in INSTITUTIONS:
        fixture = _provision(shape.key)
        configure_institution(fixture, shape)
        built[f"inst:{shape.key}"] = fixture
    return built


ALL_KEYS = [f"school:{s.key}" for s in SHAPES] + [f"inst:{i.key}" for i in INSTITUTIONS]


def placement_from_configuration(db: Session) -> Placement:
    """Build a placement out of whatever layers this institution actually has.

    Deliberately one function for all nine, and deliberately ignorant: it asks
    the database what exists and uses it. An institution with no programme
    produces a placement with no programme, and nothing anywhere has to know
    which kind of institution this is.
    """
    level = db.execute(select(Level).order_by(Level.sequence)).scalars().first()
    year = db.execute(select(AcademicYear)).scalars().first()
    class_group = None
    cohort = None
    if level is not None:
        class_group = (
            db.execute(select(ClassGroup).where(ClassGroup.level_id == level.id))
            .scalars()
            .first()
        )
        if level.programme_id is not None:
            cohort = (
                db.execute(select(Cohort).where(Cohort.programme_id == level.programme_id))
                .scalars()
                .first()
            )
    return Placement(
        academic_year_id=year.id if year else None,
        programme_id=level.programme_id if level else None,
        level_id=level.id if level else None,
        class_group_id=class_group.id if class_group else None,
        cohort_id=cohort.id if cohort else None,
    )


def admit_and_enrol(
    db: Session,
    *,
    full_name: str,
    on: date = date(2026, 9, 1),
    reference: str | None = None,
    kind_label: str = "Student",
    **person_fields: object,
) -> tuple[Person, StudentRelationship, Enrolment]:
    """The whole journey from stranger to enrolled, in one path for nine institutions."""
    person = service.record_person(db, full_name=full_name, **person_fields)
    student = service.register_student(
        db, person, reference=reference, kind_label=kind_label
    )
    enrolment = service.admit(
        db, student, on=on, placement=placement_from_configuration(db)
    )
    service.enrol(db, enrolment, on=on)
    db.commit()
    return person, student, enrolment


# --- the sweep: one path, nine institutions -------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_a_person_can_be_enrolled_in_every_institution(
    nine: dict[str, TenantFixture], key: str
) -> None:
    """The claim, stated plainly.

    A nursery child, an adult literacy learner, an apprentice, an
    undergraduate and a doctoral researcher all reach an active enrolment
    through the same three calls.
    """
    session = nine[key].session()
    try:
        _person, student, enrolment = admit_and_enrol(
            session, full_name=f"Enrolled Learner {key}"
        )
        assert enrolment.status is EnrolmentStatus.active, key
        assert enrolment.is_open, key
        assert enrolment.outcome is None, key
        assert student.status is RelationshipStatus.active, key
        # Admission and enrolment are two events, not one.
        kinds = [e.kind for e in service.history(session, student)]
        assert kinds == [
            EnrolmentEventKind.admitted,
            EnrolmentEventKind.enrolled,
        ], f"{key}: unexpected ledger {kinds}"
    finally:
        session.close()


def test_the_layers_an_institution_does_not_use_stay_null(
    nine: dict[str, TenantFixture]
) -> None:
    """Absent, not invented.

    The schools place a learner in a class group and have no programme. The
    programme-based institutions place one on a programme and have no class
    group. Neither is a special case; both are the same row with different
    columns filled.
    """
    populated: dict[str, set[str]] = {}
    for key, institution in nine.items():
        session = institution.session()
        try:
            _p, _s, enrolment = admit_and_enrol(
                session, full_name=f"Layer Probe {key}"
            )
            populated[key] = {
                name
                for name in (
                    "academic_year_id",
                    "programme_id",
                    "level_id",
                    "class_group_id",
                    "cohort_id",
                )
                if getattr(enrolment, name) is not None
            }
        finally:
            session.close()

    for key in (f"school:{s.key}" for s in SHAPES):
        assert "class_group_id" in populated[key], f"{key} lost its class group"
        assert "programme_id" not in populated[key], (
            f"{key} invented a programme it never configured"
        )
    for key in (f"inst:{i.key}" for i in INSTITUTIONS):
        assert "programme_id" in populated[key], f"{key} lost its programme"
        assert "class_group_id" not in populated[key], (
            f"{key} invented a class group it never configured"
        )
    # And one institution uses the cohort layer while another, configured with a
    # cohort on a different programme, correctly does not.
    assert "cohort_id" in populated["inst:credit-university"]
    assert "cohort_id" not in populated["inst:ladder"]


# --- identity is not a person, and a person is not a relationship ---------


def test_a_person_needs_no_identity_at_all(nine: dict[str, TenantFixture]) -> None:
    """A four-year-old has no email address, and must still exist."""
    session = nine["school:british"].session()
    try:
        person, _s, enrolment = admit_and_enrol(session, full_name="A Very Young Child")
        assert person.user_id is None
        assert person.email is None
        assert enrolment.status is EnrolmentStatus.active
    finally:
        session.close()


def test_a_person_may_hold_three_relationships_without_being_duplicated(
    nine: dict[str, TenantFixture]
) -> None:
    """The teacher whose child attends, who is also studying for a further award.

    One `Person` row. Three relationships. A model that made "student" a kind of
    user would need three accounts and would then have to reconcile them.
    """
    session = nine["school:british"].session()
    try:
        adult = service.record_person(session, full_name="Amina Yusuf")
        child = service.record_person(session, full_name="Bilal Yusuf")

        staff = service.register_staff(
            session, adult, kind_label="Teacher", is_teaching=True, reference="EMP-1"
        )
        learner = service.register_student(session, adult, kind_label="Learner")
        guardian_link = service.link_guardian(
            session, guardian=adult, student=child, relationship_label="Mother"
        )
        service.register_student(session, child, reference="ADM-1")
        session.commit()

        held = service.relationships_of(session, adult)
        assert len(held["student"]) == 1
        assert len(held["staff"]) == 1
        assert len(held["guardian_of"]) == 1
        assert held["guardians"] == []

        # One person, not three.
        matching = session.execute(
            select(Person).where(Person.full_name == "Amina Yusuf")
        ).scalars().all()
        assert len(matching) == 1
        assert {staff.person_id, learner.person_id, guardian_link.guardian_person_id} == {
            adult.id
        }
    finally:
        session.close()


def test_a_guardian_is_a_person_and_the_label_is_free_text(
    nine: dict[str, TenantFixture]
) -> None:
    """Family structures are not a closed list, and none of these is a special case."""
    session = nine["school:nigerian"].session()
    try:
        child = service.record_person(session, full_name="Chidi Okafor")
        service.register_student(session, child)
        for sequence, (name, label) in enumerate(
            [
                ("Ngozi Okafor", "Mother"),
                ("Emeka Okafor", "Uncle"),
                ("St. Michael's Trust", "Sponsor"),
            ]
        ):
            guardian = service.record_person(session, full_name=name)
            service.link_guardian(
                session,
                guardian=guardian,
                student=child,
                relationship_label=label,
                sequence=sequence,
                is_primary_contact=sequence == 0,
                is_financially_responsible=label == "Sponsor",
            )
        session.commit()

        links = service.relationships_of(session, child)["guardians"]
        assert {link.relationship_label for link in links} == {
            "Mother",
            "Uncle",
            "Sponsor",
        }
        payer = next(link for link in links if link.is_financially_responsible)
        first_contact = next(link for link in links if link.is_primary_contact)
        # Who pays and who is called first are separate facts.
        assert payer.id != first_contact.id
        # And none of the guardians needed an account.
        for link in links:
            guardian = session.get(Person, link.guardian_person_id)
            assert guardian is not None and guardian.user_id is None
    finally:
        session.close()


def test_the_same_identity_is_a_separate_person_at_each_institution(
    nine: dict[str, TenantFixture]
) -> None:
    """One human, one credential, two institutions that cannot see each other.

    The person records are entirely separate, and neither institution learns
    that the other exists.
    """
    from app.modules.identity.models import User

    british = nine["school:british"]
    american = nine["school:american"]

    platform = session_for(british.tenant_id)
    try:
        shared = User(email=f"dual-{_uuid.uuid4().hex[:8]}@example.test",
                      full_name="Dual Institution Teacher")
        platform.add(shared)
        platform.commit()
        shared_id = shared.id
    finally:
        platform.close()

    for institution, note in ((british, "British record"), (american, "American record")):
        session = institution.session()
        try:
            person = service.record_person(
                session, full_name="Dual Institution Teacher", user_id=shared_id,
                custom={"note": note},
            )
            service.register_staff(session, person, kind_label="Teacher", is_teaching=True)
            session.commit()
        finally:
            session.close()

    session = british.session()
    try:
        visible = session.execute(
            select(Person).where(Person.user_id == shared_id)
        ).scalars().all()
        assert len(visible) == 1, "one institution can see the other's person record"
        assert visible[0].custom["note"] == "British record"
    finally:
        session.close()


# --- enrolment is history -------------------------------------------------


def test_a_transfer_leaves_the_previous_placement_exactly_as_it_was(
    nine: dict[str, TenantFixture]
) -> None:
    """The whole reason the model is shaped this way.

    Ask the closed row where the child was last term and it still knows.
    """
    school = nine["school:british"]
    session = school.session()
    try:
        _p, student, first = admit_and_enrol(session, full_name="Transferring Pupil")
        original_class = first.class_group_id
        original_level = first.level_id

        year = session.execute(select(AcademicYear)).scalars().one()
        other_level = (
            session.execute(select(Level).order_by(Level.sequence)).scalars().all()[1]
        )
        second_group = ClassGroup(
            code="b", name="B", level_id=other_level.id, academic_year_id=year.id
        )
        session.add(second_group)
        session.flush()

        replacement = service.transfer(
            session,
            first,
            to=Placement(level_id=other_level.id, class_group_id=second_group.id),
            on=date(2027, 1, 8),
            reason="Moved to the other form",
        )
        session.commit()

        session.refresh(first)
        assert first.class_group_id == original_class, "history was overwritten"
        assert first.level_id == original_level, "history was overwritten"
        assert first.ended_on == date(2027, 1, 8)
        assert first.outcome is EnrolmentOutcome.transferred

        assert replacement.class_group_id == second_group.id
        assert replacement.previous_enrolment_id == first.id
        assert replacement.is_open

        history = service.enrolments_for(session, student)
        assert len(history) == 2
        # The reason survives, on both sides of the move.
        events = {e.kind for e in service.history(session, student)}
        assert EnrolmentEventKind.transferred in events
        assert EnrolmentEventKind.placed in events
    finally:
        session.close()


def test_where_was_she_in_march(nine: dict[str, TenantFixture]) -> None:
    """The question a mutable pointer cannot answer.

    Two placements, one closed in January. Asking about October returns the
    first; asking about March returns the second.
    """
    session = nine["school:british"].session()
    try:
        _p, student, first = admit_and_enrol(
            session, full_name="Asked About Later", on=date(2026, 9, 1)
        )
        year = session.execute(select(AcademicYear)).scalars().one()
        levels = session.execute(select(Level).order_by(Level.sequence)).scalars().all()
        group = ClassGroup(
            code=f"m-{_uuid.uuid4().hex[:4]}", name="M",
            level_id=levels[1].id, academic_year_id=year.id,
        )
        session.add(group)
        session.flush()
        second = service.transfer(
            session, first,
            to=Placement(level_id=levels[1].id, class_group_id=group.id),
            on=date(2027, 1, 10),
        )
        session.commit()

        october = service.enrolment_on(session, student, date(2026, 10, 15))
        march = service.enrolment_on(session, student, date(2027, 3, 15))
        assert [e.id for e in october] == [first.id]
        assert [e.id for e in march] == [second.id]
    finally:
        session.close()


def test_progression_opens_the_next_placement_rather_than_editing_this_one(
    nine: dict[str, TenantFixture]
) -> None:
    """A promotion decided by the institution's own rule, recorded as history.

    The rule comes from the configured row, the metrics from the student's
    results, and the reasoning is copied into the ledger so it survives the rule
    being rewritten next year.
    """
    from app.tests.test_universal_education import _results

    session = nine["school:british"].session()
    try:
        _p, student, first = admit_and_enrol(session, full_name="Promoted Pupil")
        rule = session.execute(select(ProgressionRule)).scalars().one()
        level = session.get(Level, first.level_id)
        assert level is not None and level.next_level_id is not None

        metrics = compute_metrics(
            _results(BRITISH, scores=[72, 61, 58, 40]), attendance_rate=0.96
        )
        decision = evaluate(
            rule.conditions,
            metrics,
            on_pass=rule.on_pass,
            on_fail=rule.on_fail,
            rule_code=rule.code,
        )
        assert decision.outcome is ProgressionOutcome.promote

        year = session.execute(select(AcademicYear)).scalars().one()
        next_group = ClassGroup(
            code=f"p-{_uuid.uuid4().hex[:4]}", name="Next",
            level_id=level.next_level_id, academic_year_id=year.id,
        )
        session.add(next_group)
        session.flush()

        following = service.progress(
            session,
            first,
            decision,
            on=date(2027, 7, 20),
            to=Placement(level_id=level.next_level_id, class_group_id=next_group.id),
        )
        session.commit()

        session.refresh(first)
        assert first.outcome is EnrolmentOutcome.progressed
        assert first.level_id == level.id, "the old placement was edited"
        assert following is not None and following.level_id == level.next_level_id

        event = next(
            e
            for e in service.history(session, student)
            if e.kind is EnrolmentEventKind.progressed
        )
        assert event.detail["rule"] == rule.code
        assert any("attendance rate" in line for line in event.detail["checks"]), (
            "the ledger does not explain the decision"
        )
    finally:
        session.close()


def test_a_research_student_completes_with_no_marks_anywhere(
    nine: dict[str, TenantFixture]
) -> None:
    """Milestones and two human approvals — and the same two functions."""
    session = nine["inst:research"].session()
    try:
        _p, student, enrolment = admit_and_enrol(
            session, full_name="Doctoral Candidate", kind_label="Researcher"
        )
        rule = session.execute(select(ProgressionRule)).scalars().one()
        decision = evaluate(
            rule.conditions,
            compute_metrics(
                [],
                milestones_completed=4,
                milestones_required=4,
                supervisor_approved=True,
                board_approved=True,
            ),
            on_pass=ProgressionOutcome.graduate,
            rule_code=rule.code,
        )
        assert decision.passed

        following = service.progress(session, enrolment, decision, on=date(2029, 6, 30))
        session.commit()

        assert following is None, "a completed journey opened another placement"
        session.refresh(enrolment)
        assert enrolment.outcome is EnrolmentOutcome.completed
        assert student.status is RelationshipStatus.ended
    finally:
        session.close()


def test_withdrawal_and_readmission_leave_the_gap_visible(
    nine: dict[str, TenantFixture]
) -> None:
    """A returning student gets a new placement, not a reopened one."""
    session = nine["inst:non-credit"].session()
    try:
        _p, student, first = admit_and_enrol(
            session, full_name="Returning Learner", on=date(2026, 9, 1)
        )
        service.withdraw(
            session, first, on=date(2026, 11, 30), reason="Work commitments"
        )
        session.commit()
        assert student.status is RelationshipStatus.ended

        second = service.readmit(
            session,
            student,
            on=date(2027, 4, 12),
            placement=Placement(level_id=first.level_id, programme_id=first.programme_id),
        )
        session.commit()

        assert student.status is RelationshipStatus.active
        assert second.previous_enrolment_id == first.id
        session.refresh(first)
        assert first.ended_on == date(2026, 11, 30)
        assert first.outcome is EnrolmentOutcome.withdrawn

        # The months away are in the record rather than smoothed over.
        assert service.enrolment_on(session, student, date(2027, 1, 15)) == []
        kinds = [e.kind for e in service.history(session, student)]
        assert kinds[-2:] == [
            EnrolmentEventKind.withdrawn,
            EnrolmentEventKind.readmitted,
        ]
    finally:
        session.close()


def test_concurrent_enrolment_is_possible(nine: dict[str, TenantFixture]) -> None:
    """Two open placements at once is ordinary, not a corruption to be prevented.

    A joint programme, a course taken at a neighbouring institution, an
    apprentice on both a qualification and a short unit. A schema enforcing one
    open enrolment would make all three impossible.
    """
    session = nine["inst:ladder"].session()
    try:
        person = service.record_person(session, full_name="Joint Programme Student")
        student = service.register_student(session, person)
        programmes = session.execute(
            select(Programme).order_by(Programme.code)
        ).scalars().all()
        assert len(programmes) >= 2

        for programme in programmes[:2]:
            enrolment = service.admit(
                session,
                student,
                on=date(2026, 9, 1),
                placement=Placement(programme_id=programme.id),
            )
            service.enrol(session, enrolment, on=date(2026, 9, 1))
        session.commit()

        open_now = service.open_enrolments(session, student)
        assert len(open_now) == 2
        assert {e.programme_id for e in open_now} == {p.id for p in programmes[:2]}

        # Leaving one of them does not end the student's relationship.
        service.withdraw(
            session, open_now[0], on=date(2027, 2, 1), end_relationship=False
        )
        session.commit()
        assert student.status is RelationshipStatus.active
        assert len(service.open_enrolments(session, student)) == 1
    finally:
        session.close()


# --- awarding -------------------------------------------------------------


def test_the_award_is_the_institutions_own_qualification(
    nine: dict[str, TenantFixture]
) -> None:
    """A certificate of attendance and a research degree are the same row."""
    for key, classification in (
        ("inst:ladder", "Upper Division"),
        ("inst:non-credit", None),
        ("inst:vocational", "Competent"),
    ):
        session = nine[key].session()
        try:
            _p, student, enrolment = admit_and_enrol(
                session, full_name=f"Awarded Student {key}"
            )
            qualification = (
                session.execute(select(Qualification).order_by(Qualification.framework_level))
                .scalars()
                .first()
            )
            assert qualification is not None
            service.complete(session, enrolment, on=date(2029, 6, 1))
            granted = service.award(
                session,
                student,
                qualification_id=qualification.id,
                on=date(2029, 7, 15),
                enrolment=enrolment,
                classification_label=classification,
            )
            session.commit()

            assert granted.qualification_id == qualification.id
            assert granted.classification_label == classification
            kinds = [e.kind for e in service.history(session, student)]
            assert EnrolmentEventKind.completed in kinds
            assert EnrolmentEventKind.awarded in kinds
        finally:
            session.close()


def test_an_institution_that_awards_nothing_records_nothing(
    nine: dict[str, TenantFixture]
) -> None:
    """Completion and awarding are separate, so one may happen without the other."""
    session = nine["school:british"].session()
    try:
        _p, student, enrolment = admit_and_enrol(session, full_name="Leaving Pupil")
        service.complete(session, enrolment, on=date(2032, 7, 1))
        session.commit()
        awards = session.execute(select(QualificationAward)).scalars().all()
        assert awards == []
        assert student.status is RelationshipStatus.ended
    finally:
        session.close()


# --- the record cannot be rewritten ---------------------------------------


def test_the_ledger_rejects_update_and_delete(nine: dict[str, TenantFixture]) -> None:
    """Append-only at the database, not by convention.

    Proved by attempting exactly the two statements the design forbids, as the
    application role, which is the role every request runs as.
    """
    session = nine["school:american"].session()
    try:
        _p, student, _e = admit_and_enrol(session, full_name="Immutable History")
        event = service.history(session, student)[0]

        with pytest.raises(ProgrammingError):
            session.execute(
                text("UPDATE enrolment_events SET reason = 'rewritten' WHERE id = :id"),
                {"id": event.id},
            )
        session.rollback()

        with pytest.raises(ProgrammingError):
            session.execute(
                text("DELETE FROM enrolment_events WHERE id = :id"), {"id": event.id}
            )
        session.rollback()
    finally:
        session.close()


def test_an_enrolment_cannot_be_deleted(nine: dict[str, TenantFixture]) -> None:
    """A placement that happened cannot be made not to have happened.

    UPDATE remains, because a placement has to be closable and a mistake has to
    be correctable. DELETE does not.
    """
    session = nine["school:american"].session()
    try:
        _p, _s, enrolment = admit_and_enrol(session, full_name="Undeletable Placement")
        with pytest.raises(ProgrammingError):
            session.execute(
                text("DELETE FROM enrolments WHERE id = :id"), {"id": enrolment.id}
            )
        session.rollback()
    finally:
        session.close()


def test_a_closed_enrolment_cannot_be_closed_again(
    nine: dict[str, TenantFixture]
) -> None:
    session = nine["school:american"].session()
    try:
        _p, _s, enrolment = admit_and_enrol(session, full_name="Closed Once")
        service.withdraw(session, enrolment, on=date(2027, 3, 1))
        session.commit()
        with pytest.raises(service.EnrolmentError):
            service.withdraw(session, enrolment, on=date(2027, 4, 1))
    finally:
        session.rollback()
        session.close()


def test_an_enrolment_cannot_end_before_it_began(
    nine: dict[str, TenantFixture]
) -> None:
    """Refused by the service, and independently by the database."""
    session = nine["school:american"].session()
    try:
        _p, student, enrolment = admit_and_enrol(
            session, full_name="Backwards Dates", on=date(2026, 9, 1)
        )
        with pytest.raises(service.EnrolmentError):
            service.withdraw(session, enrolment, on=date(2026, 1, 1))
        session.rollback()

        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO enrolments "
                    "(id, tenant_id, student_relationship_id, status, started_on, "
                    " ended_on, outcome, custom, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :tenant, :student, 'ended', "
                    "'2026-09-01', '2026-01-01', 'withdrawn', '{}', now(), now())"
                ),
                {"tenant": student.tenant_id, "student": student.id},
            )
            session.flush()
    finally:
        session.rollback()
        session.close()


def test_a_closed_enrolment_must_say_why(nine: dict[str, TenantFixture]) -> None:
    """An end date with no outcome is an unexplained gap in somebody's record."""
    session = nine["school:american"].session()
    try:
        person = service.record_person(session, full_name="Unexplained Ending")
        student = service.register_student(session, person)
        session.commit()
        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO enrolments "
                    "(id, tenant_id, student_relationship_id, status, started_on, "
                    " ended_on, custom, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :tenant, :student, 'ended', "
                    "'2026-09-01', '2027-06-01', '{}', now(), now())"
                ),
                {"tenant": student.tenant_id, "student": student.id},
            )
            session.flush()
    finally:
        session.rollback()
        session.close()


# --- isolation, with people in it -----------------------------------------


def test_people_and_their_history_do_not_cross_institutions(
    nine: dict[str, TenantFixture]
) -> None:
    """Phase 1's guarantee, over the most sensitive records the product holds."""
    british = nine["school:british"]
    american = nine["school:american"]

    session = british.session()
    try:
        person, student, enrolment = admit_and_enrol(
            session, full_name="Strictly Private Pupil", reference="PRIVATE-1"
        )
        event_id = service.history(session, student)[0].id
    finally:
        session.close()

    stranger = american.session()
    try:
        assert stranger.get(Person, person.id) is None
        assert stranger.get(StudentRelationship, student.id) is None
        assert stranger.get(Enrolment, enrolment.id) is None
        assert stranger.get(EnrolmentEvent, event_id) is None
        assert (
            stranger.execute(
                select(StudentRelationship).where(
                    StudentRelationship.reference == "PRIVATE-1"
                )
            )
            .scalars()
            .all()
            == []
        )
        # Even raw SQL, which bypasses the ORM guard entirely, sees nothing.
        leaked = stranger.execute(
            text("SELECT count(*) FROM people WHERE id = :id"), {"id": person.id}
        ).scalar_one()
        assert leaked == 0
    finally:
        stranger.close()


def test_an_enrolment_cannot_reference_another_institutions_student(
    nine: dict[str, TenantFixture]
) -> None:
    """The foreign key is not the guarantee; row-level security is.

    From the stranger's context the student relationship does not exist, so the
    reference fails rather than silently creating a placement in the wrong
    school's records.
    """
    session = nine["school:nigerian"].session()
    try:
        person = service.record_person(session, full_name="Belongs Elsewhere")
        student = service.register_student(session, person)
        session.commit()
        foreign_student_id = student.id
    finally:
        session.close()

    stranger = nine["school:university"].session()
    try:
        with pytest.raises(IntegrityError):
            stranger.add(
                Enrolment(
                    student_relationship_id=foreign_student_id,
                    status=EnrolmentStatus.active,
                    started_on=date(2026, 9, 1),
                )
            )
            stranger.flush()
    finally:
        stranger.rollback()
        stranger.close()


# --- refusals -------------------------------------------------------------


def test_a_person_needs_a_name(nine: dict[str, TenantFixture]) -> None:
    session = nine["school:british"].session()
    try:
        for empty in ("", "   "):
            with pytest.raises(service.EnrolmentError):
                service.record_person(session, full_name=empty)
    finally:
        session.rollback()
        session.close()


def test_nobody_is_their_own_guardian(nine: dict[str, TenantFixture]) -> None:
    """Refused by the service, and independently by a check constraint."""
    session = nine["school:british"].session()
    try:
        person = service.record_person(session, full_name="Self Guardian")
        session.commit()
        with pytest.raises(service.EnrolmentError):
            service.link_guardian(
                session, guardian=person, student=person, relationship_label="Self"
            )
        session.rollback()

        with pytest.raises(IntegrityError):
            session.add(
                GuardianRelationship(
                    guardian_person_id=person.id,
                    student_person_id=person.id,
                    relationship_label="Self",
                )
            )
            session.flush()
    finally:
        session.rollback()
        session.close()


def test_only_a_prospective_enrolment_can_be_taken_up(
    nine: dict[str, TenantFixture]
) -> None:
    session = nine["school:british"].session()
    try:
        _p, _s, enrolment = admit_and_enrol(session, full_name="Already Enrolled")
        with pytest.raises(service.EnrolmentError):
            service.enrol(session, enrolment, on=date(2026, 9, 2))
    finally:
        session.rollback()
        session.close()


# --- the structural guarantee ---------------------------------------------


PEOPLE_ROOT = pathlib.Path(__file__).resolve().parents[1] / "modules" / "people"

# The columns whose existence would mean placement had become a mutable pointer
# again. Named here rather than described in prose, so the guarantee is checked
# rather than remembered.
FORBIDDEN_PLACEMENT_COLUMNS = {
    "class_id",
    "class_group_id",
    "level_id",
    "stage_id",
    "programme_id",
    "cohort_id",
    "academic_year_id",
    "current_class_id",
    "current_level_id",
}


@pytest.mark.parametrize(
    "model",
    [Person, StudentRelationship, StaffRelationship, GuardianRelationship],
    ids=lambda m: m.__name__,
)
def test_no_relationship_table_carries_a_placement(model: type) -> None:
    """The regression this whole module exists to prevent.

    The day somebody adds `class_group_id` to `student_relationships` "just for
    the list screen", the history stops being a history: the column will be
    updated in place, and every enrolment row will become decoration. This test
    fails that change on the commit that makes it.

    `staff_relationships.academic_unit_id` is deliberately *not* forbidden — a
    member of staff's department is a fact about their employment, not a
    placement that a student progresses through.
    """
    columns = {c.key for c in inspect(model).columns}
    offending = columns & FORBIDDEN_PLACEMENT_COLUMNS
    assert not offending, (
        f"{model.__name__} carries {sorted(offending)}. Placement belongs to "
        "`enrolments`, where it has a start and an end; a column here would be "
        "overwritten and the student's history would be lost."
    )


def test_the_people_module_never_mutates_a_placement_column() -> None:
    """Only `_close` may write to an enrolment, and only its end and outcome.

    Parsing the module rather than trusting the convention: any assignment to a
    placement attribute of an existing enrolment outside `_open` would be the
    overwrite this design exists to prevent.
    """
    source = (PEOPLE_ROOT / "service.py").read_text()
    tree = ast.parse(source, filename="service.py")

    allowed_functions = {"_open", "enrol"}  # `enrol` fills in a placement never used yet
    offending: list[str] = []
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if function.name in allowed_functions:
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr in FORBIDDEN_PLACEMENT_COLUMNS
                ):
                    offending.append(f"{function.name} line {node.lineno}: {target.attr}")
    assert not offending, (
        "A placement column is assigned outside the functions allowed to set "
        "one. Moving a student must close a placement and open another:\n"
        + "\n".join(offending)
    )
