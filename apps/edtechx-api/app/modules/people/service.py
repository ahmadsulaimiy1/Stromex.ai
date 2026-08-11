"""The operations that move a person through an institution.

This module exists so that "enrolment is history" is a property of the code
rather than a convention people remember. Every transition here follows the
same shape:

    close the current placement, with an outcome and an end date
    open the next one, pointing back at it
    write an event saying why

There is no function that changes where a student is. `transfer` and `progress`
both produce a *new* enrolment; the previous row keeps the class group it
always had. Anything that wants to know where somebody is now asks for the open
enrolment, and anything that wants to know where they were in March asks for
the enrolment covering March. Both questions have answers, which is the whole
reason for the design.

Nothing here reads a programme, a level, or a class group in order to decide
what to do. The caller passes whichever layers its institution uses, and the
absent ones stay null.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.academics.progression import Evaluation, ProgressionOutcome
from app.modules.audit.service import AuditAction, record
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


class EnrolmentError(ValueError):
    """An operation that the record would not survive."""


@dataclass(frozen=True, slots=True)
class Placement:
    """The academic layers a placement names — all of them optional.

    A value object rather than five keyword arguments repeated at every call
    site, and the reason `transfer` can say "change only the class group" while
    leaving everything else exactly as it was.
    """

    academic_year_id: uuid.UUID | None = None
    programme_id: uuid.UUID | None = None
    level_id: uuid.UUID | None = None
    class_group_id: uuid.UUID | None = None
    cohort_id: uuid.UUID | None = None

    @classmethod
    def of(cls, enrolment: Enrolment) -> Placement:
        return cls(
            academic_year_id=enrolment.academic_year_id,
            programme_id=enrolment.programme_id,
            level_id=enrolment.level_id,
            class_group_id=enrolment.class_group_id,
            cohort_id=enrolment.cohort_id,
        )

    def merged(self, other: Placement | None) -> Placement:
        """Overlay another placement, keeping this one's values where unset.

        `None` means "unchanged", not "clear it". Clearing a layer is rare
        enough to deserve being explicit at the call site rather than being the
        accidental result of omitting an argument.
        """
        if other is None:
            return self
        return Placement(
            academic_year_id=other.academic_year_id or self.academic_year_id,
            programme_id=other.programme_id or self.programme_id,
            level_id=other.level_id or self.level_id,
            class_group_id=other.class_group_id or self.class_group_id,
            cohort_id=other.cohort_id or self.cohort_id,
        )

    def describe(self) -> dict[str, str]:
        return {
            name: str(value)
            for name, value in (
                ("academic_year_id", self.academic_year_id),
                ("programme_id", self.programme_id),
                ("level_id", self.level_id),
                ("class_group_id", self.class_group_id),
                ("cohort_id", self.cohort_id),
            )
            if value is not None
        }


# --- people and their relationships ---------------------------------------


def record_person(db: Session, *, full_name: str, **fields: object) -> Person:
    """Record a human being. No relationship implied, and no identity required.

    Creating a person is separate from making them a student or a member of
    staff, because they are separate facts and because the same person may
    later become both.
    """
    if not full_name or not full_name.strip():
        raise EnrolmentError("A person needs a name.")
    person = Person(full_name=full_name.strip(), **fields)
    person.sort_name = person.sort_name or (person.family_name or person.full_name)
    db.add(person)
    db.flush()
    record(
        db,
        action=AuditAction.create,
        resource_type="person",
        resource_id=person.id,
        after={"full_name": person.full_name},
    )
    return person


def register_student(
    db: Session,
    person: Person,
    *,
    reference: str | None = None,
    kind_label: str = "Student",
    started_on: date | None = None,
    status: RelationshipStatus = RelationshipStatus.prospective,
    **fields: object,
) -> StudentRelationship:
    """Record that this person learns here."""
    relationship = StudentRelationship(
        person_id=person.id,
        reference=reference,
        kind_label=kind_label,
        started_on=started_on,
        status=status,
        **fields,
    )
    db.add(relationship)
    db.flush()
    record(
        db,
        action=AuditAction.create,
        resource_type="student_relationship",
        resource_id=relationship.id,
        after={"person_id": str(person.id), "reference": reference},
    )
    return relationship


def register_staff(
    db: Session,
    person: Person,
    *,
    reference: str | None = None,
    kind_label: str = "Staff",
    academic_unit_id: uuid.UUID | None = None,
    is_teaching: bool = False,
    started_on: date | None = None,
    **fields: object,
) -> StaffRelationship:
    """Record that this person works here. Independent of any student record."""
    relationship = StaffRelationship(
        person_id=person.id,
        reference=reference,
        kind_label=kind_label,
        academic_unit_id=academic_unit_id,
        is_teaching=is_teaching,
        started_on=started_on,
        status=RelationshipStatus.active,
        **fields,
    )
    db.add(relationship)
    db.flush()
    record(
        db,
        action=AuditAction.create,
        resource_type="staff_relationship",
        resource_id=relationship.id,
        after={"person_id": str(person.id), "kind_label": kind_label},
    )
    return relationship


def link_guardian(
    db: Session,
    *,
    guardian: Person,
    student: Person,
    relationship_label: str,
    **fields: object,
) -> GuardianRelationship:
    """Record that one person is responsible for another."""
    if guardian.id == student.id:
        raise EnrolmentError("A person cannot be their own guardian.")
    link = GuardianRelationship(
        guardian_person_id=guardian.id,
        student_person_id=student.id,
        relationship_label=relationship_label,
        **fields,
    )
    db.add(link)
    db.flush()
    record(
        db,
        action=AuditAction.create,
        resource_type="guardian_relationship",
        resource_id=link.id,
        after={
            "guardian_person_id": str(guardian.id),
            "student_person_id": str(student.id),
            "relationship_label": relationship_label,
        },
    )
    return link


# --- the enrolment lifecycle ----------------------------------------------


def _log(
    db: Session,
    enrolment: Enrolment,
    kind: EnrolmentEventKind,
    *,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
    **detail: object,
) -> EnrolmentEvent:
    event = EnrolmentEvent(
        enrolment_id=enrolment.id,
        kind=kind,
        occurred_on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        detail={k: v for k, v in detail.items() if v is not None},
    )
    db.add(event)
    db.flush()
    return event


def _student_of(db: Session, enrolment: Enrolment) -> StudentRelationship:
    """The student this placement belongs to, or a refusal.

    `db.get` returns `None` for a row in another tenant just as it does for a
    row that does not exist — row-level security makes those the same thing.
    Treating the result as present would let a cross-tenant reference fail
    later, somewhere less obvious, so it fails here.
    """
    student = db.get(StudentRelationship, enrolment.student_relationship_id)
    if student is None:
        raise EnrolmentError("That enrolment's student record is not reachable.")
    return student


def _open(
    db: Session,
    student: StudentRelationship,
    placement: Placement,
    *,
    on: date,
    status: EnrolmentStatus,
    previous: Enrolment | None = None,
) -> Enrolment:
    enrolment = Enrolment(
        student_relationship_id=student.id,
        academic_year_id=placement.academic_year_id,
        programme_id=placement.programme_id,
        level_id=placement.level_id,
        class_group_id=placement.class_group_id,
        cohort_id=placement.cohort_id,
        status=status,
        started_on=on,
        previous_enrolment_id=previous.id if previous else None,
    )
    db.add(enrolment)
    db.flush()
    return enrolment


def _close(enrolment: Enrolment, *, on: date, outcome: EnrolmentOutcome) -> None:
    """End a placement. The only mutation this module performs on an enrolment.

    It sets an end date and an outcome, and touches nothing else. The class
    group, level and programme it was opened with remain exactly as they were,
    which is what makes the row a historical record rather than a cache of the
    present.
    """
    if enrolment.ended_on is not None:
        raise EnrolmentError(
            "That enrolment is already closed. Correct it with a new event "
            "rather than reopening it."
        )
    if on < enrolment.started_on:
        raise EnrolmentError(
            "An enrolment cannot end before it began — check the effective date."
        )
    enrolment.ended_on = on
    enrolment.outcome = outcome


def admit(
    db: Session,
    student: StudentRelationship,
    *,
    on: date,
    placement: Placement | None = None,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """Offer a place. The enrolment exists but is not yet active.

    Admission and enrolment are separate because institutions separate them:
    an offer can be made, held, and declined, and a system that only records
    the accepted ones cannot report on admissions at all.
    """
    enrolment = _open(
        db,
        student,
        placement or Placement(),
        on=on,
        status=EnrolmentStatus.prospective,
    )
    _log(
        db,
        enrolment,
        EnrolmentEventKind.admitted,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        **(placement or Placement()).describe(),
    )
    record(
        db,
        action=AuditAction.create,
        resource_type="enrolment",
        resource_id=enrolment.id,
        after={"status": EnrolmentStatus.prospective.value, "started_on": str(on)},
    )
    return enrolment


def enrol(
    db: Session,
    enrolment: Enrolment,
    *,
    on: date,
    placement: Placement | None = None,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """Accept the place: the enrolment becomes active.

    A placement passed here fills in layers that were unknown at admission —
    which class group, which cohort — without closing and reopening the row,
    because nothing has yet happened under the old placement to preserve.
    """
    if enrolment.status is not EnrolmentStatus.prospective:
        raise EnrolmentError("Only a prospective enrolment can be taken up.")
    merged = Placement.of(enrolment).merged(placement)
    enrolment.academic_year_id = merged.academic_year_id
    enrolment.programme_id = merged.programme_id
    enrolment.level_id = merged.level_id
    enrolment.class_group_id = merged.class_group_id
    enrolment.cohort_id = merged.cohort_id
    enrolment.status = EnrolmentStatus.active

    student = db.get(StudentRelationship, enrolment.student_relationship_id)
    if student is not None and student.status is RelationshipStatus.prospective:
        student.status = RelationshipStatus.active
        student.started_on = student.started_on or on

    _log(
        db,
        enrolment,
        EnrolmentEventKind.enrolled,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        **merged.describe(),
    )
    db.flush()
    return enrolment


def transfer(
    db: Session,
    enrolment: Enrolment,
    *,
    to: Placement,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """Move a student. Closes this placement and opens the next one.

    The old row is not edited. Ask it where the student was last term and it
    still knows, which is the entire difference between a record and a pointer.
    """
    previous = Placement.of(enrolment)
    _close(enrolment, on=on, outcome=EnrolmentOutcome.transferred)
    replacement = _open(
        db,
        _student_of(db, enrolment),
        previous.merged(to),
        on=on,
        status=EnrolmentStatus.active,
        previous=enrolment,
    )
    _log(
        db,
        enrolment,
        EnrolmentEventKind.transferred,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        to_enrolment_id=str(replacement.id),
        **{f"from_{k}": v for k, v in previous.describe().items()},
    )
    _log(
        db,
        replacement,
        EnrolmentEventKind.placed,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        from_enrolment_id=str(enrolment.id),
        **Placement.of(replacement).describe(),
    )
    record(
        db,
        action=AuditAction.update,
        resource_type="enrolment",
        resource_id=enrolment.id,
        before=previous.describe(),
        after=Placement.of(replacement).describe(),
        reason=reason,
    )
    return replacement


def suspend(
    db: Session,
    enrolment: Enrolment,
    *,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """Deferral, intermission, leave of absence — one state, three words.

    The placement stays open, because the student has not left it. Only the
    status changes, and the ledger records when.
    """
    if enrolment.status is not EnrolmentStatus.active:
        raise EnrolmentError("Only an active enrolment can be suspended.")
    enrolment.status = EnrolmentStatus.suspended
    _log(
        db,
        enrolment,
        EnrolmentEventKind.suspended,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
    )
    db.flush()
    return enrolment


def resume(
    db: Session,
    enrolment: Enrolment,
    *,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    if enrolment.status is not EnrolmentStatus.suspended:
        raise EnrolmentError("Only a suspended enrolment can be resumed.")
    enrolment.status = EnrolmentStatus.active
    _log(
        db,
        enrolment,
        EnrolmentEventKind.resumed,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
    )
    db.flush()
    return enrolment


def withdraw(
    db: Session,
    enrolment: Enrolment,
    *,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
    end_relationship: bool = True,
) -> Enrolment:
    """The student leaves. The placement closes and nothing opens.

    `end_relationship` is false when the student is leaving one of several
    concurrent placements — a joint programme, a single course elsewhere —
    and remains a student here.
    """
    _close(enrolment, on=on, outcome=EnrolmentOutcome.withdrawn)
    enrolment.status = EnrolmentStatus.ended
    if end_relationship:
        student = db.get(StudentRelationship, enrolment.student_relationship_id)
        if student is not None:
            student.status = RelationshipStatus.ended
            student.ended_on = on
    _log(
        db,
        enrolment,
        EnrolmentEventKind.withdrawn,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
    )
    record(
        db,
        action=AuditAction.update,
        resource_type="enrolment",
        resource_id=enrolment.id,
        after={"outcome": EnrolmentOutcome.withdrawn.value, "ended_on": str(on)},
        reason=reason,
    )
    return enrolment


def readmit(
    db: Session,
    student: StudentRelationship,
    *,
    on: date,
    placement: Placement | None = None,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """A returning student. A new placement, with the gap visible in between.

    Not a reopening of the closed one: the months away are part of the record,
    and reopening the old row would silently claim they were not.
    """
    previous = latest_enrolment(db, student)
    if previous is not None and previous.is_open:
        raise EnrolmentError(
            "That student already has an open enrolment; readmission applies "
            "to somebody who has left."
        )
    enrolment = _open(
        db,
        student,
        placement or Placement(),
        on=on,
        status=EnrolmentStatus.active,
        previous=previous,
    )
    student.status = RelationshipStatus.active
    student.ended_on = None
    _log(
        db,
        enrolment,
        EnrolmentEventKind.readmitted,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
        previous_enrolment_id=str(previous.id) if previous else None,
        **(placement or Placement()).describe(),
    )
    return enrolment


def progress(
    db: Session,
    enrolment: Enrolment,
    evaluation: Evaluation,
    *,
    on: date,
    to: Placement | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment | None:
    """Apply a progression decision, whatever the institution's rule decided.

    Takes the `Evaluation` produced by `academics.progression` rather than
    re-deciding anything: this function knows how to *record* an outcome and
    nothing at all about what earns one. Its reasoning is copied into the
    event, so the answer to "why was he held back?" survives the rule being
    edited afterwards.

    Returns the next placement, or `None` when the outcome ends the student's
    journey rather than continuing it.
    """
    reasoning = {"rule": evaluation.rule_code, "checks": evaluation.explain()}

    if evaluation.outcome is ProgressionOutcome.graduate:
        complete(
            db,
            enrolment,
            on=on,
            actor_membership_id=actor_membership_id,
            reason="; ".join(evaluation.explain()),
        )
        # Nothing opens: the journey ended rather than continuing.
        return None

    if evaluation.outcome is ProgressionOutcome.review:
        # A decision nobody has made yet is not an outcome. The placement stays
        # open, and the ledger says a review is owed.
        _log(
            db,
            enrolment,
            EnrolmentEventKind.corrected,
            on=on,
            reason="Held for review",
            actor_membership_id=actor_membership_id,
            **reasoning,
        )
        db.flush()
        return enrolment

    repeating = evaluation.outcome is ProgressionOutcome.repeat
    outcome = EnrolmentOutcome.repeated if repeating else EnrolmentOutcome.progressed
    kind = (
        EnrolmentEventKind.repeated if repeating else EnrolmentEventKind.progressed
    )

    previous = Placement.of(enrolment)
    _close(enrolment, on=on, outcome=outcome)
    enrolment.status = EnrolmentStatus.ended
    # A repeat keeps the same level; a promotion takes the caller's target. The
    # target is not derived here — `Level.next_level_id` is the institution's
    # own graph, and reading it is the caller's business, not a rule this
    # module invents.
    replacement = _open(
        db,
        _student_of(db, enrolment),
        previous.merged(to),
        on=on,
        status=EnrolmentStatus.active,
        previous=enrolment,
    )
    _log(
        db,
        enrolment,
        kind,
        on=on,
        actor_membership_id=actor_membership_id,
        to_enrolment_id=str(replacement.id),
        **reasoning,
    )
    record(
        db,
        action=AuditAction.update,
        resource_type="enrolment",
        resource_id=enrolment.id,
        before=previous.describe(),
        after=Placement.of(replacement).describe(),
        reason=kind.value,
    )
    return replacement


def complete(
    db: Session,
    enrolment: Enrolment,
    *,
    on: date,
    reason: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> Enrolment:
    """The student finished. Distinct from withdrawing, and from being awarded.

    Completion is about the placement; an award is a separate record, because
    some institutions award nothing and some award more than one thing for the
    same programme.
    """
    _close(enrolment, on=on, outcome=EnrolmentOutcome.completed)
    enrolment.status = EnrolmentStatus.ended
    student = db.get(StudentRelationship, enrolment.student_relationship_id)
    if student is not None:
        student.status = RelationshipStatus.ended
        student.ended_on = on
    _log(
        db,
        enrolment,
        EnrolmentEventKind.completed,
        on=on,
        reason=reason,
        actor_membership_id=actor_membership_id,
    )
    record(
        db,
        action=AuditAction.update,
        resource_type="enrolment",
        resource_id=enrolment.id,
        after={"outcome": EnrolmentOutcome.completed.value, "ended_on": str(on)},
    )
    return enrolment


def award(
    db: Session,
    student: StudentRelationship,
    *,
    qualification_id: uuid.UUID,
    on: date,
    programme_id: uuid.UUID | None = None,
    enrolment: Enrolment | None = None,
    classification_label: str | None = None,
    reference: str | None = None,
    actor_membership_id: uuid.UUID | None = None,
) -> QualificationAward:
    """Award the institution's own qualification.

    The qualification is a row the institution created, so this one function
    awards a certificate of attendance and a research doctorate without
    knowing the difference between them.
    """
    granted = QualificationAward(
        student_relationship_id=student.id,
        qualification_id=qualification_id,
        programme_id=programme_id,
        enrolment_id=enrolment.id if enrolment else None,
        awarded_on=on,
        classification_label=classification_label,
        reference=reference,
        awarded_by_membership_id=actor_membership_id,
    )
    db.add(granted)
    db.flush()
    if enrolment is not None:
        _log(
            db,
            enrolment,
            EnrolmentEventKind.awarded,
            on=on,
            actor_membership_id=actor_membership_id,
            qualification_id=str(qualification_id),
            classification_label=classification_label,
        )
    record(
        db,
        action=AuditAction.approve,
        resource_type="qualification_award",
        resource_id=granted.id,
        after={"qualification_id": str(qualification_id), "awarded_on": str(on)},
    )
    return granted


# --- reading the record ---------------------------------------------------


def enrolments_for(db: Session, student: StudentRelationship) -> list[Enrolment]:
    """Every placement, oldest first. The student's academic history."""
    return list(
        db.execute(
            select(Enrolment)
            .where(Enrolment.student_relationship_id == student.id)
            .order_by(Enrolment.started_on, Enrolment.created_at)
        )
        .scalars()
        .all()
    )


def open_enrolments(db: Session, student: StudentRelationship) -> list[Enrolment]:
    """Where the student is now — plural, because concurrent enrolment is real."""
    return [e for e in enrolments_for(db, student) if e.is_open]


def latest_enrolment(db: Session, student: StudentRelationship) -> Enrolment | None:
    history = enrolments_for(db, student)
    return history[-1] if history else None


def enrolment_on(
    db: Session, student: StudentRelationship, when: date
) -> list[Enrolment]:
    """Where the student was on a given date.

    The question a mark sheet, an attendance register, or a subject-access
    request actually asks, and the one a mutable `class_id` cannot answer.
    """
    return [
        e
        for e in enrolments_for(db, student)
        if e.started_on <= when and (e.ended_on is None or e.ended_on >= when)
    ]


def history(db: Session, student: StudentRelationship) -> list[EnrolmentEvent]:
    """The ledger for this student, in the order things happened."""
    enrolment_ids = [e.id for e in enrolments_for(db, student)]
    if not enrolment_ids:
        return []
    return list(
        db.execute(
            select(EnrolmentEvent)
            .where(EnrolmentEvent.enrolment_id.in_(enrolment_ids))
            .order_by(EnrolmentEvent.occurred_on, EnrolmentEvent.created_at)
        )
        .scalars()
        .all()
    )


def relationships_of(db: Session, person: Person) -> dict[str, list[object]]:
    """Everything this person is to the institution, at once.

    One query set rather than three call sites, because the answer to "who is
    this?" is routinely "all three of these", and a caller that checks only the
    student table will confidently report that a parent who teaches here is a
    stranger.
    """
    student = db.execute(
        select(StudentRelationship).where(StudentRelationship.person_id == person.id)
    ).scalars().all()
    staff = db.execute(
        select(StaffRelationship).where(StaffRelationship.person_id == person.id)
    ).scalars().all()
    guardian_of = db.execute(
        select(GuardianRelationship).where(
            GuardianRelationship.guardian_person_id == person.id
        )
    ).scalars().all()
    guardians = db.execute(
        select(GuardianRelationship).where(
            GuardianRelationship.student_person_id == person.id
        )
    ).scalars().all()
    return {
        "student": list(student),
        "staff": list(staff),
        "guardian_of": list(guardian_of),
        "guardians": list(guardians),
    }


# --- finding somebody who may already be here -----------------------------


def find_student_by_reference(
    db: Session, reference: str
) -> StudentRelationship | None:
    """The institution's own identifier is the strongest match there is."""
    if not reference:
        return None
    return db.execute(
        select(StudentRelationship).where(
            StudentRelationship.reference == reference.strip()
        )
    ).scalars().first()


def find_person_by_email(db: Session, email: str) -> Person | None:
    if not email:
        return None
    return db.execute(
        select(Person).where(
            Person.email == email.strip().lower(), Person.deleted_at.is_(None)
        )
    ).scalars().first()


def find_person_by_name_and_birth(
    db: Session, full_name: str, date_of_birth: date | None
) -> Person | None:
    """The weakest match, and deliberately requiring both halves.

    Name alone is not identity: two children called Muhammad Ibrahim in a school
    of nine hundred is ordinary, not a coincidence, and merging them would be a
    far worse outcome than creating a second record. With a date of birth the
    match is good enough to *flag*, which is all this is used for.
    """
    if not full_name or date_of_birth is None:
        return None
    return db.execute(
        select(Person).where(
            func.lower(Person.full_name) == full_name.strip().lower(),
            Person.date_of_birth == date_of_birth,
            Person.deleted_at.is_(None),
        )
    ).scalars().first()


# --- primitives other modules need, so nobody imports these tables ---------
#
# The module-boundary rule (EDTECHX_ARCHITECTURE.md §3) says a module owns its
# tables and everyone else reads them through its service. These exist so that
# rule needs no exception for the importer, which legitimately has to undo what
# it created.


def person(db: Session, person_id: uuid.UUID) -> Person | None:
    return db.get(Person, person_id)


def student(db: Session, student_id: uuid.UUID) -> StudentRelationship | None:
    return db.get(StudentRelationship, student_id)


def enrolment(db: Session, enrolment_id: uuid.UUID) -> Enrolment | None:
    return db.get(Enrolment, enrolment_id)


def events_for(db: Session, enrolment_id: uuid.UUID) -> list[EnrolmentEvent]:
    return list(
        db.execute(
            select(EnrolmentEvent)
            .where(EnrolmentEvent.enrolment_id == enrolment_id)
            .order_by(EnrolmentEvent.occurred_on, EnrolmentEvent.created_at)
        )
        .scalars()
        .all()
    )


def forget_person(db: Session, subject: Person) -> None:
    """Soft-delete. The row stays so an auditor can see it existed."""
    subject.deleted_at = _now()
    db.flush()


def end_student(db: Session, relationship: StudentRelationship, *, on: date) -> None:
    relationship.status = RelationshipStatus.ended
    relationship.ended_on = on
    db.flush()


def unlink_guardian(db: Session, link_id: uuid.UUID) -> None:
    """Guardianships are the one relationship that is genuinely deletable.

    A guardianship recorded in error is not a historical fact about a child's
    education; it is a mistake about who to telephone. Nothing hangs off it, and
    the audit entry records that it was removed.
    """
    link = db.get(GuardianRelationship, link_id)
    if link is not None:
        db.delete(link)
        db.flush()


def _now() -> datetime:
    from datetime import UTC

    return datetime.now(UTC)


def people_by_ids(db: Session, ids) -> dict[uuid.UUID, Person]:
    """Load people by id, for callers holding ids from rows they may already see.

    Exists so a route never writes `db.get(Person, …)` itself. The distinction
    is real: fetching a person whose id came out of an already-scoped query is
    implied by that query, and fetching one whose id came out of a URL is an
    IDOR. Only the first is what this function is for, and keeping it in the
    owning module is what lets `test_boundaries.py` forbid the second outright.
    """
    wanted = [i for i in ids if i is not None]
    if not wanted:
        return {}
    rows = db.execute(select(Person).where(Person.id.in_(wanted))).scalars().all()
    return {person.id: person for person in rows}


def students_in_class(
    db: Session, class_group_id: uuid.UUID | None, *, on: date
) -> list[tuple[StudentRelationship, Person]]:
    """Who was in this group on this date, from the enrolments themselves.

    Derived rather than stored, which is the whole reason enrolment is a row
    with a beginning and an end (ADR-027). A child who transferred in on Monday
    is on Monday's register without anybody rebuilding a list, and last March's
    register still shows last March's class.

    The date is the question rather than a filter on today, so a register
    reopened in July still lists the people who were actually there in March.
    """
    if class_group_id is None:
        return []
    placements = db.execute(
        select(Enrolment).where(
            Enrolment.class_group_id == class_group_id,
            Enrolment.started_on <= on,
            (Enrolment.ended_on.is_(None)) | (Enrolment.ended_on >= on),
        )
    ).scalars().all()
    if not placements:
        return []
    students = {
        row.id: row
        for row in db.execute(
            select(StudentRelationship).where(
                StudentRelationship.id.in_([p.student_relationship_id for p in placements])
            )
        ).scalars().all()
    }
    found = people_by_ids(db, [s.person_id for s in students.values()])
    return [
        (student, found[student.person_id])
        for student in students.values()
        if student.person_id in found
    ]
