"""Moving marks from a teacher's screen to an institution's record.

Six things happen between the two, and each is a separate call because each is
a separate decision somebody is accountable for:

    enter      a teacher's working value, revisable
    moderate   a second marker, where the department requires one
    submit     the teacher says they are finished
    review     the institution's own steps, however many it has
    publish    the moment it becomes official — and immutable
    amend      a correction afterwards, with its reason

The one rule that decides the shape of everything: **publishing snapshots**. A
published result carries the mark *and* the grading it was given, so a school
that moves its grade boundaries next year cannot silently change what it awarded
last year. Recomputing from live scores would be smaller, tidier and wrong.

Nothing here knows what a passing mark is. The scale is the institution's, the
bands are its rows, and this module asks it (`GradingScale.band_for`) rather
than deciding.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.assessment.models import (
    ApprovalRecord,
    ApprovalWorkflow,
    Assessment,
    AssessmentScore,
    AssessmentStatus,
    PublishedResult,
    ResultAmendment,
    ResultSet,
    ResultStage,
)
from app.modules.audit.service import AuditAction, record


class AssessmentError(ValueError):
    """An operation the academic record would not survive."""


class NotAuthorisedForStep(AssessmentError):
    """The right action, by the wrong person, at the wrong point in the workflow."""


# --- workflows --------------------------------------------------------------


def define_workflow(
    db: Session,
    *,
    code: str,
    name: str,
    steps: list[dict],
    applies_to: str = "results",
    is_default: bool = False,
) -> ApprovalWorkflow:
    """Record an institution's own approval sequence.

    Every step's permission is checked against the catalogue here, so a typo
    fails when somebody configures the workflow rather than at the end of term
    when a result set cannot leave review and nobody can say why.
    """
    from app.modules.authz import permissions as perms

    if not steps:
        raise AssessmentError(
            "A workflow needs at least one step. An institution that approves in "
            "one action simply has no workflow row."
        )
    seen: set[str] = set()
    for index, step in enumerate(steps):
        key = str(step.get("key") or "").strip()
        if not key:
            raise AssessmentError(f"Step {index + 1} has no key.")
        if key in seen:
            raise AssessmentError(f"Step key {key!r} appears twice.")
        seen.add(key)
        permission = step.get("permission")
        if not permission:
            raise AssessmentError(f"Step {key!r} names no permission.")
        perms.validate(str(permission))

    workflow = ApprovalWorkflow(
        code=code, name=name, applies_to=applies_to,
        steps=[
            {
                "key": str(s["key"]).strip(),
                "name": str(s.get("name") or s["key"]),
                "permission": str(s["permission"]),
            }
            for s in steps
        ],
        is_default=is_default,
    )
    db.add(workflow)
    db.flush()
    return workflow


def default_workflow(db: Session, applies_to: str = "results") -> ApprovalWorkflow | None:
    return db.execute(
        select(ApprovalWorkflow).where(
            ApprovalWorkflow.applies_to == applies_to,
            ApprovalWorkflow.is_active.is_(True),
            ApprovalWorkflow.is_default.is_(True),
        )
    ).scalars().first()


# --- entering marks ---------------------------------------------------------


def enter_scores(
    db: Session,
    assessment: Assessment,
    scores: dict[uuid.UUID, float | None],
    *,
    membership_id: uuid.UUID | None = None,
    absent: set[uuid.UUID] | None = None,
    comments: dict[uuid.UUID, str] | None = None,
) -> int:
    """A teacher's working values. Revisable until the assessment closes.

    Refuses a mark above the maximum, because a 105 out of 100 is a slip that
    becomes a published result if nothing catches it, and refuses to touch a
    closed assessment at all.
    """
    if assessment.status is AssessmentStatus.cancelled:
        raise AssessmentError("That assessment was cancelled.")
    if assessment.status is AssessmentStatus.closed:
        raise AssessmentError(
            "That assessment is closed. Reopen it before changing marks."
        )
    maximum = float(assessment.max_score) if assessment.max_score is not None else None
    absent = absent or set()
    comments = comments or {}
    now = datetime.now(UTC)

    existing = {
        row.student_relationship_id: row
        for row in db.execute(
            select(AssessmentScore).where(
                AssessmentScore.assessment_id == assessment.id,
                AssessmentScore.student_relationship_id.in_(list(scores)),
            )
        ).scalars().all()
    }
    written = 0
    for student_id, value in scores.items():
        if value is not None:
            if value < 0:
                raise AssessmentError(f"A mark of {value:g} is below zero.")
            if maximum is not None and value > maximum:
                raise AssessmentError(
                    f"A mark of {value:g} is above the maximum of {maximum:g}."
                )
        row = existing.get(student_id)
        if row is None:
            db.add(
                AssessmentScore(
                    assessment_id=assessment.id,
                    student_relationship_id=student_id,
                    score=value,
                    is_absent=student_id in absent,
                    comment=comments.get(student_id),
                    entered_by_membership_id=membership_id,
                    entered_at=now,
                )
            )
        else:
            row.score = value
            row.is_absent = student_id in absent
            if student_id in comments:
                row.comment = comments[student_id]
            row.entered_by_membership_id = membership_id
            row.entered_at = now
        written += 1
    db.flush()
    return written


def moderate(
    db: Session,
    assessment: Assessment,
    adjustments: dict[uuid.UUID, float],
    *,
    membership_id: uuid.UUID,
    note: str | None = None,
) -> int:
    """A second marker's value, kept alongside the first rather than over it.

    Both numbers survive. A moderation that overwrote the original would destroy
    the evidence that moderation happened at all, which is the only reason a
    department asks for it.
    """
    rows = db.execute(
        select(AssessmentScore).where(
            AssessmentScore.assessment_id == assessment.id,
            AssessmentScore.student_relationship_id.in_(list(adjustments)),
        )
    ).scalars().all()
    now = datetime.now(UTC)
    for row in rows:
        row.moderated_score = adjustments[row.student_relationship_id]
        row.moderated_by_membership_id = membership_id
        row.moderated_at = now
        row.moderation_note = note
    db.flush()
    return len(rows)


# --- what stands in the way of publishing ----------------------------------


@dataclass(frozen=True, slots=True)
class Readiness:
    """What a person reviewing a result set needs to see before deciding.

    Problems, not a boolean. "Not ready" is useless to somebody at four o'clock
    on results day; "eleven marks missing in Chemistry, two above the maximum,
    one assessment still open" is a list they can act on.
    """

    missing_marks: tuple[str, ...] = ()
    invalid_marks: tuple[str, ...] = ()
    open_assessments: tuple[str, ...] = ()
    unmoderated: tuple[str, ...] = ()
    outstanding_steps: tuple[str, ...] = ()

    @property
    def problems(self) -> tuple[str, ...]:
        return (
            *self.missing_marks, *self.invalid_marks, *self.open_assessments,
            *self.unmoderated, *self.outstanding_steps,
        )

    @property
    def is_ready(self) -> bool:
        return not self.problems


def _assessments_for(db: Session, result_set: ResultSet) -> list[Assessment]:
    statement = select(Assessment).where(Assessment.deleted_at.is_(None))
    if result_set.academic_period_id:
        statement = statement.where(
            Assessment.academic_period_id == result_set.academic_period_id
        )
    if result_set.class_group_id:
        statement = statement.where(
            Assessment.class_group_id == result_set.class_group_id
        )
    return list(db.execute(statement).scalars().all())


def _already_published(
    db: Session, assessment_ids: Sequence[uuid.UUID]
) -> set[tuple[uuid.UUID, uuid.UUID]]:
    """The `(assessment, student)` pairs the institution has already published.

    A result set covers a period and a class rather than a list of assessments,
    which is right — a results day is a decision about a cohort. It also means a
    *second* set over the same period and class sweeps up the assessments the
    first one already published. Without this, a late resit published in January
    would republish the whole autumn term, and every one of those marks would
    appear twice on a transcript.

    Found by the document engine, which is the first thing to read a student's
    results as a list rather than one set at a time.
    """
    ids = [i for i in assessment_ids if i is not None]
    if not ids:
        return set()
    rows = db.execute(
        select(
            PublishedResult.assessment_id, PublishedResult.student_relationship_id
        ).where(PublishedResult.assessment_id.in_(ids))
    ).all()
    return {(row[0], row[1]) for row in rows}


def _period_end(db: Session, result_set: ResultSet):
    """The last day of the period these results cover, where there is one."""
    from app.modules.academics import service as academics

    found = academics.period(db, result_set.academic_period_id)
    return found.ends_on if found else None


def readiness(db: Session, result_set: ResultSet) -> Readiness:
    """Everything an institution would want checked before it commits.

    Deliberately reports rather than refuses: a school may knowingly publish
    with a mark missing for a child who left, and that is its decision. What it
    may not do is publish *without being told*.
    """
    assessments = _assessments_for(db, result_set)
    missing: list[str] = []
    invalid: list[str] = []
    still_open: list[str] = []
    unmoderated: list[str] = []

    from app.modules.people import service as people

    # As of the *period the results cover*, not as of the day somebody pressed
    # the button. Publishing the autumn term in January would otherwise find
    # nobody expected — every child having since moved on — and report a set
    # with no marks in it as ready.
    as_of = _period_end(db, result_set) or datetime.now(UTC).date()
    expected = (
        {
            student.id
            for student, _person in people.students_in_class(
                db, result_set.class_group_id, on=as_of
            )
        }
        if result_set.class_group_id
        else set()
    )

    for assessment in assessments:
        if assessment.status is AssessmentStatus.open:
            still_open.append(f"{assessment.name} is still open for marking.")
        rows = db.execute(
            select(AssessmentScore).where(AssessmentScore.assessment_id == assessment.id)
        ).scalars().all()
        by_student = {row.student_relationship_id: row for row in rows}
        for student_id in expected:
            row = by_student.get(student_id)
            if row is None or (row.effective_score is None and not row.is_absent):
                missing.append(f"{assessment.name}: a mark is missing.")
                break
        maximum = (
            float(assessment.max_score) if assessment.max_score is not None else None
        )
        for row in rows:
            value = row.effective_score
            if value is None:
                continue
            if float(value) < 0 or (maximum is not None and float(value) > maximum):
                invalid.append(f"{assessment.name}: a mark is outside the scale.")
                break
        if assessment.requires_moderation and any(
            row.moderated_at is None for row in rows
        ):
            unmoderated.append(f"{assessment.name} has not been moderated.")

    return Readiness(
        missing_marks=tuple(missing),
        invalid_marks=tuple(invalid),
        open_assessments=tuple(still_open),
        unmoderated=tuple(unmoderated),
        outstanding_steps=tuple(outstanding_steps(db, result_set)),
    )


# --- the workflow -----------------------------------------------------------


def _workflow_of(db: Session, result_set: ResultSet) -> ApprovalWorkflow | None:
    if result_set.workflow_id:
        return db.get(ApprovalWorkflow, result_set.workflow_id)
    return default_workflow(db)


def approvals(db: Session, result_set: ResultSet) -> list[ApprovalRecord]:
    return list(
        db.execute(
            select(ApprovalRecord)
            .where(ApprovalRecord.result_set_id == result_set.id)
            .order_by(ApprovalRecord.occurred_at)
        ).scalars().all()
    )


def outstanding_steps(db: Session, result_set: ResultSet) -> list[str]:
    """Steps this result set still needs, in order.

    A step that was approved and then *returned* counts as outstanding again:
    sending work back is the point of a review, and a ledger that treated the
    first yes as permanent would let a returned set walk straight to
    publication.
    """
    workflow = _workflow_of(db, result_set)
    if workflow is None:
        return []
    taken = approvals(db, result_set)
    latest: dict[str, str] = {}
    for entry in taken:
        latest[entry.step_key] = entry.decision
    return [
        str(step["name"])
        for step in workflow.steps
        if latest.get(str(step["key"])) != "approved"
    ]


def submit_for_review(
    db: Session, result_set: ResultSet, *, membership_id: uuid.UUID | None = None
) -> ResultSet:
    if result_set.stage is ResultStage.published:
        raise AssessmentError("Published results are corrected by amendment.")
    workflow = _workflow_of(db, result_set)
    result_set.stage = (
        ResultStage.in_review if workflow else ResultStage.submitted
    )
    result_set.current_step = (
        str(workflow.steps[0]["key"]) if workflow and workflow.steps else None
    )
    db.flush()
    record(
        db,
        action=AuditAction.update,
        resource_type="result_set",
        resource_id=result_set.id,
        after={"stage": result_set.stage.value},
        actor_membership_id=membership_id,
    )
    return result_set


def approve_step(
    db: Session,
    result_set: ResultSet,
    *,
    step_key: str,
    membership_id: uuid.UUID,
    permissions: frozenset[str],
    reason: str | None = None,
) -> ResultSet:
    """Take one step of the institution's own workflow.

    The permission checked is the *step's*, not a global one. That is what makes
    the workflow real: a programme coordinator holding the coordinator step's
    permission cannot take the board's step, however senior they are.
    """
    from app.modules.authz import permissions as perms

    if result_set.stage is ResultStage.published:
        raise AssessmentError("Published results are corrected by amendment.")
    workflow = _workflow_of(db, result_set)
    if workflow is None:
        raise AssessmentError("This result set has no approval workflow.")
    step = next((s for s in workflow.steps if str(s["key"]) == step_key), None)
    if step is None:
        raise AssessmentError(f"{step_key!r} is not a step of this workflow.")
    if not perms.has(permissions, str(step["permission"])):
        raise NotAuthorisedForStep(
            f"Approving {step['name']!r} needs {step['permission']}."
        )

    # Steps are taken in order. Approving the board's step before the
    # department has seen it is not an approval, it is a shortcut around one.
    for earlier in workflow.steps:
        if str(earlier["key"]) == step_key:
            break
        if str(earlier["name"]) in outstanding_steps(db, result_set):
            raise AssessmentError(
                f"{earlier['name']!r} has not been approved yet."
            )

    db.add(
        ApprovalRecord(
            result_set_id=result_set.id,
            step_key=step_key,
            decision="approved",
            actor_membership_id=membership_id,
            reason=reason,
            occurred_at=datetime.now(UTC),
        )
    )
    db.flush()
    remaining = outstanding_steps(db, result_set)
    result_set.stage = ResultStage.approved if not remaining else ResultStage.in_review
    result_set.current_step = None if not remaining else result_set.current_step
    db.flush()
    return result_set


def return_for_changes(
    db: Session,
    result_set: ResultSet,
    *,
    step_key: str,
    membership_id: uuid.UUID,
    reason: str,
) -> ResultSet:
    """Send it back. Recorded, because a delay has to be explainable."""
    if not (reason or "").strip():
        raise AssessmentError("Returning a result set needs a reason.")
    db.add(
        ApprovalRecord(
            result_set_id=result_set.id,
            step_key=step_key,
            decision="returned",
            actor_membership_id=membership_id,
            reason=reason.strip(),
            occurred_at=datetime.now(UTC),
        )
    )
    result_set.stage = ResultStage.draft
    db.flush()
    return result_set


# --- publication ------------------------------------------------------------


@dataclass(slots=True)
class Publication:
    result_set_id: uuid.UUID
    published: int = 0
    entries: list[uuid.UUID] = field(default_factory=list)


def publish(
    db: Session,
    result_set: ResultSet,
    *,
    membership_id: uuid.UUID,
    permissions: frozenset[str],
    force: bool = False,
    force_reason: str | None = None,
) -> Publication:
    """Make it official. Snapshots the mark *and* the grading it was given.

    Refuses without the approvals the institution's own workflow requires — and
    `force` is not a way round that. Force covers the readiness warnings a
    school may legitimately overrule (a missing mark for a child who left), and
    demands a reason; the workflow is not overrulable at all, because an
    approval nobody gave is not an approval.
    """
    from app.modules.authz import permissions as perms

    if not perms.has(permissions, "assessment.result.publish"):
        raise NotAuthorisedForStep("Publishing results needs assessment.result.publish.")
    if result_set.stage is ResultStage.published:
        raise AssessmentError("That result set is already published.")

    outstanding = outstanding_steps(db, result_set)
    if outstanding:
        raise AssessmentError(
            "These approvals have not been given: " + ", ".join(outstanding)
        )

    state = readiness(db, result_set)
    if not state.is_ready:
        if not force:
            raise AssessmentError(
                "Not ready to publish:\n" + "\n".join(f"  · {p}" for p in state.problems)
            )
        if not (force_reason or "").strip():
            raise AssessmentError(
                "Publishing over these warnings needs a reason: "
                + "; ".join(state.problems)
            )

    now = datetime.now(UTC)
    published = Publication(result_set_id=result_set.id)

    from app.modules.academics import service as academics

    covered = _assessments_for(db, result_set)
    already = _already_published(db, [a.id for a in covered])

    for assessment in covered:
        scale = academics.grading_scale(db, assessment.grading_scale_id)
        # The course's credit value *as it stands at publication*, frozen onto
        # every row below. Reading it at transcript time instead would make a
        # graduate's total change whenever a department revalued a module.
        subject = academics.course(db, assessment.course_id)
        credits = subject.credits if subject else None
        unit_label = ""
        if credits is not None:
            unit_label, _plural = academics.credit_unit_label(
                db, subject.credit_system_id
            )
        rows = db.execute(
            select(AssessmentScore).where(AssessmentScore.assessment_id == assessment.id)
        ).scalars().all()
        for row in rows:
            if (assessment.id, row.student_relationship_id) in already:
                # Published once, in an earlier set. Publishing it again would
                # give one mark two official results, and a transcript would
                # count it twice. A correction to a published mark is an
                # amendment, not a second publication.
                continue
            value = row.effective_score
            band = scale.band_for(float(value)) if scale and value is not None else None
            entry = PublishedResult(
                result_set_id=result_set.id,
                student_relationship_id=row.student_relationship_id,
                assessment_id=assessment.id,
                course_id=assessment.course_id,
                score=value,
                max_score=assessment.max_score,
                band_label=band.label if band else None,
                points=band.points if band else None,
                is_pass=band.is_pass if band else None,
                is_absent=row.is_absent,
                grading_scale_code=scale.code if scale else None,
                credits=credits,
                credit_unit_label=unit_label or None,
                weight=assessment.weight,
                comment=row.comment,
                published_at=now,
            )
            db.add(entry)
            db.flush()
            published.entries.append(entry.id)
            published.published += 1

    if published.published == 0 and already:
        raise AssessmentError(
            "Every mark this set covers has already been published. Correct a "
            "published result with an amendment rather than by publishing it "
            "again — two official results for one mark is a transcript that "
            "counts it twice."
        )

    result_set.stage = ResultStage.published
    result_set.published_at = now
    result_set.published_by_membership_id = membership_id
    db.flush()
    record(
        db,
        action=AuditAction.publish,
        resource_type="result_set",
        resource_id=result_set.id,
        after={"published": str(published.published)},
        reason=force_reason if force else None,
        actor_membership_id=membership_id,
    )
    return published


def results_for(
    db: Session,
    student_relationship_id: uuid.UUID,
    *,
    period_ids: Sequence[uuid.UUID] | None = None,
) -> list[PublishedResult]:
    """A student's official record — only what was published.

    `period_ids` narrows to particular terms, which is what a report card asks
    for and a transcript does not. The period comes from the *result set* rather
    than from the assessment: an institution that publishes a January resit
    against the autumn term has said which term it belongs to, and the
    assessment's own period would contradict it.
    """
    statement = select(PublishedResult).where(
        PublishedResult.student_relationship_id == student_relationship_id
    )
    if period_ids is not None:
        ids = list(period_ids)
        if not ids:
            return []
        statement = statement.where(
            PublishedResult.result_set_id.in_(
                select(ResultSet.id).where(ResultSet.academic_period_id.in_(ids))
            )
        )
    return list(
        db.execute(statement.order_by(PublishedResult.published_at)).scalars().all()
    )


def results_with_periods(
    db: Session,
    student_relationship_id: uuid.UUID,
    *,
    period_ids: Sequence[uuid.UUID] | None = None,
) -> list[tuple[PublishedResult, uuid.UUID | None]]:
    """Published results paired with the period each belongs to.

    The pairing comes from the *result set* rather than from the assessment: an
    institution that publishes a January resit against the autumn term has said
    which term it counts for, and the assessment's own period would contradict
    it. One query, because a transcript otherwise asks this question once per
    result.
    """
    statement = (
        select(PublishedResult, ResultSet.academic_period_id)
        .join(ResultSet, ResultSet.id == PublishedResult.result_set_id)
        .where(PublishedResult.student_relationship_id == student_relationship_id)
    )
    if period_ids is not None:
        ids = list(period_ids)
        if not ids:
            return []
        statement = statement.where(ResultSet.academic_period_id.in_(ids))
    return [
        (row[0], row[1])
        for row in db.execute(
            statement.order_by(PublishedResult.published_at)
        ).all()
    ]


def assessment_summaries(
    db: Session, assessment_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, dict]:
    """Enough about each assessment to name it on a document."""
    ids = [i for i in assessment_ids if i is not None]
    if not ids:
        return {}
    rows = db.execute(
        select(
            Assessment.id,
            Assessment.code,
            Assessment.name,
            Assessment.kind_label,
            Assessment.course_id,
        ).where(Assessment.id.in_(ids))
    ).all()
    return {
        row[0]: {
            "code": row[1],
            "name": row[2],
            "kind_label": row[3],
            "course_id": row[4],
        }
        for row in rows
    }


def amendment_counts(
    db: Session, published_result_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """How many times each of these results has been corrected.

    Used by the document engine to tell whether a document issued earlier has
    been overtaken by a correction. Counting rather than fetching, because the
    question is "has this changed since?" and the answer is a number.
    """
    ids = list(published_result_ids)
    if not ids:
        return {}
    rows = db.execute(
        select(ResultAmendment.published_result_id, func.count())
        .where(ResultAmendment.published_result_id.in_(ids))
        .group_by(ResultAmendment.published_result_id)
    ).all()
    return {row[0]: row[1] for row in rows}


# --- correcting what has been published ------------------------------------


def amend(
    db: Session,
    entry: PublishedResult,
    *,
    membership_id: uuid.UUID,
    permissions: frozenset[str],
    reason: str,
    score: float | None = None,
    band_label: str | None = None,
    comment: str | None = None,
) -> ResultAmendment:
    """Correct an official record, keeping what it said before.

    Three things are required and none is negotiable: the authority to approve
    results, a reason, and the previous value. A correction without the first is
    somebody changing a record they may not; without the second it is an anomaly
    nobody can explain; without the third the institution can no longer say what
    it originally published, which is the question an appeal actually asks.
    """
    from app.modules.authz import permissions as perms

    if not perms.has(permissions, "assessment.result.approve"):
        raise NotAuthorisedForStep(
            "Amending a published result needs assessment.result.approve."
        )
    if not (reason or "").strip():
        raise AssessmentError(
            "Amending a published result needs a reason. Without one the change "
            "is an anomaly rather than a record."
        )
    if score is None and band_label is None and comment is None:
        raise AssessmentError("An amendment that changes nothing is not an amendment.")

    now = datetime.now(UTC)
    previous_sequence = db.execute(
        select(ResultAmendment).where(
            ResultAmendment.published_result_id == entry.id
        )
    ).scalars().all()

    amendment = ResultAmendment(
        published_result_id=entry.id,
        previous_score=entry.score,
        new_score=score if score is not None else entry.score,
        previous_band_label=entry.band_label,
        new_band_label=band_label if band_label is not None else entry.band_label,
        previous_comment=entry.comment,
        new_comment=comment if comment is not None else entry.comment,
        reason=reason.strip(),
        actor_membership_id=membership_id,
        occurred_at=now,
        sequence=len(previous_sequence) + 1,
    )
    db.add(amendment)

    if score is not None:
        entry.score = score
    if band_label is not None:
        entry.band_label = band_label
    if comment is not None:
        entry.comment = comment
    entry.amended_at = now
    db.flush()

    record(
        db,
        action=AuditAction.update,
        resource_type="published_result",
        resource_id=entry.id,
        before={"score": str(amendment.previous_score),
                "band": str(amendment.previous_band_label)},
        after={"score": str(amendment.new_score), "band": str(amendment.new_band_label)},
        reason=reason.strip(),
        actor_membership_id=membership_id,
    )
    return amendment


def amendments_for(db: Session, published_result_id: uuid.UUID) -> list[ResultAmendment]:
    return list(
        db.execute(
            select(ResultAmendment)
            .where(ResultAmendment.published_result_id == published_result_id)
            .order_by(ResultAmendment.sequence)
        ).scalars().all()
    )
