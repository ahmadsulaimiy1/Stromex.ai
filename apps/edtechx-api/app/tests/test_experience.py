"""The Universal Education Test, asked the other way round.

The backend's acceptance question was *can one engine represent radically
different institutions?* This suite asks the question that decides whether any
of that flexibility is worth having:

> Does each institution see only the complexity relevant to its actual
> operation?

Four institutions on one deployment. A nursery, a secondary school, a
university, and a doctoral institute. The assertions are mostly negative,
because the law being enforced is about what people are **not** shown:

  A nursery administrator must never see programmes, qualifications, credits,
  faculties or research milestones. Not as an empty menu item, not as a
  disabled row, not as a padlock. The concepts do not exist in their world.

  A university registrar must see faculties, departments, programmes, levels,
  credits and semesters — and must not be shown a nursery's concepts merely
  because the database supports them.

  A doctoral institute must additionally see supervision and milestones.

And within one institution, the same four questions produce different answers
for different people: a teacher, a parent and a bursar open the same deployment
into three different working lives.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.context import Grant, Principal
from app.modules.academics.models import AcademicPeriod, AcademicYear, ClassGroup, Level
from app.modules.academics.structure import (
    AcademicUnit,
    Cohort,
    CreditSystem,
    MilestoneDefinition,
    Programme,
    Qualification,
    SupervisionRole,
)
from app.modules.authz import permissions as perms
from app.modules.authz.system_roles import SYSTEM_ROLES_BY_KEY
from app.modules.billing import service as billing
from app.modules.billing.plans import PLANS
from app.modules.customization import terminology
from app.modules.experience import capabilities
from app.modules.experience import service as experience
from app.tests.conftest import TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision

pytestmark = requires_db

from datetime import date


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


def actor(role_key: str, tenant_id: _uuid.UUID) -> Principal:
    """Somebody holding exactly one system role, school-wide."""
    template = SYSTEM_ROLES_BY_KEY[role_key]
    granted = perms.expand(set(template.permissions))
    return Principal(
        user_id=_uuid.uuid4(),
        membership_id=_uuid.uuid4(),
        tenant_id=tenant_id,
        permissions=granted,
        grants=(Grant(frozenset(template.permissions), "tenant", ()),),
        session_id=_uuid.uuid4(),
        authenticated_at=datetime.now(UTC).timestamp(),
    )


def _year(session: Session) -> AcademicYear:
    year = AcademicYear(
        name="2026", code="2026", starts_on=date(2026, 9, 1),
        ends_on=date(2027, 7, 31), is_current=True,
    )
    session.add(year)
    session.flush()
    return year


# --- four institutions, configured as they actually are --------------------


def build_nursery(school: TenantFixture) -> None:
    """Classes, children, teachers, parents. Nothing else exists here."""
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.free")
        stage_free_level = Level(code="pre", name="Pre-school", sequence=0,
                                 stage_id=None, programme_id=None)
        # A level needs a stage or a programme, so a nursery keeps one stage and
        # never speaks of it again.
        from app.modules.academics.models import AcademicStage

        stage = AcademicStage(code="all", name="Nursery", sequence=0)
        session.add(stage)
        session.flush()
        stage_free_level.stage_id = stage.id
        session.add(stage_free_level)
        session.flush()

        year = _year(session)
        session.add(
            AcademicPeriod(academic_year_id=year.id, name="The Year", kind_label="Year",
                           sequence=1, starts_on=date(2026, 9, 1),
                           ends_on=date(2027, 7, 31), is_current=True)
        )
        session.add(
            ClassGroup(code="butterflies", name="Butterflies", kind_label="Room",
                       level_id=stage_free_level.id, academic_year_id=year.id)
        )
        terminology.publish(
            session,
            terms={
                "student": {"singular": "child", "plural": "children"},
                "class_group": {"singular": "room", "plural": "rooms"},
                "guardian": {"singular": "parent", "plural": "parents"},
            },
        )
        session.commit()
    finally:
        session.close()


def build_secondary(school: TenantFixture) -> None:
    """Stages, year groups, forms, subjects, terms, grading, promotion."""
    from app.modules.academics.models import AcademicStage, GradingScale, ProgressionRule, ScaleKind

    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.standard")
        lower = AcademicStage(code="lower", name="Lower School", sequence=0)
        upper = AcademicStage(code="upper", name="Upper School", sequence=1)
        session.add_all([lower, upper])
        session.flush()
        y7 = Level(code="y7", name="Year 7", sequence=0, stage_id=lower.id)
        y11 = Level(code="y11", name="Year 11", sequence=1, stage_id=upper.id)
        session.add_all([y7, y11])
        session.flush()
        year = _year(session)
        for index, name in enumerate(("Autumn", "Spring", "Summer"), start=1):
            session.add(
                AcademicPeriod(academic_year_id=year.id, name=f"{name} Term",
                               kind_label="Term", sequence=index,
                               starts_on=date(2026, 9, 1), ends_on=date(2027, 7, 31),
                               is_current=index == 1)
            )
        session.add(ClassGroup(code="7a", name="7A", kind_label="Form",
                               level_id=y7.id, academic_year_id=year.id))
        from app.modules.academics.models import Course

        session.add(Course(code="mat", name="Mathematics", is_core=True))
        scale = GradingScale(code="gcse", name="Grades", kind=ScaleKind.letter,
                             is_default=True)
        session.add(scale)
        session.add(ProgressionRule(
            code="default", name="Default",
            conditions={"all": [{"metric": "core_courses_failed", "op": "==", "value": 0}]},
        ))
        terminology.publish(
            session,
            terms={"class_group": {"singular": "form", "plural": "forms"},
                   "student": {"singular": "pupil", "plural": "pupils"}},
        )
        session.commit()
    finally:
        session.close()


def build_university(school: TenantFixture) -> None:
    """Faculties, departments, programmes, levels, courses, credits, semesters."""
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")
        faculty = AcademicUnit(code="fst", name="Faculty of Science", kind_label="Faculty")
        session.add(faculty)
        session.flush()
        department = AcademicUnit(code="cs", name="Computer Science",
                                  kind_label="Department", parent_id=faculty.id)
        session.add(department)
        session.flush()
        credits = CreditSystem(code="cr", name="Credits", unit_label="credit",
                               unit_label_plural="credits", is_default=True)
        session.add(credits)
        session.flush()
        qualification = Qualification(code="bsc", name="Bachelor of Science",
                                      category_label="Undergraduate", framework_level=30,
                                      credit_system_id=credits.id)
        session.add(qualification)
        session.flush()
        programme = Programme(code="bsc-cs", name="BSc Computer Science",
                              academic_unit_id=department.id,
                              qualification_id=qualification.id,
                              credit_system_id=credits.id)
        session.add(programme)
        session.flush()
        level = Level(code="l100", name="Level 100", sequence=0, programme_id=programme.id)
        session.add(level)
        session.flush()
        year = _year(session)
        session.add(Cohort(code="c2026", name="2026 Intake", programme_id=programme.id,
                           academic_year_id=year.id))
        for index, name in enumerate(("First", "Second"), start=1):
            session.add(
                AcademicPeriod(academic_year_id=year.id, name=f"{name} Semester",
                               kind_label="Semester", sequence=index,
                               starts_on=date(2026, 9, 1), ends_on=date(2027, 7, 31),
                               is_current=index == 1)
            )
        from app.modules.academics.models import Course

        session.add(Course(code="cs101", name="Programming", credits=20,
                           credit_system_id=credits.id, programme_id=programme.id))
        terminology.publish(
            session,
            terms={"course": {"singular": "module", "plural": "modules"},
                   "academic_unit": {"singular": "faculty", "plural": "faculties"},
                   "academic_period": {"singular": "semester", "plural": "semesters"}},
        )
        session.commit()
    finally:
        session.close()


def build_doctoral(school: TenantFixture) -> None:
    """A research institute: programmes, supervision, milestones. No classes."""
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")
        graduate = AcademicUnit(code="grad", name="Graduate School", kind_label="School")
        session.add(graduate)
        session.flush()
        qualification = Qualification(code="dr", name="Doctoral Degree",
                                      category_label="Doctoral", framework_level=50)
        session.add(qualification)
        session.flush()
        programme = Programme(code="dr-bio", name="Doctoral Programme",
                              academic_unit_id=graduate.id,
                              qualification_id=qualification.id, is_research=True)
        session.add(programme)
        session.flush()
        session.add(Level(code="probation", name="Probationary", sequence=0,
                          programme_id=programme.id))
        _year(session)
        session.add(SupervisionRole(code="principal", name="Principal Supervisor",
                                    is_primary=True, max_per_student=1))
        session.add(MilestoneDefinition(programme_id=programme.id, code="viva",
                                        name="Oral Examination", sequence=0))
        terminology.publish(
            session,
            terms={"student": {"singular": "researcher", "plural": "researchers"},
                   "course": {"singular": "research unit", "plural": "research units"}},
        )
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="module")
def institutions(platform: None) -> dict[str, TenantFixture]:
    built = {}
    for key, build in (
        ("nursery", build_nursery),
        ("secondary", build_secondary),
        ("university", build_university),
        ("doctoral", build_doctoral),
    ):
        school = _provision(f"ux-{key}")
        build(school)
        built[key] = school
    return built


def world(
    institutions: dict[str, TenantFixture], key: str, role: str = "admin"
) -> experience.Experience:
    school = institutions[key]
    session = school.session()
    try:
        return experience.resolve(
            session, actor(role, school.tenant_id), role_keys=[role],
            institution=school.tenant.name,
        )
    finally:
        session.close()


# --- the law, stated as four negative assertions ---------------------------


def test_a_nursery_administrator_never_meets_the_academic_engine(
    institutions: dict[str, TenantFixture]
) -> None:
    """The single most important assertion in the product.

    Not "these are hidden". Not "these are empty". Absent — because the concepts
    do not exist in this institution's world, and a "Programmes — 0" row teaches
    a person that their system is full of things they have done something wrong
    about.
    """
    seen = world(institutions, "nursery").keys()
    for concept in (
        "academics.programmes",
        "academics.qualifications",
        "academics.credits",
        "academics.units",
        "academics.cohorts",
        "research.supervision",
        "research.milestones",
        "operations.transcripts",
    ):
        assert concept not in seen, f"a nursery was shown {concept}"


def test_a_nursery_sees_what_a_nursery_has(
    institutions: dict[str, TenantFixture]
) -> None:
    seen = world(institutions, "nursery").keys()
    for concept in (
        "people.students", "people.guardians", "people.staff",
        "academics.classes", "academics.calendar",
        "operations.attendance", "communication.announcements",
    ):
        assert concept in seen, f"a nursery could not find {concept}"


def test_the_nursery_reads_in_its_own_words(
    institutions: dict[str, TenantFixture]
) -> None:
    """"Children" and "rooms", because that is what this institution says."""
    resolved = world(institutions, "nursery")
    labels = {c.key: c.label_plural for c in resolved.capabilities}
    assert labels["people.students"] == "Children"
    assert labels["academics.classes"] == "Rooms"
    assert labels["people.guardians"] == "Parents"


def test_a_university_sees_the_structure_it_actually_uses(
    institutions: dict[str, TenantFixture]
) -> None:
    resolved = world(institutions, "university", role="registrar")
    seen = resolved.keys()
    for concept in (
        "academics.units", "academics.programmes", "academics.qualifications",
        "academics.levels", "academics.courses", "academics.credits",
        "academics.cohorts", "academics.calendar",
    ):
        assert concept in seen, f"a university could not find {concept}"

    labels = {c.key: c.label_plural for c in resolved.capabilities}
    assert labels["academics.units"] == "Faculties"
    assert labels["academics.courses"] == "Modules"
    # And it is not shown a research institute's concepts merely because the
    # database supports them.
    assert "research.supervision" not in seen
    assert "research.milestones" not in seen


def test_a_secondary_school_sees_neither_a_nurserys_nor_a_universitys_world(
    institutions: dict[str, TenantFixture]
) -> None:
    seen = world(institutions, "secondary", role="registrar").keys()
    assert "academics.stages" in seen
    assert "academics.classes" in seen
    assert "academics.courses" in seen
    assert "academics.grading" in seen
    assert "academics.progression" in seen
    for absent in ("academics.programmes", "academics.credits", "academics.units",
                   "research.milestones"):
        assert absent not in seen, f"a secondary school was shown {absent}"


def test_a_doctoral_institute_additionally_sees_supervision_and_milestones(
    institutions: dict[str, TenantFixture]
) -> None:
    seen = world(institutions, "doctoral", role="registrar").keys()
    assert "research.supervision" in seen
    assert "research.milestones" in seen
    assert "academics.programmes" in seen
    # It runs no classes, so it is shown none.
    assert "academics.classes" not in seen
    assert "operations.timetable" not in seen


def test_the_four_institutions_produce_four_different_experiences(
    institutions: dict[str, TenantFixture]
) -> None:
    """The acceptance question, asked directly.

    Same deployment, same code path, same role. Four worlds, and no two of them
    the same.
    """
    worlds = {
        key: frozenset(world(institutions, key, role="registrar").keys())
        for key in institutions
    }
    for a, b in (("nursery", "secondary"), ("secondary", "university"),
                 ("university", "doctoral"), ("nursery", "university")):
        assert worlds[a] != worlds[b], f"{a} and {b} see the same product"
    assert len({frozenset(v) for v in worlds.values()}) == 4


def test_absence_records_why(institutions: dict[str, TenantFixture]) -> None:
    """"Not configured" and "not permitted" are different facts.

    A support conversation that cannot tell them apart is a support conversation
    that goes nowhere.
    """
    resolved = world(institutions, "nursery")
    assert resolved.absent["academics.programmes"] == experience.NOT_CONFIGURED
    assert resolved.absent["academics.credits"] == experience.NOT_CONFIGURED
    # The free plan does not include the studios, and this administrator cannot
    # buy them, so it is an absence rather than an advertisement.
    assert resolved.absent["configuration.design_studio"] in (
        experience.NOT_ENTITLED, experience.NOT_PERMITTED
    )


# --- the same institution, different people --------------------------------


def test_a_teacher_a_parent_and_a_bursar_open_three_different_products(
    institutions: dict[str, TenantFixture]
) -> None:
    teacher = world(institutions, "secondary", role="teacher")
    guardian = world(institutions, "secondary", role="guardian")
    bursar = world(institutions, "secondary", role="bursar")

    assert teacher.groups[0] in ("today", "operations")
    assert [c.key for c in teacher.primary][:1] == ["operations.attendance"]

    # A parent's world is small on purpose.
    assert len(guardian.capabilities) < len(teacher.capabilities)
    assert "academics.grading" not in guardian.keys()
    assert "configuration.roles" not in guardian.keys()

    assert bursar.groups[0] == "finance"
    assert "finance.invoices" in bursar.keys()
    # And a bursar is not handed the academic engine.
    assert "academics.progression" not in bursar.keys()


def test_a_person_never_sees_a_capability_they_lack_permission_for(
    institutions: dict[str, TenantFixture]
) -> None:
    """Absent, not disabled. Existence is sensitive (ADR-004)."""
    guardian = world(institutions, "secondary", role="guardian")
    assert "people.staff" not in guardian.keys()
    assert guardian.absent["people.staff"] == experience.NOT_PERMITTED


def test_an_unentitled_capability_is_an_offer_only_to_somebody_who_could_buy_it(
    institutions: dict[str, TenantFixture]
) -> None:
    """A padlock a teacher cannot open is an advertisement placed in their way."""
    school = institutions["nursery"]
    session = school.session()
    try:
        owner = actor("owner", school.tenant_id)
        teacher = actor("teacher", school.tenant_id)
        as_owner = experience.resolve(session, owner, role_keys=["owner"])
        as_teacher = experience.resolve(session, teacher, role_keys=["teacher"])
    finally:
        session.close()

    offered = {c.key for c in as_owner.capabilities if c.upgrade_from}
    assert offered, "nothing on the free plan was offered as an upgrade"
    for key in offered:
        assert key not in as_teacher.keys(), (
            f"a teacher was shown {key} as a locked upgrade"
        )


# --- zero states -----------------------------------------------------------


def test_a_present_capability_with_no_records_carries_what_to_do(
    institutions: dict[str, TenantFixture]
) -> None:
    """"Your school has no courses yet" plus the action, not "0 courses"."""
    resolved = world(institutions, "nursery")
    students = next(c for c in resolved.capabilities if c.key == "people.students")
    assert students.empty_action == "Add your first child"


def test_an_absent_capability_has_no_empty_state_because_it_has_no_state(
    institutions: dict[str, TenantFixture]
) -> None:
    resolved = world(institutions, "nursery")
    assert not any(c.key == "academics.programmes" for c in resolved.capabilities)
    assert "academics.programmes" in resolved.absent


def test_empty_groups_are_dropped_rather_than_rendered(
    institutions: dict[str, TenantFixture]
) -> None:
    resolved = world(institutions, "nursery", role="teacher")
    grouped = resolved.grouped()
    assert all(members for members in grouped.values())
    assert set(grouped) <= set(resolved.groups)


# --- declaration, for an institution that has not started yet --------------


def test_a_new_institution_can_declare_its_shape_before_it_has_any_rows(
    platform: None
) -> None:
    """A university on its first morning must not be shown a nursery's product.

    Nothing can be inferred from an empty database, so the institution says what
    it intends to use and the interface believes it immediately.
    """
    school = _provision("ux-declared")
    session = school.session()
    try:
        billing.subscribe(session, plan_key="plan.institution")
        session.commit()
        before = experience.resolve(session, actor("registrar", school.tenant_id),
                                    role_keys=["registrar"])
        assert "academics.programmes" not in before.keys()

        experience.declare_layers(
            session,
            layers=["academic_units", "programmes", "qualifications", "levels",
                    "credits", "periods", "years", "courses"],
            self_description="the University",
        )
        session.commit()

        after = experience.resolve(session, actor("registrar", school.tenant_id),
                                   role_keys=["registrar"])
        assert "academics.programmes" in after.keys()
        assert "academics.credits" in after.keys()
        assert after.self_description == "the University"
        # And it is still not shown what it did not declare.
        assert "research.milestones" not in after.keys()
    finally:
        session.close()


def test_an_institution_cannot_hide_a_layer_it_is_actively_using(
    institutions: dict[str, TenantFixture]
) -> None:
    """Data that exists stays reachable. Suppression tidies; it does not conceal."""
    school = institutions["university"]
    session = school.session()
    try:
        experience.suppress_layers(session, layers=["programmes", "cohorts"])
        session.commit()
        resolved = experience.resolve(session, actor("registrar", school.tenant_id),
                                      role_keys=["registrar"])
        assert "academics.programmes" in resolved.keys(), (
            "a university hid a layer full of its own records"
        )
    finally:
        session.rollback()
        session.close()


def test_a_declared_layer_that_is_not_a_layer_is_refused(
    institutions: dict[str, TenantFixture]
) -> None:
    session = institutions["nursery"].session()
    try:
        with pytest.raises(ValueError):
            experience.declare_layers(session, layers=["not_a_layer"])
    finally:
        session.rollback()
        session.close()


# --- the structural guarantee ----------------------------------------------


def test_no_institution_type_exists_anywhere(institutions: dict[str, TenantFixture]) -> None:
    """The enum ADR-024 forbids, arriving through the interface's back door.

    A `NURSERY | SECONDARY | UNIVERSITY` column would answer "what kind of place
    is this?" when the only question worth asking is "what does this place
    actually use?" — and it would be wrong for the first institution that is two
    of them at once, which is most of them.
    """
    import ast
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[1]
    forbidden = ("institution_type", "school_type", "institution_kind", "org_type")
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text_value = node.value.lower()
            elif isinstance(node, ast.Name):
                text_value = node.id.lower()
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                text_value = node.name.lower()
            else:
                continue
            for word in forbidden:
                if re.search(rf"(?<![a-z0-9]){word}(?![a-z0-9])", text_value):
                    offenders.append(f"{path.relative_to(root)}: {word}")
    assert not offenders, (
        "An institution type appears in product code. What an institution is "
        "must be derived from what it uses:\n" + "\n".join(offenders)
    )


def test_every_capability_names_a_real_permission_and_feature() -> None:
    """A typo here produces a capability nobody ever sees and nobody can explain."""
    from app.modules.billing import catalogue
    from app.modules.experience.capabilities import CAPABILITIES, GROUPS

    for capability in CAPABILITIES:
        if capability.permission:
            perms.validate(capability.permission)
        if capability.feature:
            catalogue.validate_feature(capability.feature)
        assert capability.group in GROUPS, capability.key
        for layer in capability.layers:
            from app.modules.academics.service import LAYER_TABLES

            assert layer in LAYER_TABLES, f"{capability.key}: unknown layer {layer}"


def test_every_capability_term_is_a_known_word() -> None:
    """A label resolved from a key nobody defined would render as an exception."""
    from app.modules.experience.capabilities import CAPABILITIES

    for capability in CAPABILITIES:
        if capability.term:
            assert capability.term in terminology.DEFAULT_TERMS, capability.key


# --- what a design review found ---------------------------------------------


def test_no_two_capabilities_can_carry_the_same_label() -> None:
    """A rail containing "Grades" twice is a rail nobody can use.

    Invisible to every test that inspects capability *keys*, which is what every
    test here did until four institutions were rendered and looked at. Five
    pairs collided: grading scales and results, class groups and the timetable,
    curriculum subjects and course content, levels and progression rules,
    qualifications and transcripts.
    """
    capabilities.validate_catalogue()


def test_every_institution_renders_a_navigation_with_no_repeated_item(
    institutions: dict[str, TenantFixture],
) -> None:
    """The check that would have caught it, applied to every world we have."""
    for key in ("nursery", "secondary", "university", "doctoral"):
        for role in ("admin", "teacher", "student", "guardian"):
            resolved = world(institutions, key, role)
            labels = [c.label_plural for c in resolved.capabilities]
            repeated = sorted({label for label in labels if labels.count(label) > 1})
            assert not repeated, (
                f"{key}/{role} would show these items twice: {repeated}"
            )


def test_an_institutions_own_vocabulary_cannot_produce_two_identical_items(
    institutions: dict[str, TenantFixture],
) -> None:
    """The catalogue cannot prevent this; only resolution can.

    A school that calls both its class groups and its cohorts "Sets" would get
    two rail items reading "Sets". The second is dropped, and the reason is
    recorded rather than swallowed.
    """
    school = institutions["university"]
    session = school.session()
    try:
        # Both concepts have to be present before they can collide.
        experience.declare_layers(session, layers=["classes", "cohorts"])
        terminology.publish(session, terms={
            "class_group": {"singular": "set", "plural": "sets"},
            "cohort": {"singular": "set", "plural": "sets"},
        })
        session.flush()
        resolved = experience.resolve(
            session, actor("admin", school.tenant_id), role_keys=["admin"]
        )
        labels = [c.label_plural for c in resolved.capabilities]
        assert len(labels) == len(set(labels))
        assert experience.NAME_COLLISION in resolved.absent.values()
    finally:
        session.rollback()
        session.close()


def test_a_nursery_is_not_offered_grades_assessments_or_report_cards(
    institutions: dict[str, TenantFixture],
) -> None:
    """An institution that grades nobody has no grading scale rows.

    These three were ungated, so every institution in the product was offered
    them — a nursery administrator's navigation carried Assessments, Grades and
    Report cards beside Children and Rooms. Found by rendering a nursery and
    looking at it.
    """
    nursery = world(institutions, "nursery")
    for key in ("operations.assessment", "operations.results",
                "operations.report_cards"):
        assert key not in nursery.keys()
        assert nursery.absent[key] == experience.NOT_CONFIGURED

    secondary = world(institutions, "secondary")
    assert {"operations.assessment", "operations.results",
            "operations.report_cards"} <= set(secondary.keys())
