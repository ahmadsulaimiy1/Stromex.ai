"""One engine, three institutions, and the question a registrar is asked in 2031.

The suite is organised around the claim the document engine makes, which is
larger than it looks: **a report card, a transcript and a certificate are the
same machine with different rows**, and **an issued document says what it said**.

Most of what follows attacks the second claim, because it is the one that fails
silently. A grading scale is edited, a course is revalued, a school renames its
vocabulary, a result is corrected, the institution rebrands — and the test asks
whether the document issued before any of that still reads the same. A system
that recomposes on reprint passes none of these and looks perfectly healthy
until somebody compares two copies of the same transcript.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.session import bind_tenant, get_session_factory
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
)
from app.modules.academics.structure import (
    AcademicUnit,
    CreditSystem,
    Programme,
    Qualification,
)
from app.modules.assessment import service as assessment
from app.modules.assessment.models import (
    Assessment,
    AssessmentStatus,
    PublishedResult,
    ResultSet,
)
from app.modules.attendance import service as attendance
from app.modules.authz import permissions as perms
from app.modules.authz.predicates import scoped_count, scoped_select
from app.modules.authz.scopes import ScopeKind
from app.modules.billing import service as billing
from app.modules.billing.plans import PLANS
from app.modules.customization import branding as branding_module
from app.modules.customization import terminology
from app.modules.documents import scopes as document_scopes
from app.modules.documents import sections as catalogue
from app.modules.documents import service as documents
from app.modules.documents.models import Document, DocumentStatus, TemplateStatus
from app.modules.documents.render import render_html, render_text
from app.modules.people import service as people
from app.modules.people.service import Placement
from app.tests.conftest import TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db


REGISTRAR = perms.expand(
    {
        "reporting.report_card.create",
        "reporting.report_card.read",
        "reporting.transcript.create",
        "reporting.transcript.read",
        "reporting.document.create",
        "reporting.document.read",
    }
)
REPORT_CARDS_ONLY = perms.expand(
    {"reporting.report_card.create", "reporting.report_card.read"}
)
PUBLISHER = perms.expand(
    {"assessment.result.publish", "assessment.result.approve", "assessment.result.read"}
)


@pytest.fixture(scope="module", autouse=True)
def platform() -> None:
    """Plans exist before any school subscribes to one."""
    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        billing.seed_plans(session, PLANS)
        session.commit()
    finally:
        session.close()


class World:
    def __init__(self, fixture: TenantFixture, **ids: object) -> None:
        self.fixture = fixture
        self.__dict__.update(ids)

    def session(self):
        return self.fixture.session()


# --- a school: terms, letter grades, a class, one subject ------------------


def _build_school(slug: str) -> World:
    fixture = _provision(slug)
    session = fixture.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")

        stage = AcademicStage(code="upper", name="Upper", sequence=0)
        session.add(stage)
        session.flush()
        level = Level(code="y10", name="Year 10", sequence=0, stage_id=stage.id)
        session.add(level)
        session.flush()
        year = AcademicYear(
            name="2026/27", code="2026", starts_on=date(2026, 9, 1),
            ends_on=date(2027, 7, 31), is_current=True,
        )
        session.add(year)
        session.flush()
        autumn = AcademicPeriod(
            academic_year_id=year.id, name="Autumn Term", kind_label="Term",
            sequence=1, starts_on=date(2026, 9, 1), ends_on=date(2026, 12, 18),
            is_current=True,
        )
        spring = AcademicPeriod(
            academic_year_id=year.id, name="Spring Term", kind_label="Term",
            sequence=2, starts_on=date(2027, 1, 6), ends_on=date(2027, 3, 31),
        )
        session.add_all([autumn, spring])
        session.flush()
        group = ClassGroup(code="10a", name="10A", level_id=level.id,
                           academic_year_id=year.id)
        other = ClassGroup(code="10b", name="10B", level_id=level.id,
                           academic_year_id=year.id)
        session.add_all([group, other])
        session.flush()

        scale = GradingScale(code="letters", name="School Grades",
                             kind=ScaleKind.letter, is_default=True)
        session.add(scale)
        session.flush()
        for index, (label, low, high, points, is_pass) in enumerate(
            (
                ("A", 70, 100, 5, True),
                ("B", 60, 69.99, 4, True),
                ("C", 50, 59.99, 3, True),
                ("F", 0, 49.99, 0, False),
            )
        ):
            session.add(
                GradingBand(scale_id=scale.id, label=label, min_value=low,
                            max_value=high, points=points, is_pass=is_pass,
                            sequence=index)
            )
        chemistry = Course(code="chem", name="Chemistry", is_core=True,
                           grading_scale_id=scale.id)
        history = Course(code="hist", name="History", grading_scale_id=scale.id)
        session.add_all([chemistry, history])
        session.flush()

        students: dict[str, _uuid.UUID] = {}
        for name, reference in (("Ada Nwosu", "S-001"), ("Bilal Haddad", "S-002")):
            person = people.record_person(session, full_name=name,
                                          date_of_birth=date(2011, 4, 2))
            student = people.register_student(session, person, reference=reference)
            placement = people.admit(
                session, student, on=date(2026, 9, 1),
                placement=Placement(academic_year_id=year.id, level_id=level.id,
                                    class_group_id=group.id),
            )
            people.enrol(session, placement, on=date(2026, 9, 1))
            students[name] = student.id

        session.commit()
        return World(
            fixture, year_id=year.id, autumn_id=autumn.id, spring_id=spring.id,
            level_id=level.id, class_id=group.id, other_class_id=other.id,
            scale_id=scale.id, chemistry_id=chemistry.id, history_id=history.id,
            students=students,
        )
    finally:
        session.close()


def _publish_marks(
    world: World,
    *,
    course_id: _uuid.UUID,
    period_id: _uuid.UUID,
    marks: dict[str, float],
    code: str,
    max_score: float = 100,
    weight: float = 1,
    kind_label: str = "Test",
) -> _uuid.UUID:
    """Enter marks and take them all the way through to publication."""
    session = world.session()
    try:
        exam = Assessment(
            code=f"{code}-{_uuid.uuid4().hex[:6]}", name=f"{kind_label} ({code})",
            kind_label=kind_label, course_id=course_id, class_group_id=world.class_id,
            academic_period_id=period_id, max_score=max_score, weight=weight,
            grading_scale_id=world.scale_id, status=AssessmentStatus.open,
        )
        session.add(exam)
        session.flush()
        assessment.enter_scores(
            session, exam,
            {world.students[name]: value for name, value in marks.items()},
            membership_id=world.fixture.membership_id,
        )
        exam.status = AssessmentStatus.closed
        result_set = ResultSet(
            code=f"set-{_uuid.uuid4().hex[:8]}", name="Results",
            academic_period_id=period_id, class_group_id=world.class_id,
        )
        session.add(result_set)
        session.flush()
        assessment.publish(
            session, result_set,
            membership_id=world.fixture.membership_id, permissions=PUBLISHER,
        )
        session.commit()
        return result_set.id
    finally:
        session.close()


REPORT_CARD_SECTIONS = [
    {"key": "identity", "options": {"show_date_of_birth": True}},
    {"key": "placement"},
    {
        "key": "course_results",
        "title": "Subjects",
        "options": {
            "columns": ("course", "assessments", "score", "max_score", "band", "comment"),
            "aggregate": "weighted",
        },
    },
    {"key": "attainment_summary"},
    {"key": "attendance"},
    {"key": "comments", "options": {"slots": ("class_teacher", "head")}},
    {"key": "grading_key"},
    {"key": "signatures"},
    {"key": "verification"},
]


def _offices(session) -> None:
    """A class teacher and a head, appointed with approved signatures.

    In the fixture rather than in one test, because every report card this
    suite issues should be one a real school could hand to a parent — and a
    report card nobody signed is not that. Costs two rows and makes the whole
    file evidence for the registry rather than for a path around it.
    """
    from app.modules.documents import signatories

    for code, name, holder in (
        ("tutor", "Class Teacher", "Ms O. Adeyemi"),
        ("head", "Head Teacher", "Dr N. Achebe"),
    ):
        office = signatories.declare_office(session, code=code, name=name)
        if signatories.live_appointment(session, office) is not None:
            continue
        person = people.record_person(session, full_name=holder)
        asset = signatories.record_asset(
            session, person_id=person.id, typeset_name=holder
        )
        signatories.approve_asset(session, asset, on=date(2020, 1, 1))
        signatories.appoint(
            session, office=office, person_id=person.id,
            on=date(2020, 1, 1), signature_asset_id=asset.id,
        )


def _report_card_template(session, **overrides):
    _offices(session)
    custom = dict(overrides.pop("custom", {}) or {})
    custom.setdefault("signatories", ["tutor", "head"])
    draft = documents.define_template(
        session,
        code=overrides.pop("code", "report-card"),
        name="Termly Report Card",
        purpose_label=overrides.pop("purpose_label", "Report Card"),
        purpose="report_card",
        custom=custom,
        sections=overrides.pop("sections", REPORT_CARD_SECTIONS),
        numbering=overrides.pop(
            "numbering",
            {"format": "{prefix}/{year}/{sequence:04d}", "prefix": "RC", "scope": "year"},
        ),
        **overrides,
    )
    return documents.publish_template(session, draft)


@pytest.fixture(scope="module")
def school() -> World:
    world = _build_school("documents-school")
    _publish_marks(
        world, course_id=world.chemistry_id, period_id=world.autumn_id,
        marks={"Ada Nwosu": 82, "Bilal Haddad": 55}, code="chem-t1",
    )
    _publish_marks(
        world, course_id=world.history_id, period_id=world.autumn_id,
        marks={"Ada Nwosu": 64, "Bilal Haddad": 41}, code="hist-t1",
    )
    return world


# --- template configuration -------------------------------------------------


def test_a_template_naming_a_section_nobody_wrote_is_refused(school: World) -> None:
    session = school.session()
    try:
        with pytest.raises(catalogue.UnknownSection):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad",
                sections=[{"key": "horoscope"}],
            )
    finally:
        session.rollback()
        session.close()


def test_a_template_asking_for_a_column_nobody_wrote_is_refused(school: World) -> None:
    session = school.session()
    try:
        with pytest.raises(catalogue.UnknownSection):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad",
                sections=[
                    {"key": "course_results", "options": {"columns": ("teacher_mood",)}}
                ],
            )
    finally:
        session.rollback()
        session.close()


def test_a_template_with_no_sections_prints_nothing_and_is_refused(school: World) -> None:
    session = school.session()
    try:
        with pytest.raises(catalogue.UnknownSection):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad", sections=[]
            )
    finally:
        session.rollback()
        session.close()


def test_a_number_format_that_cannot_be_filled_in_fails_at_configuration(
    school: World,
) -> None:
    """Not at the moment a registrar is printing for somebody standing there."""
    session = school.session()
    try:
        with pytest.raises(documents.DocumentError):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad",
                sections=[{"key": "identity"}],
                numbering={"format": "{registrar_name}/{sequence}"},
            )
        with pytest.raises(documents.DocumentError):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad",
                sections=[{"key": "identity"}],
                numbering={"format": "{prefix}", "scope": "whenever"},
            )
    finally:
        session.rollback()
        session.close()


def test_a_template_purpose_outside_the_three_is_refused(school: World) -> None:
    session = school.session()
    try:
        with pytest.raises(documents.DocumentError):
            documents.define_template(
                session, code="bad", name="Bad", purpose_label="Bad",
                purpose="anything_at_all", sections=[{"key": "identity"}],
            )
    finally:
        session.rollback()
        session.close()


def test_publishing_a_template_archives_the_version_it_replaces(school: World) -> None:
    session = school.session()
    try:
        code = f"versioned-{_uuid.uuid4().hex[:6]}"
        first = _report_card_template(session, code=code)
        second = documents.define_template(
            session, code=code, name="Termly Report Card",
            purpose_label="Report Card", purpose="report_card",
            sections=REPORT_CARD_SECTIONS,
        )
        documents.publish_template(session, second)
        session.flush()

        assert second.version == first.version + 1
        assert first.status is TemplateStatus.archived
        assert documents.published_template(session, code).id == second.id
    finally:
        session.rollback()
        session.close()


def test_a_document_records_which_template_version_produced_it(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"tv-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        assert issued.template_code == template.code
        assert issued.template_version == template.version
        assert issued.payload["context"]["template"]["version"] == template.version
    finally:
        session.rollback()
        session.close()


# --- one engine, three documents -------------------------------------------


def test_the_school_report_card_carries_what_a_school_report_card_carries(
    school: World,
) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"rc-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
            comments={"class_teacher": "A thoughtful term's work."},
        )
        blocks = {b["key"]: b for b in issued.payload["sections"]}

        assert blocks["identity"]["content"]["full_name"] == "Ada Nwosu"
        assert blocks["identity"]["content"]["reference"] == "S-001"
        assert blocks["placement"]["content"]["class_group"] == "10A"
        assert blocks["course_results"]["title"] == "Subjects"

        rows = {r["course"]: r for r in blocks["course_results"]["content"]["rows"]}
        assert rows["Chemistry"]["band"] == "A"
        assert rows["History"]["band"] == "B"
        assert blocks["comments"]["content"]["entries"][0]["text"] == (
            "A thoughtful term's work."
        )
        # Signed by the officers the institution appointed, not by names typed
        # into the template — see `test_authority.py`.
        signed = {s["key"]: s for s in blocks["signatures"]["content"]["signatories"]}
        assert signed["head"]["name"] == "Dr N. Achebe"
        assert signed["head"]["title"] == "Head Teacher"
        assert blocks["verification"]["content"]["number"].startswith("RC/")
    finally:
        session.rollback()
        session.close()


def test_a_certificate_is_the_same_engine_with_different_rows(school: World) -> None:
    """No branch anywhere knows that this one is a certificate."""
    session = school.session()
    try:
        template = documents.define_template(
            session, code=f"cert-{_uuid.uuid4().hex[:6]}", name="Certificate of Enrolment",
            purpose_label="Certificate of Enrolment", purpose="document",
            sections=[
                {"key": "identity", "options": {"show_reference": True}},
                {
                    "key": "narrative",
                    "options": {
                        "text": (
                            "This is to certify that {student_name} is enrolled at "
                            "{institution} as at {date}."
                        )
                    },
                },
                {"key": "signatures"},
                {"key": "verification"},
            ],
            numbering={"format": "{prefix}-{sequence:03d}", "prefix": "CERT",
                       "scope": "institution"},
        )
        documents.publish_template(session, template)
        student = people.student(session, school.students["Bilal Haddad"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            issued_on=date(2027, 2, 1),
        )
        blocks = {b["key"]: b for b in issued.payload["sections"]}
        assert "course_results" not in blocks
        assert "Bilal Haddad is enrolled at" in blocks["narrative"]["content"]["text"]
        assert "2027-02-01" in blocks["narrative"]["content"]["text"]
        assert issued.number.startswith("CERT-")
    finally:
        session.rollback()
        session.close()


# --- a university: credits, GPA, programmes, a transcript ------------------


def _build_university(slug: str) -> World:
    fixture = _provision(slug)
    session = fixture.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")
        terminology.publish(
            session,
            terms={
                "course": {"singular": "module", "plural": "modules"},
                "academic_period": {"singular": "semester", "plural": "semesters"},
            },
        )
        credits = CreditSystem(
            code="ects", name="ECTS", unit_label="ECTS credit",
            unit_label_plural="ECTS credits", is_default=True,
        )
        faculty = AcademicUnit(code="sci", name="Faculty of Science",
                               kind_label="Faculty")
        session.add_all([credits, faculty])
        session.flush()
        qualification = Qualification(
            code="bsc", name="Bachelor of Science", short_name="BSc",
            category_label="Undergraduate", framework_level=6,
            awarding_body="The University", required_credits=180,
            credit_system_id=credits.id,
        )
        session.add(qualification)
        session.flush()
        programme = Programme(
            code="bsc-cs", name="BSc Computer Science", academic_unit_id=faculty.id,
            qualification_id=qualification.id, credit_system_id=credits.id,
            required_credits=180,
        )
        session.add(programme)
        session.flush()
        level = Level(code="l4", name="Level 4", sequence=0, programme_id=programme.id)
        session.add(level)
        session.flush()
        year = AcademicYear(name="2026/27", code="2026", starts_on=date(2026, 9, 1),
                            ends_on=date(2027, 8, 31), is_current=True)
        session.add(year)
        session.flush()
        first = AcademicPeriod(
            academic_year_id=year.id, name="Semester 1", kind_label="Semester",
            sequence=1, starts_on=date(2026, 9, 21), ends_on=date(2027, 1, 29),
            is_current=True,
        )
        second = AcademicPeriod(
            academic_year_id=year.id, name="Semester 2", kind_label="Semester",
            sequence=2, starts_on=date(2027, 2, 8), ends_on=date(2027, 6, 4),
        )
        session.add_all([first, second])
        session.flush()
        group = ClassGroup(code="cs-l4", name="Level 4 Cohort", level_id=level.id,
                           academic_year_id=year.id, kind_label="Seminar group")
        session.add(group)
        session.flush()

        scale = GradingScale(code="gpa", name="Grade Points", kind=ScaleKind.gpa,
                             is_default=True)
        session.add(scale)
        session.flush()
        for index, (label, low, high, points, is_pass) in enumerate(
            (
                ("A", 70, 100, 4.0, True),
                ("B", 60, 69.99, 3.0, True),
                ("C", 50, 59.99, 2.0, True),
                ("F", 0, 49.99, 0.0, False),
            )
        ):
            session.add(GradingBand(scale_id=scale.id, label=label, min_value=low,
                                    max_value=high, points=points, is_pass=is_pass,
                                    sequence=index))
        algorithms = Course(code="cs101", name="Algorithms", credits=20,
                            credit_system_id=credits.id, grading_scale_id=scale.id,
                            programme_id=programme.id)
        databases = Course(code="cs102", name="Databases", credits=10,
                           credit_system_id=credits.id, grading_scale_id=scale.id,
                           programme_id=programme.id)
        session.add_all([algorithms, databases])
        session.flush()

        person = people.record_person(session, full_name="Nadia Rahman")
        student = people.register_student(session, person, reference="U-9001")
        placement = people.admit(
            session, student, on=date(2026, 9, 21),
            placement=Placement(academic_year_id=year.id, programme_id=programme.id,
                                level_id=level.id, class_group_id=group.id),
        )
        people.enrol(session, placement, on=date(2026, 9, 21))
        session.commit()

        return World(
            fixture, year_id=year.id, first_id=first.id, second_id=second.id,
            programme_id=programme.id, qualification_id=qualification.id,
            level_id=level.id, class_id=group.id, scale_id=scale.id,
            algorithms_id=algorithms.id, databases_id=databases.id,
            students={"Nadia Rahman": student.id},
        )
    finally:
        session.close()


TRANSCRIPT_SECTIONS = [
    {"key": "identity"},
    {"key": "enrolment_history"},
    {
        "key": "period_results",
        "options": {
            "columns": ("course_code", "course", "credits", "band", "points"),
            "aggregate": "weighted",
        },
    },
    {"key": "credit_summary"},
    {"key": "grade_points"},
    {"key": "qualifications"},
    {"key": "grading_key"},
    {"key": "verification"},
]


@pytest.fixture(scope="module")
def university() -> World:
    world = _build_university("documents-university")
    _publish_marks(
        world, course_id=world.algorithms_id, period_id=world.first_id,
        marks={"Nadia Rahman": 74}, code="alg", kind_label="Examination",
    )
    _publish_marks(
        world, course_id=world.databases_id, period_id=world.first_id,
        marks={"Nadia Rahman": 62}, code="db", kind_label="Examination",
    )
    return world


def _transcript_template(session, **overrides):
    draft = documents.define_template(
        session,
        code=overrides.pop("code", f"transcript-{_uuid.uuid4().hex[:6]}"),
        name="Academic Transcript",
        purpose_label="Academic Transcript",
        purpose="transcript",
        sections=overrides.pop("sections", TRANSCRIPT_SECTIONS),
        numbering=overrides.pop(
            "numbering",
            {"format": "{prefix}/{sequence:05d}", "prefix": "TR", "scope": "institution"},
        ),
        **overrides,
    )
    return documents.publish_template(session, draft)


def test_the_same_engine_produces_a_university_transcript(university: World) -> None:
    """Credits, grade points, a qualification framework — none of it new code."""
    session = university.session()
    try:
        template = _transcript_template(session)
        student = people.student(session, university.students["Nadia Rahman"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        blocks = {b["key"]: b for b in issued.payload["sections"]}

        groups = blocks["period_results"]["content"]["groups"]
        assert [g["period"] for g in groups] == ["Semester 1"]
        rows = {r["course_code"]: r for r in groups[0]["rows"]}
        assert rows["cs101"]["credits"] == 20
        assert rows["cs101"]["band"] == "A"
        assert rows["cs102"]["band"] == "B"

        credit = blocks["credit_summary"]["content"]
        assert credit["unit_label_plural"] == "ECTS credits"
        assert credit["attempted"] == 30
        assert credit["earned"] == 30

        # 4.0 over 20 credits and 3.0 over 10 → 3.67, weighted by credit.
        assert blocks["grade_points"]["content"]["average"] == 3.67
        assert issued.number.startswith("TR/")
    finally:
        session.rollback()
        session.close()


def test_a_transcript_uses_the_institutions_own_word_for_a_course(
    university: World,
) -> None:
    """The heading says Module because this institution says module."""
    session = university.session()
    try:
        template = _transcript_template(session)
        student = people.student(session, university.students["Nadia Rahman"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        page = documents.render(session, issued)
        assert ">Module<" in page
        assert ">Course<" not in page
    finally:
        session.rollback()
        session.close()


# --- historical integrity: the point of the whole module --------------------


def test_moving_a_grade_boundary_does_not_change_an_issued_report_card(
    school: World,
) -> None:
    """The 2026 copy and the 2031 reprint have to agree."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"hist-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        before = documents.render(session, issued)

        scale = session.get(GradingScale, school.scale_id)
        top = next(b for b in scale.bands if b.label == "A")
        top.min_value = 90  # 82 would no longer be an A
        session.flush()

        after = documents.render(session, issued)
        rows = {
            r["course"]: r
            for block in issued.payload["sections"]
            if block["key"] == "course_results"
            for r in block["content"]["rows"]
        }
        assert rows["Chemistry"]["band"] == "A"
        assert before == after
    finally:
        session.rollback()
        session.close()


def test_revaluing_a_module_does_not_change_an_issued_transcript(
    university: World,
) -> None:
    """A department that moves 20 credits to 30 has not changed a graduate's total."""
    session = university.session()
    try:
        template = _transcript_template(session)
        student = people.student(session, university.students["Nadia Rahman"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        course = session.get(Course, university.algorithms_id)
        course.credits = 30
        session.flush()

        def attempted(document):
            return next(
                b["content"]["attempted"] for b in document.payload["sections"]
                if b["key"] == "credit_summary"
            )

        # The document issued before the change is frozen, which is the easy half.
        assert attempted(issued) == 30

        # The half that matters: a transcript issued *after* the revaluation
        # still reports what the student earned, because the credit value was
        # snapshotted onto the published result rather than read from the course.
        reissued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        assert attempted(reissued) == 30
        rows = session.execute(
            text("SELECT credits FROM published_results WHERE course_id = :c"),
            {"c": str(university.algorithms_id)},
        ).scalars().all()
        assert {float(c) for c in rows} == {20.0}
    finally:
        session.rollback()
        session.close()


def test_renaming_the_schools_vocabulary_does_not_change_an_issued_document(
    school: World,
) -> None:
    """A report card that said Form keeps saying Form."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"vocab-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        assert issued.payload["terminology"]["course"]["singular"] == "subject"

        terminology.publish(
            session, terms={"course": {"singular": "paper", "plural": "papers"}}
        )
        session.flush()

        reread = session.get(Document, issued.id)
        assert reread.payload["terminology"]["course"]["singular"] == "subject"
        assert ">Subject<" in documents.render(session, reread)
    finally:
        session.rollback()
        session.close()


def test_a_report_card_shows_the_class_the_student_was_in_then(school: World) -> None:
    """Not the one they are in today. This is why enrolment is history."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"place-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Bilal Haddad"])

        # The transfer happens *first*, so that both documents are issued while
        # the student sits in 10B. A card that read today's placement would say
        # 10B for the autumn term, and the test would not be able to tell.
        current = people.open_enrolments(session, student)[0]
        people.transfer(
            session, current, on=date(2027, 1, 6),
            to=Placement(academic_year_id=school.year_id,
                         level_id=school.level_id,
                         class_group_id=school.other_class_id),
        )
        session.flush()

        autumn_card = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        spring_card = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.spring_id],
        )

        def placement_of(document):
            return next(
                b["content"] for b in document.payload["sections"]
                if b["key"] == "placement"
            )

        assert placement_of(autumn_card)["class_group"] == "10A"
        assert placement_of(spring_card)["class_group"] == "10B"
    finally:
        session.rollback()
        session.close()


def test_reprinting_is_not_regenerating(school: World) -> None:
    """Byte-for-byte, from the payload, however much has moved on underneath."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"rp-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        first = documents.render(session, issued)
        stored = dict(issued.payload)

        # Move everything the document quotes.
        session.get(Course, school.chemistry_id).name = "Chemical Sciences"
        band = next(
            b for b in session.get(GradingScale, school.scale_id).bands if b.label == "A"
        )
        band.label = "A*"
        session.flush()

        reread = session.get(Document, issued.id)
        assert reread.payload == stored
        assert documents.render(session, reread) == first
    finally:
        session.rollback()
        session.close()


def test_amending_a_published_result_leaves_the_issued_document_alone(
    school: World,
) -> None:
    """And the engine can say that the document has been overtaken."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"am-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        assert documents.outdated(session, issued) == []

        entry = session.execute(
            scoped_select(
                PublishedResult, __import__(
                    "app.modules.assessment.scopes", fromlist=["x"]
                ).PUBLISHED_RESULTS,
                db=session, principal=None, permission="assessment.result.read",
            )
        ).scalars().first()
        # No principal: the scoped read is fail-closed, which is itself the point.
        assert entry is None

        entry = session.execute(
            text(
                "SELECT id FROM published_results "
                "WHERE student_relationship_id = :s AND course_id = :c"
            ),
            {"s": str(student.id), "c": str(school.chemistry_id)},
        ).scalars().one()
        result = session.get(PublishedResult, entry)
        assessment.amend(
            session, result, membership_id=school.fixture.membership_id,
            permissions=PUBLISHER, reason="Transcription error on the mark sheet.",
            score=88,
        )
        session.flush()

        reread = session.get(Document, issued.id)
        rows = {
            r["course"]: r
            for b in reread.payload["sections"] if b["key"] == "course_results"
            for r in b["content"]["rows"]
        }
        assert rows["Chemistry"]["score"] == 82
        assert documents.outdated(session, reread) == [
            "A result quoted here has been corrected 1 time since this was issued."
        ]
    finally:
        session.rollback()
        session.close()


def test_a_reissue_supersedes_and_both_survive(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"ri-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        first = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        second = documents.reissue(
            session, first, permissions=REGISTRAR,
            reason="A mark was corrected after the original was issued.",
            period_ids=[school.autumn_id],
        )
        session.flush()

        assert first.status is DocumentStatus.superseded
        assert second.supersedes_id == first.id
        assert second.version == 2
        assert second.number != first.number
        assert session.get(Document, first.id) is not None
    finally:
        session.rollback()
        session.close()


def test_reissuing_without_a_reason_is_refused(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"rr-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        with pytest.raises(documents.DocumentError):
            documents.reissue(session, issued, permissions=REGISTRAR, reason="   ")
    finally:
        session.rollback()
        session.close()


# --- the branding line: current presentation, not historical fact -----------


def test_a_rebrand_changes_the_letterhead_and_not_one_grade(school: World) -> None:
    session = school.session()
    try:
        branding_module.publish(
            session, display_name="Old Name School", address="1 Old Road",
            primary_colour="#111111",
        )
        template = _report_card_template(session, code=f"br-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        before = documents.render(session, issued)
        assert "Old Name School" in before

        branding_module.publish(
            session, display_name="New Name Academy", address="2 New Avenue"
        )
        session.flush()

        after = documents.render(session, issued)
        assert "New Name Academy" in after
        assert "2 New Avenue" in after
        # Every grade is identical: only the letterhead moved.
        assert issued.payload == session.get(Document, issued.id).payload
        assert after.count(">A<") == before.count(">A<")
    finally:
        session.rollback()
        session.close()


def test_a_template_may_freeze_the_identity_that_issued_it(school: World) -> None:
    """A certificate awarded by a body that has since been renamed."""
    session = school.session()
    try:
        branding_module.publish(session, display_name="The Awarding School")
        template = documents.define_template(
            session, code=f"frz-{_uuid.uuid4().hex[:6]}", name="Certificate",
            purpose_label="Certificate", purpose="document",
            sections=[{"key": "identity"}, {"key": "verification"}],
            freeze_branding=True,
        )
        documents.publish_template(session, template)
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        assert issued.payload["branding"]["display_name"] == "The Awarding School"

        branding_module.publish(session, display_name="Something Else Entirely")
        session.flush()

        page = documents.render(session, issued)
        assert "The Awarding School" in page
        assert "Something Else Entirely" not in page
    finally:
        session.rollback()
        session.close()


# --- numbering --------------------------------------------------------------


def test_numbers_are_sequential_and_never_repeat(school: World) -> None:
    session = school.session()
    try:
        # Its own prefix, and therefore its own series: a suite that shared one
        # counter across tests would be asserting the order it happened to run in.
        prefix = f"N{_uuid.uuid4().hex[:5].upper()}"
        template = _report_card_template(
            session, code=f"num-{_uuid.uuid4().hex[:6]}",
            numbering={"format": "{prefix}/{year}/{sequence:04d}", "prefix": prefix,
                       "scope": "year"},
        )
        student = people.student(session, school.students["Ada Nwosu"])
        numbers = [
            documents.issue(
                session, template=template, student=student, permissions=REGISTRAR,
                period_ids=[school.autumn_id], issued_on=date(2027, 1, 20),
            ).number
            for _ in range(3)
        ]
        assert numbers == [
            f"{prefix}/2027/0001", f"{prefix}/2027/0002", f"{prefix}/2027/0003"
        ]
        assert len(set(numbers)) == 3
    finally:
        session.rollback()
        session.close()


def test_a_year_scoped_sequence_restarts_when_the_year_does(school: World) -> None:
    session = school.session()
    try:
        prefix = f"Y{_uuid.uuid4().hex[:5].upper()}"
        template = _report_card_template(
            session, code=f"yr-{_uuid.uuid4().hex[:6]}",
            numbering={"format": "{prefix}/{year}/{sequence:04d}", "prefix": prefix,
                       "scope": "year"},
        )
        student = people.student(session, school.students["Ada Nwosu"])
        first = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id], issued_on=date(2027, 6, 1),
        )
        later = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id], issued_on=date(2028, 6, 1),
        )
        assert first.number == f"{prefix}/2027/0001"
        assert later.number == f"{prefix}/2028/0001"
    finally:
        session.rollback()
        session.close()


def test_a_preview_allocates_no_number_and_leaves_no_record(school: World) -> None:
    """Somebody designing a report card will look at it forty times."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"pv-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        before = session.execute(text("SELECT count(*) FROM documents")).scalar_one()
        for _ in range(5):
            composition = documents.preview(
                session, template=template, student=student,
                period_ids=[school.autumn_id],
            )
        after = session.execute(text("SELECT count(*) FROM documents")).scalar_one()

        assert before == after
        verification = next(
            b["content"] for b in composition.blocks if b["key"] == "verification"
        )
        assert verification["number"] == ""
    finally:
        session.rollback()
        session.close()


# --- verification -----------------------------------------------------------


def test_verification_confirms_a_document_without_disclosing_its_contents(
    school: World,
) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"vf-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        session.flush()

        checked = documents.verify(session, issued.verification_code)
        assert checked is not None
        assert checked.number == issued.number
        assert checked.subject_name == "Ada Nwosu"
        assert checked.is_current

        # Nothing about what it says. The disclosed surface is pinned rather
        # than sampled: a substring check over the repr passes by accident, and
        # a new field added to `Verification` in six months would slip past it.
        assert set(documents.Verification.__dataclass_fields__) == {
            "number", "title", "subject_name", "issued_on", "status",
            "checksum", "superseded_by", "content_verified", "integrity_unknown",
        }
        # Deliberately absent: the registrar's reason for withdrawing a
        # document. A verification code must not disclose why somebody's
        # certificate was revoked.
        assert not hasattr(checked, "revocation_note")
        disclosed = " ".join(
            str(getattr(checked, name))
            for name in documents.Verification.__dataclass_fields__
            if name != "checksum"
        )
        for leak in ("Chemistry", "History", "Grade", "82"):
            assert leak not in disclosed
    finally:
        session.rollback()
        session.close()


def test_an_unknown_verification_code_gets_the_same_answer_as_a_wrong_one(
    school: World,
) -> None:
    session = school.session()
    try:
        assert documents.verify(session, "ZZZZZZZZZZZZZZZZ") is None
        assert documents.verify(session, "") is None
        assert documents.verify(session, "   ") is None
    finally:
        session.close()


def test_a_superseded_document_verifies_as_superseded_and_names_its_replacement(
    school: World,
) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"vs-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        first = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        second = documents.reissue(
            session, first, permissions=REGISTRAR, reason="Corrected mark.",
            period_ids=[school.autumn_id],
        )
        session.flush()

        checked = documents.verify(session, first.verification_code)
        assert checked.status == "superseded"
        assert not checked.is_current
        assert checked.superseded_by == second.number
    finally:
        session.rollback()
        session.close()


def test_a_verification_code_does_not_cross_the_tenant_boundary(
    school: World, university: World
) -> None:
    session = school.session()
    other = university.session()
    try:
        template = _report_card_template(session, code=f"xt-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        session.commit()

        assert documents.verify(other, issued.verification_code) is None
    finally:
        session.rollback()
        session.close()
        other.close()


# --- contextual complexity: a nursery is offered none of this ---------------


def test_a_nursery_is_not_offered_sections_it_could_only_leave_empty() -> None:
    """No credit summary, because there are no credits here to summarise."""
    offered = {s.key for s in catalogue.available_to(frozenset({"levels", "classes"}))}
    assert "credit_summary" not in offered
    assert "qualifications" not in offered
    assert "grading_key" not in offered
    assert {"identity", "placement", "comments", "attendance"} <= offered


def test_a_university_is_offered_all_of_them() -> None:
    offered = {
        s.key
        for s in catalogue.available_to(
            frozenset({"credits", "qualifications", "grading", "programmes"})
        )
    }
    assert {"credit_summary", "qualifications", "grading_key"} <= offered
    assert offered == {s.key for s in catalogue.CATALOGUE}


def test_a_credit_section_on_a_school_template_composes_to_nothing(
    school: World,
) -> None:
    """Not an empty heading, and the designer was never offered it either.

    Two guarantees, in the two places they belong. `available_to` is where
    "complexity must be capability" applies — a school designing a report card
    is not shown a credit section at all. This test covers the other end: if one
    is configured anyway, it composes to nothing rather than to a blank heading.
    """
    assert "credit_summary" not in {
        s.key for s in catalogue.available_to(frozenset({"levels", "classes"}))
    }
    session = school.session()
    try:
        template = documents.define_template(
            session, code=f"nc-{_uuid.uuid4().hex[:6]}", name="Report",
            purpose_label="Report Card", purpose="report_card",
            sections=[
                {"key": "identity"},
                {"key": "credit_summary"},
                {"key": "verification"},
            ],
        )
        documents.publish_template(session, template)
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        keys = [b["key"] for b in issued.payload["sections"]]
        assert "credit_summary" not in keys
        assert "Credit" not in documents.render(session, issued)
    finally:
        session.rollback()
        session.close()


# --- authorization ----------------------------------------------------------


def test_issuing_without_the_permission_is_refused(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"na-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        with pytest.raises(documents.NotAuthorisedToIssue):
            documents.issue(
                session, template=template, student=student,
                permissions=perms.expand({"people.student.read"}),
                period_ids=[school.autumn_id],
            )
    finally:
        session.rollback()
        session.close()


def test_permission_to_print_report_cards_is_not_permission_to_print_transcripts(
    university: World,
) -> None:
    session = university.session()
    try:
        template = _transcript_template(session)
        student = people.student(session, university.students["Nadia Rahman"])
        with pytest.raises(documents.NotAuthorisedToIssue):
            documents.issue(
                session, template=template, student=student,
                permissions=REPORT_CARDS_ONLY,
            )
    finally:
        session.rollback()
        session.close()


def test_a_draft_template_cannot_issue(school: World) -> None:
    session = school.session()
    try:
        draft = documents.define_template(
            session, code=f"dr-{_uuid.uuid4().hex[:6]}", name="Draft",
            purpose_label="Report Card", purpose="report_card",
            sections=[{"key": "identity"}],
        )
        student = people.student(session, school.students["Ada Nwosu"])
        with pytest.raises(documents.DocumentError):
            documents.issue(
                session, template=draft, student=student, permissions=REGISTRAR
            )
    finally:
        session.rollback()
        session.close()


class _Principal:
    """The minimum a scope predicate needs, without an HTTP request behind it."""

    def __init__(self, *, user_id=None, membership_id=None, grants=()):
        from app.core.context import Grant

        self.user_id = user_id
        self.membership_id = membership_id
        self.grants = tuple(
            Grant(permissions=frozenset(p), scope_kind=k, scope_ids=frozenset(i))
            for p, k, i in grants
        )


def test_a_guardian_reaches_documents_about_their_own_child_and_no_others(
    school: World,
) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"gd-{_uuid.uuid4().hex[:6]}")
        for name in ("Ada Nwosu", "Bilal Haddad"):
            documents.issue(
                session, template=template,
                student=people.student(session, school.students[name]),
                permissions=REGISTRAR, period_ids=[school.autumn_id],
            )
        session.flush()

        ada = people.student(session, school.students["Ada Nwosu"])
        guardian_person = people.record_person(
            session, full_name="Chidi Nwosu", user_id=school.fixture.user_id
        )
        people.link_guardian(
            session, guardian=guardian_person,
            student=people.person(session, ada.person_id),
            relationship_label="father",
        )
        session.flush()

        principal = _Principal(
            user_id=school.fixture.user_id,
            grants=(({"reporting.report_card.read"}, ScopeKind.own_children, ()),),
        )
        visible = session.execute(
            scoped_select(
                Document, document_scopes.DOCUMENTS, db=session, principal=principal,
                permission="reporting.report_card.read",
            )
        ).scalars().all()
        assert visible
        assert {d.payload["subject"]["full_name"] for d in visible} == {"Ada Nwosu"}

        # The count leaks nothing either — the whole point of `scoped_count`.
        # Asserted against the rows rather than against a literal, because a
        # count that disagrees with the select is the bug worth catching: it is
        # how a total tells somebody how many records they may not see.
        assert scoped_count(
            Document, document_scopes.DOCUMENTS, db=session, principal=principal,
            permission="reporting.report_card.read",
        ) == len(visible)
        everything = session.execute(
            text("SELECT count(*) FROM documents")
        ).scalar_one()
        assert everything > len(visible)
    finally:
        session.rollback()
        session.close()


def test_a_principal_with_no_scope_for_this_permission_sees_nothing(
    school: World,
) -> None:
    """Fail closed: a scope on one permission cannot widen another."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"fc-{_uuid.uuid4().hex[:6]}")
        documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.flush()

        wrong_permission = _Principal(
            user_id=school.fixture.user_id,
            grants=(({"attendance.mark.read"}, ScopeKind.tenant, ()),),
        )
        assert scoped_count(
            Document, document_scopes.DOCUMENTS, db=session,
            principal=wrong_permission, permission="reporting.report_card.read",
        ) == 0
        assert scoped_count(
            Document, document_scopes.DOCUMENTS, db=session, principal=None,
            permission="reporting.report_card.read",
        ) == 0
    finally:
        session.rollback()
        session.close()


def test_documents_do_not_cross_the_tenant_boundary(
    school: World, university: World
) -> None:
    session = school.session()
    other = university.session()
    try:
        template = _report_card_template(session, code=f"tb-{_uuid.uuid4().hex[:6]}")
        documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.commit()

        seen = other.execute(text("SELECT count(*) FROM documents")).scalar_one()
        template_rows = other.execute(
            text("SELECT count(*) FROM document_templates WHERE code = :c"),
            {"c": template.code},
        ).scalar_one()
        assert seen == 0
        assert template_rows == 0
    finally:
        session.rollback()
        session.close()
        other.close()


# --- entitlement, which is not authorization --------------------------------


def test_an_institution_without_the_feature_cannot_issue_however_permitted(
    school: World,
) -> None:
    """Permission and entitlement are different questions (ADR-030)."""
    from app.core import errors

    session = school.session()
    try:
        template = _report_card_template(session, code=f"en-{_uuid.uuid4().hex[:6]}")
        billing.set_feature_enabled(
            session, "core.report_cards", enabled=False,
            note="Switched off while we redesign them.",
        )
        session.flush()
        student = people.student(session, school.students["Ada Nwosu"])
        with pytest.raises(errors.FeatureDisabled):
            documents.issue(
                session, template=template, student=student, permissions=REGISTRAR,
                period_ids=[school.autumn_id],
            )
    finally:
        session.rollback()
        session.close()


def test_issuing_a_document_is_metered(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"me-{_uuid.uuid4().hex[:6]}")
        before = billing.usage(session, "documents.rendered")
        documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.flush()
        assert billing.usage(session, "documents.rendered") == before + 1
    finally:
        session.rollback()
        session.close()


# --- withdrawal without erasure ---------------------------------------------


def test_a_voided_document_still_prints_and_says_so(school: World) -> None:
    """Refusing would leave whoever holds a copy unable to learn it was withdrawn."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"vd-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        documents.void(
            session, issued, reason="Issued against the wrong term.",
            permissions=REGISTRAR,
        )
        session.flush()

        assert issued.status is DocumentStatus.void
        assert "VOID" in documents.render(session, issued)
        assert documents.verify(session, issued.verification_code).status == "void"
    finally:
        session.rollback()
        session.close()


def test_voiding_without_a_reason_is_refused(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"vr-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        with pytest.raises(documents.DocumentError):
            documents.void(session, issued, reason="", permissions=REGISTRAR)
    finally:
        session.rollback()
        session.close()


def test_the_application_role_cannot_delete_an_issued_document(school: World) -> None:
    """Enforced by the grant, not by the code that happens to be calling."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"dl-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.commit()

        with pytest.raises(ProgrammingError):
            session.execute(
                text("DELETE FROM documents WHERE id = :i"), {"i": str(issued.id)}
            )
    finally:
        session.rollback()
        session.close()


# --- composition safety -----------------------------------------------------


def test_a_comment_the_template_has_no_place_for_is_refused(school: World) -> None:
    """Silently dropping it would lose a teacher's remark without telling them."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"cm-{_uuid.uuid4().hex[:6]}")
        student = people.student(session, school.students["Ada Nwosu"])
        with pytest.raises(documents.ComposeError):
            documents.issue(
                session, template=template, student=student, permissions=REGISTRAR,
                period_ids=[school.autumn_id],
                comments={"deputy_head": "A remark nobody configured a slot for."},
            )
    finally:
        session.rollback()
        session.close()


def test_narrative_substitution_cannot_reach_beyond_the_names_it_offers(
    school: World,
) -> None:
    """`str.format` on administrator text reaches attributes. This does not."""
    session = school.session()
    try:
        template = documents.define_template(
            session, code=f"ns-{_uuid.uuid4().hex[:6]}", name="Certificate",
            purpose_label="Certificate", purpose="document",
            sections=[
                {
                    "key": "narrative",
                    "options": {
                        "text": "{student_name} · {student_name.__class__} · {0} · {nope}"
                    },
                },
            ],
        )
        documents.publish_template(session, template)
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR
        )
        text_out = issued.payload["sections"][0]["content"]["text"]
        assert text_out.startswith("Ada Nwosu · ")
        assert "{student_name.__class__}" in text_out
        assert "{0}" in text_out
        assert "{nope}" in text_out
        assert "class '" not in text_out
    finally:
        session.rollback()
        session.close()


def test_a_students_name_containing_markup_is_escaped(school: World) -> None:
    session = school.session()
    try:
        person = people.record_person(session, full_name="<script>alert(1)</script>")
        student = people.register_student(session, person, reference="S-XSS")
        template = _report_card_template(session, code=f"xs-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        page = documents.render(session, issued)
        assert "<script>alert(1)</script>" not in page
        assert "&lt;script&gt;" in page
    finally:
        session.rollback()
        session.close()


def test_attendance_appears_only_for_the_period_the_document_covers(
    school: World,
) -> None:
    session = school.session()
    try:
        attendance.seed_codes(session)
        code = attendance.default_code(session)
        student = people.student(session, school.students["Ada Nwosu"])
        for day, period_id in (
            (date(2026, 10, 1), school.autumn_id),
            (date(2026, 10, 2), school.autumn_id),
            (date(2027, 2, 1), school.spring_id),
        ):
            register = attendance.open_session(
                session, class_group_id=school.class_id, occurred_on=day,
                academic_period_id=period_id,
                membership_id=school.fixture.membership_id,
            )
            attendance.mark_all(session, register, code_id=code.id,
                                membership_id=school.fixture.membership_id)
        session.flush()

        template = _report_card_template(session, code=f"at-{_uuid.uuid4().hex[:6]}")
        autumn = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id],
        )
        both = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
            period_ids=[school.autumn_id, school.spring_id],
        )

        def sessions_of(document):
            return next(
                b["content"]["sessions"] for b in document.payload["sections"]
                if b["key"] == "attendance"
            )

        assert sessions_of(autumn) == 2
        assert sessions_of(both) == 3
    finally:
        session.rollback()
        session.close()


# --- the renderer is a renderer ---------------------------------------------


def test_the_renderer_cannot_reach_the_database() -> None:
    """Structural. A renderer with a session is one refresh away from rewriting history."""
    import ast
    import pathlib

    source = pathlib.Path(
        __file__
    ).resolve().parents[1] / "modules" / "documents" / "render.py"
    tree = ast.parse(source.read_text())
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)

    forbidden = ("sqlalchemy", "app.db", "service")
    offenders = [
        name for name in imported if any(bad in name for bad in forbidden)
    ]
    assert not offenders, (
        "The document renderer imports "
        f"{offenders}. It renders a stored payload and must not be able to read "
        "anything else — a renderer that can query is a renderer that will "
        "eventually be asked to refresh the totals on a historical transcript."
    )


def test_the_same_payload_renders_as_text_as_well(school: World) -> None:
    """Two renderers over one payload, which proves the payload is presentation-free."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"tx-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        plain = render_text(issued.payload)
        assert "Ada Nwosu" in plain
        assert "Chemistry" in plain
        assert "<" not in plain
    finally:
        session.rollback()
        session.close()


def test_a_document_renders_without_a_branding_profile_at_all(school: World) -> None:
    """A school that has filled in nothing still gets a page that looks deliberate."""
    fresh = _build_school(f"documents-plain-{_uuid.uuid4().hex[:6]}")
    session = fresh.session()
    try:
        template = _report_card_template(session, code="plain")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, fresh.students["Ada Nwosu"]),
            permissions=REGISTRAR,
        )
        page = render_html(issued.payload, branding=branding_module.resolve(session))
        assert "<!doctype html>" in page
        assert "Ada Nwosu" in page
        assert "None" not in page
    finally:
        session.rollback()
        session.close()


def test_the_checksum_is_stable_across_renderings(school: World) -> None:
    session = school.session()
    try:
        template = _report_card_template(session, code=f"cs-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.flush()
        assert len(issued.checksum) == 64
        assert documents.verify(session, issued.verification_code).checksum == (
            issued.checksum
        )
    finally:
        session.rollback()
        session.close()


def test_a_document_that_reports_no_period_does_not_claim_one(school: World) -> None:
    """A certificate issued in March is not "the autumn term".

    Found by looking at the rendered page rather than at the payload: the
    certificate carried a subtitle naming a term it says nothing about, because
    the periods covered were derived from whatever the student had results for.
    They now follow what the document actually reports on.
    """
    session = school.session()
    try:
        certificate = documents.define_template(
            session, code=f"pd-{_uuid.uuid4().hex[:6]}", name="Certificate",
            purpose_label="Certificate of Enrolment", purpose="document",
            sections=[{"key": "identity"}, {"key": "placement"},
                      {"key": "verification"}],
        )
        documents.publish_template(session, certificate)
        student = people.student(session, school.students["Ada Nwosu"])
        issued = documents.issue(
            session, template=certificate, student=student, permissions=REGISTRAR,
            issued_on=date(2027, 3, 2),
        )
        assert issued.payload["context"]["periods"] == []
        assert issued.academic_period_id is None
        page = documents.render(session, issued)
        assert "Autumn Term" not in page

        # And a report card, which does report on a period, still names it.
        card_template = _report_card_template(session, code=f"pc-{_uuid.uuid4().hex[:6]}")
        card = documents.issue(
            session, template=card_template, student=student, permissions=REGISTRAR,
        )
        assert [p["name"] for p in card.payload["context"]["periods"]] == ["Autumn Term"]
        assert "Autumn Term" in documents.render(session, card)
    finally:
        session.rollback()
        session.close()


def test_a_credit_unit_is_printed_as_the_institution_writes_it(
    university: World,
) -> None:
    """Not title-cased. An institution counting in ECTS credits is not counting
    in Ects Credits, and a formatter that thinks it knows better is a formatter
    that mangles every acronym an institution has."""
    session = university.session()
    try:
        template = _transcript_template(session)
        student = people.student(session, university.students["Nadia Rahman"])
        issued = documents.issue(
            session, template=template, student=student, permissions=REGISTRAR,
        )
        page = documents.render(session, issued)
        assert "ECTS credits" in page
        assert "Ects" not in page
    finally:
        session.rollback()
        session.close()


# --- tamper-evidence, learned from a real credential architecture -----------


def test_an_issued_document_is_signed_not_merely_digested(school: World) -> None:
    """A plain digest is an integrity check against ourselves, not against a
    forger — anybody can recompute one. The signature is keyed (ADR-036)."""
    from app.modules.documents import integrity

    session = school.session()
    try:
        template = _report_card_template(session, code=f"sg-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.flush()
        assert issued.hash_key_version >= 1
        assert documents.verify(session, issued.verification_code).content_verified

        # The digest is not derivable without the key.
        plain = _uuid.uuid5(_uuid.NAMESPACE_OID, str(issued.payload)).hex
        assert issued.checksum != plain
        wrong = integrity.verify(
            {"number": issued.number}, issued.checksum,
            key_version=issued.hash_key_version,
        )
        assert wrong.reason == "mismatch"
    finally:
        session.rollback()
        session.close()


def test_editing_the_stored_record_is_detected(school: World) -> None:
    """The check the whole mechanism exists for."""
    session = school.session()
    try:
        template = _report_card_template(session, code=f"tm-{_uuid.uuid4().hex[:6]}")
        issued = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=REGISTRAR, period_ids=[school.autumn_id],
        )
        session.flush()
        assert documents.verify(session, issued.verification_code).content_verified

        payload = dict(issued.payload)
        payload["subject"] = {**payload["subject"], "full_name": "Someone Else"}
        issued.payload = payload
        session.flush()

        checked = documents.verify(session, issued.verification_code)
        assert not checked.content_verified
        assert not checked.integrity_unknown, (
            "a real mismatch must not be reported as a deployment gap"
        )
    finally:
        session.rollback()
        session.close()


def test_a_missing_key_is_a_deployment_gap_and_never_an_accusation(
    school: World,
) -> None:
    """Rotating a secret must not make the platform publicly call genuine
    graduates forgers. A key this environment lacks says nothing about the
    document, and the two outcomes are reported differently."""
    from app.modules.documents import integrity

    fields = {"number": "TR/00001", "name": "Nadia Rahman"}
    signed = integrity.compute(
        fields,
        env={"EDIRASX_DOCUMENT_HASH_SECRET": "era-one",
             "EDIRASX_DOCUMENT_HASH_KEY_VERSION": "1"},
    )
    rotated = {"EDIRASX_DOCUMENT_HASH_SECRET": "era-two",
               "EDIRASX_DOCUMENT_HASH_KEY_VERSION": "2"}

    lost = integrity.verify(fields, signed.digest, key_version=1, env=rotated)
    assert lost.reason == "key_unavailable"
    assert lost.is_deployment_gap
    assert not lost.accuses

    kept = integrity.verify(
        fields, signed.digest, key_version=1,
        env={**rotated, "EDIRASX_DOCUMENT_HASH_SECRET_V1": "era-one"},
    )
    assert kept.ok, "a document signed in an earlier era must keep verifying"


def test_a_retired_key_may_never_sign_again() -> None:
    from app.modules.documents import integrity

    original = dict(integrity.RETIRED_KEY_VERSIONS)
    integrity.RETIRED_KEY_VERSIONS[7] = "Leaked in the 2027 incident."
    try:
        with pytest.raises(integrity.IntegrityError, match="retired"):
            integrity.compute(
                {"a": 1},
                env={"EDIRASX_DOCUMENT_HASH_SECRET": "x",
                     "EDIRASX_DOCUMENT_HASH_KEY_VERSION": "7"},
            )
    finally:
        integrity.RETIRED_KEY_VERSIONS.clear()
        integrity.RETIRED_KEY_VERSIONS.update(original)


def test_issuing_without_a_signing_key_is_refused_rather_than_faked() -> None:
    """Better to refuse than to stamp a document with a predictable digest that
    looks like tamper-evidence and is none."""
    from app.modules.documents import integrity

    with pytest.raises(integrity.IntegrityError, match="tamper-evidence"):
        integrity.compute({"a": 1}, env={"EDIRASX_DOCUMENT_HASH_KEY_VERSION": "1"})


def test_a_document_number_checks_itself_before_any_lookup() -> None:
    """A forger can invent TR/00042. They cannot compute its suffix — and a
    verifier can refuse it without touching the database, which matters because
    an endpoint that queries on every string handed to it gets enumerated."""
    from app.modules.documents import integrity

    env = {"EDIRASX_DOCUMENT_HASH_SECRET": "series-key",
           "EDIRASX_DOCUMENT_HASH_KEY_VERSION": "1"}
    fields = {"name": "Nadia Rahman", "issued_on": "2027-07-14"}
    suffix = integrity.serial_suffix("TR/00001", fields, env=env)

    assert integrity.verify_serial(f"TR/00001-{suffix}", fields, env=env).ok
    # The suffix belongs to that one number and cannot be lifted onto another.
    assert integrity.verify_serial(f"TR/00042-{suffix}", fields, env=env).reason == "mismatch"
    assert integrity.verify_serial("TR/00042-9F3A1", fields, env=env).reason == "mismatch"
    assert integrity.verify_serial("TR/00001", fields, env=env).reason == "unsigned"


def test_a_verifiers_address_is_hashed_never_stored(school: World) -> None:
    from app.modules.documents import integrity

    assert integrity.hash_ip(None) is None
    digest = integrity.hash_ip("203.0.113.7")
    assert digest is not None
    assert "203.0.113" not in digest
    assert len(digest) == 64
