"""Journeys 4 and 5: results are approved, published, and corrected honestly.

The distinction this suite defends is the one every school depends on and most
systems never draw:

    a **score** is what a teacher entered — working, revisable, theirs
    a **result** is what the institution has said — official, immutable, quoted

Most of what follows is an attempt to blur that line and fail. The seven attacks
are the ones named in the brief: mutating a published result, correcting without
authority, correcting without a reason, correcting without keeping the old
value, a correction with no audit event, reading another institution's results,
and publishing without the approvals the institution requires.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

from app.modules.academics.models import (
    AcademicPeriod,
    AcademicStage,
    AcademicYear,
    ClassGroup,
    Course,
    GradingBand,
    GradingScale,
    Level,
    ScaleKind,
    TeachingAllocation,
)
from app.modules.assessment import scopes as assessment_scopes
from app.modules.assessment import service as assessment
from app.modules.assessment.models import (
    Assessment,
    AssessmentStatus,
    PublishedResult,
    ResultSet,
    ResultStage,
)
from app.modules.authz import permissions as perms
from app.modules.authz.predicates import scoped_select
from app.modules.authz.scopes import ScopeKind
from app.modules.people import service as people
from app.modules.people.service import Placement
from app.tests.conftest import TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db

TEACHER = perms.expand({"assessment.score.write", "assessment.assessment.write"})
PRINCIPAL = perms.expand({"assessment.result.approve", "assessment.result.publish",
                          "assessment.result.read"})
COORDINATOR = perms.expand({"assessment.result.approve", "assessment.result.read"})


class World:
    def __init__(self, fixture: TenantFixture, **ids: object) -> None:
        self.fixture = fixture
        self.__dict__.update(ids)

    def session(self):
        return self.fixture.session()


def _build(slug: str) -> World:
    fixture = _provision(slug)
    session = fixture.session()
    try:
        stage = AcademicStage(code="upper", name="Upper", sequence=0)
        session.add(stage)
        session.flush()
        level = Level(code="y10", name="Year 10", sequence=0, stage_id=stage.id)
        session.add(level)
        session.flush()
        year = AcademicYear(name="2026", code="2026", starts_on=date(2026, 9, 1),
                            ends_on=date(2027, 7, 31), is_current=True)
        session.add(year)
        session.flush()
        period = AcademicPeriod(academic_year_id=year.id, name="Autumn Term",
                                kind_label="Term", sequence=1,
                                starts_on=date(2026, 9, 1), ends_on=date(2026, 12, 18),
                                is_current=True)
        session.add(period)
        session.flush()
        group = ClassGroup(code="10a", name="10A", level_id=level.id,
                           academic_year_id=year.id)
        other = ClassGroup(code="10b", name="10B", level_id=level.id,
                           academic_year_id=year.id)
        session.add_all([group, other])
        session.flush()

        scale = GradingScale(code="letters", name="Letters", kind=ScaleKind.letter,
                             is_default=True)
        session.add(scale)
        session.flush()
        for label, low, high, points, is_pass in (
            ("A", 70, 100, 5, True), ("B", 60, 69.99, 4, True),
            ("C", 50, 59.99, 3, True), ("F", 0, 49.99, 0, False),
        ):
            session.add(GradingBand(scale_id=scale.id, label=label, min_value=low,
                                    max_value=high, points=points, is_pass=is_pass))
        course = Course(code="chem", name="Chemistry", is_core=True,
                        grading_scale_id=scale.id)
        session.add(course)
        session.flush()

        students: dict[str, _uuid.UUID] = {}
        for name in ("Ada Nwosu", "Bilal Haddad", "Carla Mendes"):
            person = people.record_person(session, full_name=name)
            student = people.register_student(session, person, reference=f"S-{name[:3]}")
            placement = people.admit(
                session, student, on=date(2026, 9, 1),
                placement=Placement(academic_year_id=year.id, level_id=level.id,
                                    class_group_id=group.id),
            )
            people.enrol(session, placement, on=date(2026, 9, 1))
            students[name] = student.id

        exam = Assessment(
            code="chem-t1", name="Chemistry Test 1", kind_label="Test",
            course_id=course.id, class_group_id=group.id,
            academic_period_id=period.id, max_score=100,
            grading_scale_id=scale.id, status=AssessmentStatus.open,
        )
        session.add(exam)
        session.flush()

        result_set = ResultSet(
            code="autumn-10a", name="Autumn Term, 10A",
            academic_period_id=period.id, class_group_id=group.id,
        )
        session.add(result_set)
        session.flush()
        session.commit()

        return World(
            fixture, class_id=group.id, other_class_id=other.id, course_id=course.id,
            period_id=period.id, scale_id=scale.id, assessment_id=exam.id,
            result_set_id=result_set.id, students=students,
        )
    finally:
        session.close()


@pytest.fixture(scope="module")
def world() -> World:
    return _build("results-school")


def _mark_everybody(session, world: World, marks: dict[str, float]) -> None:
    exam = session.get(Assessment, world.assessment_id)
    # Reopened first: the module fixture is shared, and an earlier test may have
    # closed it. Reopening is a fixture concern rather than a production path —
    # `test_a_teachers_mark_is_revisable_until_the_assessment_closes` asserts
    # that the closed state genuinely refuses new marks.
    exam.status = AssessmentStatus.open
    session.flush()
    assessment.enter_scores(
        session, exam,
        {world.students[name]: value for name, value in marks.items()},
        membership_id=_uuid.uuid4(),
    )
    exam.status = AssessmentStatus.closed
    session.flush()


def _ready_set(session, world: World, marks: dict[str, float] | None = None) -> ResultSet:
    """Marks entered, and a *fresh* result set to publish them into.

    Fresh rather than shared: publication is terminal, so a suite that reused
    one result set would be asserting the order its own tests happen to run in
    rather than the behaviour of the code.
    """
    _mark_everybody(session, world, marks or {"Ada Nwosu": 82, "Bilal Haddad": 64,
                                              "Carla Mendes": 41})
    result_set = ResultSet(
        code=f"set-{_uuid.uuid4().hex[:8]}",
        name="Autumn Term, 10A",
        academic_period_id=world.period_id,
        class_group_id=world.class_id,
    )
    session.add(result_set)
    session.flush()
    return result_set


# --- entering marks ---------------------------------------------------------


def test_a_mark_above_the_maximum_is_refused(world: World) -> None:
    """A 105 out of 100 becomes a published result if nothing catches it."""
    session = world.session()
    try:
        exam = session.get(Assessment, world.assessment_id)
        with pytest.raises(assessment.AssessmentError):
            assessment.enter_scores(
                session, exam, {world.students["Ada Nwosu"]: 105}
            )
        with pytest.raises(assessment.AssessmentError):
            assessment.enter_scores(
                session, exam, {world.students["Ada Nwosu"]: -1}
            )
    finally:
        session.rollback()
        session.close()


def test_a_teachers_mark_is_revisable_until_the_assessment_closes(
    world: World
) -> None:
    """This is the row a teacher fixes when they misread a 6 as a 5."""
    session = world.session()
    try:
        exam = session.get(Assessment, world.assessment_id)
        ada = world.students["Ada Nwosu"]
        assessment.enter_scores(session, exam, {ada: 55})
        assessment.enter_scores(session, exam, {ada: 65})
        from app.modules.assessment.models import AssessmentScore

        row = session.execute(
            select(AssessmentScore).where(
                AssessmentScore.assessment_id == exam.id,
                AssessmentScore.student_relationship_id == ada,
            )
        ).scalars().one()
        assert float(row.score) == 65
        # Nothing has been published, so nothing was amended.
        assert session.execute(select(PublishedResult)).scalars().all() == []

        exam.status = AssessmentStatus.closed
        session.flush()
        with pytest.raises(assessment.AssessmentError):
            assessment.enter_scores(session, exam, {ada: 70})
    finally:
        session.rollback()
        session.close()


def test_moderation_keeps_both_numbers(world: World) -> None:
    """A moderation that overwrote the original would destroy the evidence.

    That evidence is the only reason a department asks for moderation at all.
    """
    session = world.session()
    try:
        exam = session.get(Assessment, world.assessment_id)
        ada = world.students["Ada Nwosu"]
        assessment.enter_scores(session, exam, {ada: 55})
        assessment.moderate(session, exam, {ada: 62},
                            membership_id=_uuid.uuid4(), note="Second marker")
        from app.modules.assessment.models import AssessmentScore

        row = session.execute(
            select(AssessmentScore).where(
                AssessmentScore.assessment_id == exam.id,
                AssessmentScore.student_relationship_id == ada,
            )
        ).scalars().one()
        assert float(row.score) == 55
        assert float(row.moderated_score) == 62
        assert float(row.effective_score) == 62, "the moderator's mark must count"
    finally:
        session.rollback()
        session.close()


# --- what stands in the way of publishing ----------------------------------


def test_readiness_lists_problems_rather_than_saying_no(world: World) -> None:
    """"Not ready" is useless at four o'clock on results day."""
    session = world.session()
    try:
        result_set = session.get(ResultSet, world.result_set_id)
        state = assessment.readiness(session, result_set)
        assert not state.is_ready
        assert state.missing_marks or state.open_assessments
        assert all(isinstance(problem, str) and problem for problem in state.problems)
    finally:
        session.rollback()
        session.close()


def test_publication_refuses_while_marks_are_missing(world: World) -> None:
    session = world.session()
    try:
        result_set = session.get(ResultSet, world.result_set_id)
        with pytest.raises(assessment.AssessmentError) as caught:
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL)
        assert "Not ready" in str(caught.value)
    finally:
        session.rollback()
        session.close()


def test_publishing_over_a_warning_needs_a_reason() -> None:
    """A school may knowingly publish with a mark missing for a child who left.

    What it may not do is publish without being told, or without saying why.

    Its own school, because the point of the test is a *deliberately incomplete*
    set of marks, and a shared fixture that any other test may have completed
    would make this assert the suite's ordering rather than the behaviour.
    """
    world = _build("results-partial")
    session = world.session()
    try:
        exam = session.get(Assessment, world.assessment_id)
        assessment.enter_scores(session, exam, {world.students["Ada Nwosu"]: 80})
        exam.status = AssessmentStatus.closed
        session.flush()
        result_set = session.get(ResultSet, world.result_set_id)

        with pytest.raises(assessment.AssessmentError):
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL, force=True)
        published = assessment.publish(
            session, result_set, membership_id=_uuid.uuid4(), permissions=PRINCIPAL,
            force=True, force_reason="Two pupils left in November; marks not sat.",
        )
        assert published.published >= 1
    finally:
        session.rollback()
        session.close()


# --- the workflow is the institution's -------------------------------------


def test_a_school_and_a_university_approve_differently(world: World) -> None:
    """Two steps and four steps, from the same machine."""
    session = world.session()
    try:
        school = assessment.define_workflow(
            session, code="school", name="Teacher then Principal",
            steps=[
                {"key": "teacher", "name": "Teacher",
                 "permission": "assessment.score.write"},
                {"key": "principal", "name": "Principal",
                 "permission": "assessment.result.approve"},
            ],
        )
        university = assessment.define_workflow(
            session, code="university", name="Lecturer to Board",
            steps=[
                {"key": "lecturer", "name": "Lecturer",
                 "permission": "assessment.score.write"},
                {"key": "coordinator", "name": "Programme Coordinator",
                 "permission": "assessment.result.approve"},
                {"key": "department", "name": "Department",
                 "permission": "assessment.result.approve"},
                {"key": "board", "name": "Examination Board",
                 "permission": "assessment.result.publish"},
            ],
        )
        assert len(school.steps) == 2
        assert len(university.steps) == 4
        assert [s["name"] for s in university.steps][-1] == "Examination Board"
    finally:
        session.rollback()
        session.close()


def test_a_workflow_naming_an_unknown_permission_is_refused(world: World) -> None:
    """Fails when somebody configures it, not at the end of term."""
    session = world.session()
    try:
        with pytest.raises(perms.UnknownPermission):
            assessment.define_workflow(
                session, code="broken", name="Broken",
                steps=[{"key": "a", "name": "A", "permission": "not.a.permission"}],
            )
    finally:
        session.rollback()
        session.close()


def test_an_institution_with_no_workflow_publishes_in_one_action(
    world: World
) -> None:
    """A small school where the head enters and publishes must not need a committee."""
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assert assessment.outstanding_steps(session, result_set) == []
        published = assessment.publish(
            session, result_set, membership_id=_uuid.uuid4(), permissions=PRINCIPAL
        )
        assert published.published == 3
    finally:
        session.rollback()
        session.close()


def test_a_step_cannot_be_taken_by_somebody_without_its_permission(
    world: World
) -> None:
    """Seniority is not the question. The step's permission is."""
    session = world.session()
    try:
        workflow = assessment.define_workflow(
            session, code="two-step", name="Two step", is_default=True,
            steps=[
                {"key": "coordinator", "name": "Coordinator",
                 "permission": "assessment.result.approve"},
                {"key": "board", "name": "Board",
                 "permission": "assessment.result.publish"},
            ],
        )
        result_set = _ready_set(session, world)
        result_set.workflow_id = workflow.id
        assessment.submit_for_review(session, result_set)

        with pytest.raises(assessment.NotAuthorisedForStep):
            assessment.approve_step(
                session, result_set, step_key="board",
                membership_id=_uuid.uuid4(), permissions=COORDINATOR,
            )
    finally:
        session.rollback()
        session.close()


def test_steps_are_taken_in_order(world: World) -> None:
    """Approving the board's step first is not an approval, it is a shortcut."""
    session = world.session()
    try:
        workflow = assessment.define_workflow(
            session, code="ordered", name="Ordered", is_default=True,
            steps=[
                {"key": "coordinator", "name": "Coordinator",
                 "permission": "assessment.result.approve"},
                {"key": "board", "name": "Board",
                 "permission": "assessment.result.publish"},
            ],
        )
        result_set = _ready_set(session, world)
        result_set.workflow_id = workflow.id
        assessment.submit_for_review(session, result_set)
        with pytest.raises(assessment.AssessmentError) as caught:
            assessment.approve_step(
                session, result_set, step_key="board",
                membership_id=_uuid.uuid4(), permissions=PRINCIPAL,
            )
        assert "Coordinator" in str(caught.value)
    finally:
        session.rollback()
        session.close()


def test_returning_a_set_makes_its_step_outstanding_again(world: World) -> None:
    """Sending work back is the point of a review."""
    session = world.session()
    try:
        workflow = assessment.define_workflow(
            session, code="returnable", name="Returnable", is_default=True,
            steps=[{"key": "coordinator", "name": "Coordinator",
                    "permission": "assessment.result.approve"}],
        )
        result_set = _ready_set(session, world)
        result_set.workflow_id = workflow.id
        assessment.submit_for_review(session, result_set)
        assessment.approve_step(session, result_set, step_key="coordinator",
                                membership_id=_uuid.uuid4(), permissions=COORDINATOR)
        assert assessment.outstanding_steps(session, result_set) == []

        assessment.return_for_changes(
            session, result_set, step_key="coordinator",
            membership_id=_uuid.uuid4(), reason="Chemistry marks look transposed",
        )
        assert assessment.outstanding_steps(session, result_set) == ["Coordinator"]
        with pytest.raises(assessment.AssessmentError):
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL)
        # And the refusal is on the record, with its reason.
        history = assessment.approvals(session, result_set)
        assert [a.decision for a in history] == ["approved", "returned"]
        assert "transposed" in history[-1].reason
    finally:
        session.rollback()
        session.close()


# --- publication is a snapshot ---------------------------------------------


def test_publishing_snapshots_the_grading_it_gave(world: World) -> None:
    """The band, the points and the pass flag are copied, not referenced."""
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        entries = {
            e.student_relationship_id: e
            for e in session.execute(select(PublishedResult)).scalars().all()
        }
        ada = entries[world.students["Ada Nwosu"]]
        assert float(ada.score) == 82
        assert ada.band_label == "A"
        assert ada.is_pass is True
        assert ada.grading_scale_code == "letters"
        carla = entries[world.students["Carla Mendes"]]
        assert carla.band_label == "F"
        assert carla.is_pass is False
    finally:
        session.rollback()
        session.close()


def test_changing_the_grading_scale_does_not_change_history(world: World) -> None:
    """The attack this whole design exists to defeat.

    A school moves its grade boundaries in the summer. A transcript reprinted
    afterwards must still say what it said — a result recomputed from a live
    scale would silently rewrite every award the institution ever made.
    """
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        ada_entry = session.execute(
            select(PublishedResult).where(
                PublishedResult.student_relationship_id == world.students["Ada Nwosu"]
            )
        ).scalars().one()
        assert ada_entry.band_label == "A"

        # The school raises the A boundary from 70 to 90.
        band = session.execute(
            select(GradingBand).where(
                GradingBand.scale_id == world.scale_id, GradingBand.label == "A"
            )
        ).scalars().one()
        band.min_value = 90
        session.flush()

        session.refresh(ada_entry)
        assert ada_entry.band_label == "A", (
            "a published award changed because the school moved a boundary"
        )
        assert float(ada_entry.score) == 82
    finally:
        session.rollback()
        session.close()


def test_a_published_set_cannot_be_published_twice(world: World) -> None:
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        with pytest.raises(assessment.AssessmentError):
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL)
    finally:
        session.rollback()
        session.close()


def test_publishing_needs_the_publish_permission(world: World) -> None:
    """Approving is not publishing. They are separate acts by separate people."""
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        with pytest.raises(assessment.NotAuthorisedForStep):
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=COORDINATOR)
    finally:
        session.rollback()
        session.close()


# --- the seven attacks ------------------------------------------------------


def test_a_published_result_cannot_be_deleted(world: World) -> None:
    """It happened, and it was relied on."""
    session = world.session()
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("DELETE FROM published_results"))
        session.rollback()
    finally:
        session.close()


def test_the_amendment_ledger_cannot_be_rewritten(world: World) -> None:
    session = world.session()
    try:
        for table in ("result_amendments", "approval_records"):
            with pytest.raises(ProgrammingError):
                session.execute(text(f"UPDATE {table} SET reason = 'x'"))
            session.rollback()
            with pytest.raises(ProgrammingError):
                session.execute(text(f"DELETE FROM {table}"))
            session.rollback()
    finally:
        session.close()


def test_an_amendment_without_authority_is_refused(world: World) -> None:
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        entry = session.execute(select(PublishedResult)).scalars().first()
        with pytest.raises(assessment.NotAuthorisedForStep):
            assessment.amend(session, entry, membership_id=_uuid.uuid4(),
                             permissions=TEACHER, reason="Remarked", score=90)
    finally:
        session.rollback()
        session.close()


def test_an_amendment_without_a_reason_is_refused(world: World) -> None:
    """Without one the change is an anomaly rather than a record."""
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        entry = session.execute(select(PublishedResult)).scalars().first()
        with pytest.raises(assessment.AssessmentError):
            assessment.amend(session, entry, membership_id=_uuid.uuid4(),
                             permissions=PRINCIPAL, reason="   ", score=90)
    finally:
        session.rollback()
        session.close()


def test_an_amendment_keeps_what_the_record_said_before(world: World) -> None:
    """The question an appeal actually asks is what was originally published."""
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        entry = session.execute(
            select(PublishedResult).where(
                PublishedResult.student_relationship_id == world.students["Carla Mendes"]
            )
        ).scalars().one()
        assert entry.band_label == "F"

        actor = _uuid.uuid4()
        amendment = assessment.amend(
            session, entry, membership_id=actor, permissions=PRINCIPAL,
            reason="Remark after appeal: question 4 was marked twice",
            score=58, band_label="C",
        )
        session.flush()

        assert float(amendment.previous_score) == 41
        assert float(amendment.new_score) == 58
        assert amendment.previous_band_label == "F"
        assert amendment.new_band_label == "C"
        assert amendment.actor_membership_id == actor
        assert amendment.occurred_at is not None
        assert "question 4" in amendment.reason

        assert float(entry.score) == 58
        assert entry.band_label == "C"
        assert entry.amended_at is not None, "the record does not show it changed"

        history = assessment.amendments_for(session, entry.id)
        assert [a.sequence for a in history] == [1]
    finally:
        session.rollback()
        session.close()


def test_an_amendment_leaves_an_audit_event(world: World) -> None:
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        entry = session.execute(select(PublishedResult)).scalars().first()
        assessment.amend(session, entry, membership_id=_uuid.uuid4(),
                         permissions=PRINCIPAL, reason="Clerical error", score=71)
        # Flushed rather than committed: the audit event is written on this
        # session, and committing a publication into a module-scoped world makes
        # every later test in the file depend on this one having run.
        session.flush()

        rows = session.execute(
            text(
                "SELECT action, reason FROM audit_events "
                "WHERE resource_type = 'published_result' AND resource_id = :id"
            ),
            {"id": entry.id},
        ).all()
        assert rows, "a published result was corrected with no audit event"
        assert any("Clerical error" in (row[1] or "") for row in rows)
    finally:
        session.rollback()
        session.close()


def test_publication_without_the_required_approvals_is_refused(
    world: World
) -> None:
    """An approval nobody gave is not an approval, and force does not cover it."""
    session = world.session()
    try:
        workflow = assessment.define_workflow(
            session, code="strict", name="Strict", is_default=True,
            steps=[{"key": "board", "name": "Board",
                    "permission": "assessment.result.publish"}],
        )
        result_set = _ready_set(session, world)
        result_set.workflow_id = workflow.id
        assessment.submit_for_review(session, result_set)

        with pytest.raises(assessment.AssessmentError) as caught:
            assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL)
        assert "Board" in str(caught.value)

        # `force` covers readiness warnings, never the workflow.
        with pytest.raises(assessment.AssessmentError) as forced:
            assessment.publish(
                session, result_set, membership_id=_uuid.uuid4(),
                permissions=PRINCIPAL, force=True, force_reason="In a hurry",
            )
        assert "Board" in str(forced.value)
    finally:
        session.rollback()
        session.close()


def test_results_do_not_cross_institutions() -> None:
    """A published result is the most quoted record a school holds."""
    theirs = _build("results-other")
    session = theirs.session()
    try:
        result_set = _ready_set(session, theirs)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        session.commit()
        entry_id = session.execute(select(PublishedResult)).scalars().first().id
    finally:
        session.close()

    stranger = _provision("results-stranger").session()
    try:
        assert stranger.get(PublishedResult, entry_id) is None
        assert (
            stranger.execute(
                text("SELECT count(*) FROM published_results WHERE id = :id"),
                {"id": entry_id},
            ).scalar_one()
            == 0
        )
    finally:
        stranger.close()


# --- scope: a draft is a teacher's, a result is a family's -----------------


def test_a_guardian_reaches_published_results_but_never_a_draft_score() -> None:
    """A parent reading a working score would be reading a mark before the
    institution had decided it was right — which is the whole reason the two
    tables are separate."""
    assert ScopeKind.own_children in assessment_scopes.PUBLISHED_RESULTS.clauses
    assert ScopeKind.own_children not in assessment_scopes.SCORES.clauses
    assert ScopeKind.self_only in assessment_scopes.PUBLISHED_RESULTS.clauses
    assert ScopeKind.self_only not in assessment_scopes.SCORES.clauses


def test_a_teacher_reaches_the_scores_of_classes_they_teach(world: World) -> None:
    from app.core.context import Grant, Principal
    from app.modules.assessment.models import AssessmentScore
    from app.modules.identity.models import Membership, MembershipStatus, User

    session = world.session()
    try:
        _mark_everybody(session, world, {"Ada Nwosu": 70})
        user = User(email=f"t-{_uuid.uuid4().hex[:6]}@results.test", full_name="T")
        session.add(user)
        session.flush()
        membership = Membership(user_id=user.id, status=MembershipStatus.active)
        session.add(membership)
        session.flush()
        session.add(TeachingAllocation(membership_id=membership.id,
                                       class_group_id=world.class_id))
        session.commit()

        teacher = Principal(
            user_id=user.id, membership_id=membership.id,
            tenant_id=world.fixture.tenant_id,
            permissions=TEACHER,
            grants=(Grant(frozenset({"assessment.score.write"}),
                          ScopeKind.taught_by_self.value, ()),),
            session_id=_uuid.uuid4(),
            authenticated_at=datetime.now(UTC).timestamp(),
        )
        visible = session.execute(
            scoped_select(AssessmentScore, assessment_scopes.SCORES, db=session,
                          principal=teacher, permission="assessment.score.write")
        ).scalars().all()
        assert visible, "a teacher could not see the marks of a class they teach"

        nobody = session.execute(
            scoped_select(AssessmentScore, assessment_scopes.SCORES, db=session,
                          principal=None, permission="assessment.score.write")
        ).scalars().all()
        assert nobody == []
    finally:
        session.rollback()
        session.close()


def test_a_score_is_not_a_result(world: World) -> None:
    """Stated as a structural fact, because everything else depends on it."""
    from app.modules.assessment.models import AssessmentScore

    assert AssessmentScore.__tablename__ != PublishedResult.__tablename__
    columns = {c.key for c in PublishedResult.__table__.columns}
    # The snapshot columns: a published result explains itself without the
    # scale, the assessment or the score it came from.
    assert {"band_label", "points", "is_pass", "grading_scale_code", "max_score"} <= columns


def test_the_stage_is_terminal_at_published(world: World) -> None:
    session = world.session()
    try:
        result_set = _ready_set(session, world)
        assessment.publish(session, result_set, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        assert result_set.stage is ResultStage.published
        assert ResultStage.published.is_official
        with pytest.raises(assessment.AssessmentError):
            assessment.submit_for_review(session, result_set)
    finally:
        session.rollback()
        session.close()


def test_a_second_result_set_does_not_republish_what_is_already_official(
    world: World,
) -> None:
    """Found by the document engine, which reads results as a list.

    A result set covers a period and a class rather than a list of assessments,
    which is right — a results day is a decision about a cohort. It also means a
    second set over the same period and class sweeps up whatever the first one
    published. Without a guard, a January resit republishes the whole autumn
    term and every mark appears twice on the transcript.
    """
    session = world.session()
    try:
        first = _ready_set(session, world)
        assessment.publish(session, first, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)
        published_first = session.execute(
            select(PublishedResult).where(PublishedResult.result_set_id == first.id)
        ).scalars().all()
        assert published_first

        second = _ready_set(session, world)
        with pytest.raises(assessment.AssessmentError, match="already been published"):
            assessment.publish(session, second, membership_id=_uuid.uuid4(),
                               permissions=PRINCIPAL)

        # And each mark still has exactly one official result.
        ada = world.students["Ada Nwosu"]
        assert len(
            session.execute(
                select(PublishedResult).where(
                    PublishedResult.student_relationship_id == ada
                )
            ).scalars().all()
        ) == 1
    finally:
        session.rollback()
        session.close()


def test_a_late_assessment_publishes_without_republishing_the_term(
    world: World,
) -> None:
    """The legitimate second set: one new assessment, and only that one."""
    session = world.session()
    try:
        first = _ready_set(session, world)
        assessment.publish(session, first, membership_id=_uuid.uuid4(),
                           permissions=PRINCIPAL)

        resit = Assessment(
            code=f"resit-{_uuid.uuid4().hex[:6]}", name="Chemistry Resit",
            kind_label="Resit", course_id=world.course_id,
            class_group_id=world.class_id, academic_period_id=world.period_id,
            max_score=100, grading_scale_id=world.scale_id,
            status=AssessmentStatus.open,
        )
        session.add(resit)
        session.flush()
        assessment.enter_scores(
            session, resit, {world.students["Carla Mendes"]: 58}
        )
        resit.status = AssessmentStatus.closed

        second = ResultSet(
            code=f"late-{_uuid.uuid4().hex[:8]}", name="January resits",
            academic_period_id=world.period_id, class_group_id=world.class_id,
        )
        session.add(second)
        session.flush()
        published = assessment.publish(
            session, second, membership_id=_uuid.uuid4(), permissions=PRINCIPAL,
            force=True, force_reason="Only the resit candidates were marked.",
        )
        assert published.published == 1

        rows = session.execute(
            select(PublishedResult).where(
                PublishedResult.result_set_id == second.id
            )
        ).scalars().all()
        assert {r.assessment_id for r in rows} == {resit.id}
    finally:
        session.rollback()
        session.close()
