"""The Four Schools acceptance test.

`EDTECHX_EDITORIAL_BIBLE.md` §8 promises that a school's structure is data, not
code. This is where that promise is either kept or exposed.

Four genuinely different institutions are configured through the same product:

  A. Primary / Secondary — three terms, A–F letter grades, pass on core
     subjects plus attendance
  B. Elementary / Middle / High — two semesters, 4.0 GPA, promotion on GPA
  C. Nursery / Primary / College — three terms, percentage with position in
     class, promotion on aggregate and rank
  D. Foundation / Undergraduate / Postgraduate — modular credits, continuous
     assessment, progression on credits accumulated

The test asserts three things that are easy to claim and hard to keep:

  * **No special-case code.** A static check proves no product module contains
    any of these schools' vocabulary or thresholds. If passing this test ever
    required an `if school_type == ...`, that check fails.
  * **The configuration layer does the work.** Each school's structure,
    grading, vocabulary, and progression come from rows, and the same functions
    evaluate all four.
  * **Tenant isolation survives it.** Four schools configured at once must not
    see one another's structure.
"""

from __future__ import annotations

import ast
import itertools
import pathlib
from dataclasses import dataclass
from datetime import date

import pytest
from sqlalchemy import select

from app.modules.academics.models import (
    AcademicStage,
    AcademicYear,
    ClassGroup,
    GradingBand,
    GradingScale,
    Level,
    ProgressionOutcome,
    ProgressionRule,
    ScaleKind,
    Subject,
    Term,
)
from app.modules.academics.progression import (
    RuleError,
    SubjectResult,
    compute_metrics,
    evaluate,
    validate,
)
from app.modules.customization import terminology
from app.tests.conftest import TenantFixture, requires_db, session_for

pytestmark = requires_db


# --- the four schools, as configuration ----------------------------------


@dataclass(frozen=True)
class SchoolShape:
    key: str
    stages: list[tuple[str, str, str | None]]          # (code, name, parent code)
    levels: list[tuple[str, str, str]]                  # (code, name, stage code)
    terms: list[str]
    scale: tuple[str, ScaleKind, list[tuple[str, float, float, float | None, bool]]]
    subjects: list[tuple[str, str, bool, float | None]]  # code, name, core, credits
    vocabulary: dict[str, dict[str, str]]
    rule: dict
    rule_outcomes: tuple[ProgressionOutcome, ProgressionOutcome]


BRITISH = SchoolShape(
    key="british",
    stages=[("primary", "Primary", None), ("secondary", "Secondary", None)],
    levels=[
        ("y1", "Year 1", "primary"),
        ("y6", "Year 6", "primary"),
        ("y7", "Year 7", "secondary"),
        ("y11", "Year 11", "secondary"),
    ],
    terms=["Autumn Term", "Spring Term", "Summer Term"],
    scale=(
        "letter",
        ScaleKind.letter,
        [
            ("A", 70, 100, 5, True),
            ("B", 60, 69.99, 4, True),
            ("C", 50, 59.99, 3, True),
            ("D", 40, 49.99, 2, True),
            ("E", 30, 39.99, 1, False),
            ("F", 0, 29.99, 0, False),
        ],
    ),
    subjects=[
        ("eng", "English", True, None),
        ("mat", "Mathematics", True, None),
        ("sci", "Science", True, None),
        ("art", "Art", False, None),
    ],
    vocabulary={
        "class_group": {"singular": "form", "plural": "forms"},
        "student": {"singular": "pupil", "plural": "pupils"},
        "level": {"singular": "year group", "plural": "year groups"},
        "term": {"singular": "term", "plural": "terms"},
    },
    rule={
        "all": [
            {"metric": "core_subjects_failed", "op": "==", "value": 0},
            {"metric": "attendance_rate", "op": ">=", "value": 0.9},
        ]
    },
    rule_outcomes=(ProgressionOutcome.promote, ProgressionOutcome.repeat),
)

AMERICAN = SchoolShape(
    key="american",
    stages=[
        ("elementary", "Elementary School", None),
        ("middle", "Middle School", None),
        ("high", "High School", None),
    ],
    levels=[
        ("g1", "Grade 1", "elementary"),
        ("g6", "Grade 6", "middle"),
        ("g9", "Grade 9", "high"),
        ("g12", "Grade 12", "high"),
    ],
    terms=["Fall Semester", "Spring Semester"],
    scale=(
        "gpa",
        ScaleKind.gpa,
        [
            ("A", 93, 100, 4.0, True),
            ("B", 83, 92.99, 3.0, True),
            ("C", 73, 82.99, 2.0, True),
            ("D", 65, 72.99, 1.0, True),
            ("F", 0, 64.99, 0.0, False),
        ],
    ),
    subjects=[
        ("eng", "English Language Arts", True, None),
        ("alg", "Algebra", True, None),
        ("bio", "Biology", False, None),
    ],
    vocabulary={
        "class_group": {"singular": "homeroom", "plural": "homerooms"},
        "level": {"singular": "grade", "plural": "grades"},
        "term": {"singular": "semester", "plural": "semesters"},
        "guardian": {"singular": "parent", "plural": "parents"},
    },
    rule={"all": [{"metric": "gpa", "op": ">=", "value": 2.0}]},
    rule_outcomes=(ProgressionOutcome.promote, ProgressionOutcome.repeat),
)

NIGERIAN = SchoolShape(
    key="nigerian",
    stages=[
        ("nursery", "Nursery", None),
        ("primary", "Primary", None),
        ("college", "College", None),
    ],
    levels=[
        ("nur1", "Nursery 1", "nursery"),
        ("pry1", "Primary 1", "primary"),
        ("jss1", "JSS 1", "college"),
        ("sss3", "SSS 3", "college"),
    ],
    terms=["First Term", "Second Term", "Third Term"],
    scale=(
        "percentage",
        ScaleKind.percentage,
        [
            ("A", 70, 100, 70, True),
            ("B", 60, 69.99, 60, True),
            ("C", 50, 59.99, 50, True),
            ("D", 45, 49.99, 45, True),
            ("F", 0, 44.99, 0, False),
        ],
    ),
    subjects=[
        ("eng", "English Language", True, None),
        ("mat", "Mathematics", True, None),
        ("civ", "Civic Education", False, None),
    ],
    vocabulary={
        "class_group": {"singular": "arm", "plural": "arms"},
        "level": {"singular": "class", "plural": "classes"},
        "term": {"singular": "term", "plural": "terms"},
        "report_card": {"singular": "result sheet", "plural": "result sheets"},
    },
    # Aggregate *and* rank — a combination neither of the first two schools uses.
    rule={
        "all": [
            {"metric": "average_percentage", "op": ">=", "value": 50},
            {"metric": "position_in_class", "op": "<=", "value": 30},
        ]
    },
    rule_outcomes=(ProgressionOutcome.promote, ProgressionOutcome.repeat),
)

UNIVERSITY = SchoolShape(
    key="university",
    stages=[
        ("foundation", "Foundation", None),
        ("ug", "Undergraduate", None),
        ("pg", "Postgraduate", "ug"),  # nested: PG sits under the UG faculty
    ],
    levels=[
        ("f0", "Foundation Year", "foundation"),
        ("l4", "Level 4", "ug"),
        ("l6", "Level 6", "ug"),
        ("l7", "Level 7", "pg"),
    ],
    terms=["Academic Session"],  # one continuous session
    scale=(
        "points",
        ScaleKind.points,
        [
            ("Distinction", 70, 100, 70, True),
            ("Merit", 60, 69.99, 60, True),
            ("Pass", 40, 59.99, 40, True),
            ("Fail", 0, 39.99, 0, False),
        ],
    ),
    subjects=[
        ("mod1", "Research Methods", True, 20.0),
        ("mod2", "Data Structures", True, 20.0),
        ("mod3", "Elective Seminar", False, 20.0),
    ],
    vocabulary={
        "class_group": {"singular": "seminar group", "plural": "seminar groups"},
        "level": {"singular": "level", "plural": "levels"},
        "subject": {"singular": "module", "plural": "modules"},
        "term": {"singular": "session", "plural": "sessions"},
        "student": {"singular": "student", "plural": "students"},
    },
    rule={"all": [{"metric": "credits_earned", "op": ">=", "value": 40}]},
    rule_outcomes=(ProgressionOutcome.promote, ProgressionOutcome.repeat),
)

SHAPES = [BRITISH, AMERICAN, NIGERIAN, UNIVERSITY]


def configure(school: TenantFixture, shape: SchoolShape) -> None:
    """Configure a school entirely through ordinary rows.

    Deliberately one function for all four. If any school needed a branch here,
    the platform would be the thing that is flexible only in documentation.
    """
    session = school.session()
    try:
        stages: dict[str, AcademicStage] = {}
        for sequence, (code, name, parent_code) in enumerate(shape.stages):
            stage = AcademicStage(
                code=code,
                name=name,
                sequence=sequence,
                parent_id=stages[parent_code].id if parent_code else None,
            )
            session.add(stage)
            session.flush()
            stages[code] = stage

        levels: dict[str, Level] = {}
        for sequence, (code, name, stage_code) in enumerate(shape.levels):
            level = Level(
                code=code, name=name, sequence=sequence, stage_id=stages[stage_code].id
            )
            session.add(level)
            session.flush()
            levels[code] = level

        # Progression targets are explicit, not "the next sequence number".
        ordered = list(levels.values())
        for current, following in itertools.pairwise(ordered):
            current.next_level_id = following.id
        ordered[-1].is_terminal = True

        year = AcademicYear(
            name="2026", code="2026", starts_on=date(2026, 9, 1), ends_on=date(2027, 7, 31),
            is_current=True,
        )
        session.add(year)
        session.flush()

        for sequence, name in enumerate(shape.terms, start=1):
            session.add(
                Term(
                    academic_year_id=year.id,
                    name=name,
                    sequence=sequence,
                    starts_on=date(2026, 9, 1),
                    ends_on=date(2027, 7, 31),
                    is_current=sequence == 1,
                )
            )

        scale_code, kind, bands = shape.scale
        scale = GradingScale(
            code=scale_code, name=scale_code.title(), kind=kind, is_default=True
        )
        session.add(scale)
        session.flush()
        for sequence, (label, low, high, points, is_pass) in enumerate(bands):
            session.add(
                GradingBand(
                    scale_id=scale.id,
                    label=label,
                    min_value=low,
                    max_value=high,
                    points=points,
                    is_pass=is_pass,
                    sequence=sequence,
                )
            )

        for code, name, is_core, credits in shape.subjects:
            session.add(
                Subject(
                    code=code,
                    name=name,
                    is_core=is_core,
                    credits=credits,
                    grading_scale_id=scale.id,
                )
            )

        session.add(
            ClassGroup(
                code="a", name="A", level_id=ordered[0].id, academic_year_id=year.id
            )
        )

        validate(shape.rule)
        on_pass, on_fail = shape.rule_outcomes
        session.add(
            ProgressionRule(
                code="default",
                name="Default progression",
                conditions=shape.rule,
                on_pass=on_pass,
                on_fail=on_fail,
            )
        )

        terminology.publish(session, terms=shape.vocabulary)
        session.commit()
    finally:
        session.close()


@pytest.fixture
def four_schools(request: pytest.FixtureRequest) -> dict[str, TenantFixture]:
    """Provision and configure all four, in one test database, at once."""
    import uuid as _uuid

    from app.modules.authz.models import Role
    from app.modules.identity.models import Membership, User
    from app.modules.tenancy.models import Tenant
    from app.modules.tenancy.service import provision_school
    from app.tests.conftest import OWNER_PASSWORD
    from app.tests.conftest import TenantFixture as Fixture

    schools: dict[str, TenantFixture] = {}
    for shape in SHAPES:
        slug = f"{shape.key}-{_uuid.uuid4().hex[:8]}"
        result = provision_school(
            slug=slug,
            name=shape.key.title(),
            owner_email=f"owner@{slug}.test",
            owner_name="Owner",
            owner_password=OWNER_PASSWORD,
            base_domain="edtechx.localhost",
        )
        scoped = session_for(result.tenant_id)
        try:
            fixture = Fixture(
                scoped.get(Tenant, result.tenant_id),
                scoped.get(User, result.owner_user_id),
                scoped.get(Membership, result.owner_membership_id),
                scoped.execute(select(Role).where(Role.key == "owner")).scalar_one(),
            )
        finally:
            scoped.close()
        configure(fixture, shape)
        schools[shape.key] = fixture
    return schools


# --- each school got the shape it asked for -------------------------------


@pytest.mark.parametrize("shape", SHAPES, ids=lambda s: s.key)
def test_each_school_has_its_own_structure(
    four_schools: dict[str, TenantFixture], shape: SchoolShape
) -> None:
    session = four_schools[shape.key].session()
    try:
        stages = session.execute(select(AcademicStage)).scalars().all()
        levels = session.execute(select(Level)).scalars().all()
        terms = session.execute(select(Term)).scalars().all()

        assert {s.name for s in stages} == {name for _, name, _ in shape.stages}
        assert {level.name for level in levels} == {n for _, n, _ in shape.levels}
        assert [t.name for t in sorted(terms, key=lambda t: t.sequence)] == shape.terms
    finally:
        session.close()


def test_stage_depth_is_the_schools_choice(four_schools: dict[str, TenantFixture]) -> None:
    """Two flat tiers, three flat tiers, and a nested hierarchy — same schema."""
    depths = {}
    for shape in SHAPES:
        session = four_schools[shape.key].session()
        try:
            stages = session.execute(select(AcademicStage)).scalars().all()
            roots = [s for s in stages if s.is_root]
            nested = [s for s in stages if not s.is_root]
            depths[shape.key] = (len(roots), len(nested))
        finally:
            session.close()

    assert depths["british"] == (2, 0)
    assert depths["american"] == (3, 0)
    assert depths["nigerian"] == (3, 0)
    assert depths["university"] == (2, 1), "a nested stage was flattened"


def test_term_count_varies_from_one_to_three(
    four_schools: dict[str, TenantFixture]
) -> None:
    counts = {}
    for shape in SHAPES:
        session = four_schools[shape.key].session()
        try:
            counts[shape.key] = len(session.execute(select(Term)).scalars().all())
        finally:
            session.close()
    assert counts == {"british": 3, "american": 2, "nigerian": 3, "university": 1}


# --- grading -------------------------------------------------------------


def test_each_school_bands_a_mark_by_its_own_scale(
    four_schools: dict[str, TenantFixture]
) -> None:
    """The same mark means four different things, and the platform has no view."""
    expected = {"british": "A", "american": "B", "nigerian": "A", "university": "Distinction"}
    for shape in SHAPES:
        session = four_schools[shape.key].session()
        try:
            scale = session.execute(select(GradingScale)).scalars().one()
            band = scale.band_for(85)
            assert band is not None, f"{shape.key} could not band a mark of 85"
            assert band.label == expected[shape.key]
        finally:
            session.close()


def test_the_pass_mark_is_the_schools_decision(
    four_schools: dict[str, TenantFixture]
) -> None:
    """45 passes in one school and fails in another. Neither is a special case."""
    outcomes = {}
    for shape in SHAPES:
        session = four_schools[shape.key].session()
        try:
            scale = session.execute(select(GradingScale)).scalars().one()
            band = scale.band_for(45)
            outcomes[shape.key] = band.is_pass if band else None
        finally:
            session.close()
    assert outcomes["nigerian"] is True     # D at 45–49.99
    assert outcomes["british"] is True      # D at 40–49.99
    assert outcomes["american"] is False    # F below 65
    assert outcomes["university"] is True   # Pass at 40–59.99


# --- progression ---------------------------------------------------------


def _results(shape: SchoolShape, *, scores: list[float]) -> list[SubjectResult]:
    """Band a set of marks against this school's own scale."""
    _code, _kind, bands = shape.scale

    def band(score: float):
        for label, low, high, points, is_pass in bands:
            if low <= score <= high:
                return label, points, is_pass
        return "?", 0, False

    out = []
    for (code, _name, is_core, credits), score in zip(shape.subjects, scores, strict=False):
        _label, points, is_pass = band(score)
        out.append(
            SubjectResult(
                subject_code=code,
                is_core=is_core,
                credits=credits,
                score=score,
                points=points,
                passed=is_pass,
            )
        )
    return out


@pytest.mark.parametrize(
    ("shape", "scores", "attendance", "position", "expected"),
    [
        # British: core subjects passed and attendance ≥ 90%
        (BRITISH, [65, 55, 52, 30], 0.95, None, ProgressionOutcome.promote),
        (BRITISH, [65, 55, 52, 30], 0.60, None, ProgressionOutcome.repeat),
        (BRITISH, [65, 55, 25, 80], 0.99, None, ProgressionOutcome.repeat),
        # American: GPA ≥ 2.0
        (AMERICAN, [95, 88, 75], None, None, ProgressionOutcome.promote),
        (AMERICAN, [70, 66, 60], None, None, ProgressionOutcome.repeat),
        # Nigerian: aggregate ≥ 50 and position ≤ 30
        (NIGERIAN, [72, 61, 55], None, 12, ProgressionOutcome.promote),
        (NIGERIAN, [72, 61, 55], None, 44, ProgressionOutcome.repeat),
        (NIGERIAN, [40, 42, 38], None, 3, ProgressionOutcome.repeat),
        # University: 40 credits earned
        (UNIVERSITY, [75, 65, 55], None, None, ProgressionOutcome.promote),
        (UNIVERSITY, [75, 30, 20], None, None, ProgressionOutcome.repeat),
    ],
    ids=[
        "british-promotes",
        "british-held-by-attendance",
        "british-held-by-core-subject",
        "american-promotes-on-gpa",
        "american-held-by-gpa",
        "nigerian-promotes",
        "nigerian-held-by-position",
        "nigerian-held-by-aggregate",
        "university-promotes-on-credits",
        "university-held-by-credits",
    ],
)
def test_one_engine_decides_progression_for_every_school(
    shape: SchoolShape,
    scores: list[float],
    attendance: float | None,
    position: int | None,
    expected: ProgressionOutcome,
) -> None:
    """The heart of the claim.

    Four different definitions of "ready to move up", evaluated by one function
    with no knowledge of any of them.
    """
    metrics = compute_metrics(
        _results(shape, scores=scores),
        attendance_rate=attendance,
        position_in_class=position,
    )
    on_pass, on_fail = shape.rule_outcomes
    result = evaluate(shape.rule, metrics, on_pass=on_pass, on_fail=on_fail)
    assert result.outcome is expected, (
        f"{shape.key}: expected {expected.value}, got {result.outcome.value}. "
        f"Reasoning: {result.explain()}"
    )


def test_a_held_student_gets_a_full_explanation() -> None:
    """"The system decided" is not an answer a registrar can give a parent."""
    metrics = compute_metrics(
        _results(BRITISH, scores=[65, 55, 20, 30]), attendance_rate=0.5
    )
    result = evaluate(BRITISH.rule, metrics)
    assert not result.passed
    # Both reasons, not just the first one encountered.
    assert len(result.failed_checks) == 2
    reasons = " ".join(result.explain())
    assert "core subjects failed" in reasons and "attendance rate" in reasons


def test_missing_data_does_not_promote() -> None:
    """A student with no attendance recorded has not met an attendance rule."""
    metrics = compute_metrics(_results(BRITISH, scores=[65, 55, 52, 70]))
    result = evaluate(BRITISH.rule, metrics)
    assert result.outcome is ProgressionOutcome.repeat
    assert any(c.actual is None for c in result.failed_checks)


def test_a_malformed_rule_is_rejected_when_written() -> None:
    """Better to fail for the person configuring it than for a child in July."""
    for bad in (
        {},
        {"metric": "invented_metric", "op": ">=", "value": 1},
        {"metric": "gpa", "op": "≥", "value": 1},
        {"metric": "gpa", "op": ">=", "value": "two"},
        {"all": []},
    ):
        with pytest.raises(RuleError):
            validate(bad)


def test_rules_compose_with_any_and_not() -> None:
    """A school offering more than one route up needs no new engine."""
    rule = {
        "any": [
            {"metric": "credits_earned", "op": ">=", "value": 40},
            {"all": [
                {"metric": "average_percentage", "op": ">=", "value": 65},
                {"not": {"metric": "core_subjects_failed", "op": ">", "value": 0}},
            ]},
        ]
    }
    validate(rule)
    strong_marks = compute_metrics(_results(UNIVERSITY, scores=[70, 68, 66]))
    assert evaluate(rule, strong_marks).passed


# --- terminology ---------------------------------------------------------


def test_each_school_sees_its_own_words(four_schools: dict[str, TenantFixture]) -> None:
    expected = {
        "british": ("form", "pupil"),
        "american": ("homeroom", "student"),
        "nigerian": ("arm", "student"),
        "university": ("seminar group", "student"),
    }
    for key, (class_word, student_word) in expected.items():
        session = four_schools[key].session()
        try:
            words = terminology.resolve(session)
            assert words.word("class_group") == class_word
            assert words.word("student") == student_word
        finally:
            session.close()


def test_unset_terms_fall_back_without_restating_everything(
    four_schools: dict[str, TenantFixture]
) -> None:
    """A school renaming two words must not have to restate the other thirty."""
    session = four_schools["university"].session()
    try:
        words = terminology.resolve(session)
        assert words.word("subject") == "module"        # overridden
        assert words.word("attendance") == "attendance"  # inherited
        assert words.title("subject", plural=True) == "Modules"
    finally:
        session.close()


def test_terminology_publishing_keeps_history(
    four_schools: dict[str, TenantFixture]
) -> None:
    """A school that renames its vocabulary and regrets it must be able to undo."""
    from app.modules.customization.models import ConfigStatus, TerminologySet

    school = four_schools["british"]
    session = school.session()
    try:
        terminology.publish(
            session, terms={"student": {"singular": "scholar", "plural": "scholars"}}
        )
        session.commit()
        versions = (
            session.execute(select(TerminologySet).order_by(TerminologySet.version))
            .scalars()
            .all()
        )
        assert len(versions) == 2
        assert versions[0].status is ConfigStatus.archived
        assert versions[1].status is ConfigStatus.published
        assert terminology.resolve(session).word("student") == "scholar"
    finally:
        session.close()


# --- isolation, with four schools configured at once ---------------------


def test_four_configured_schools_cannot_see_each_other(
    four_schools: dict[str, TenantFixture]
) -> None:
    """The Phase 1 guarantee, under the conditions this phase creates."""
    for key, school in four_schools.items():
        session = school.session()
        try:
            level_names = {
                level.name for level in session.execute(select(Level)).scalars().all()
            }
            shape = next(s for s in SHAPES if s.key == key)
            assert level_names == {n for _, n, _ in shape.levels}

            others = [s for s in SHAPES if s.key != key]
            for other in others:
                leaked = level_names & {n for _, n, _ in other.levels}
                assert not leaked, f"{key} can see {other.key}'s levels: {leaked}"
        finally:
            session.close()


# --- and no special-case code --------------------------------------------

PRODUCT_ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_IN_PRODUCT_CODE = (
    "jss", "sss", "homeroom", "seminar group", "nursery", "foundation year",
    "key stage", "freshman", "sophomore", "gcse", "waec",
)


def _code_strings_and_names(path: pathlib.Path) -> list[tuple[str, str]]:
    """Every string literal and identifier that is *executed*, not documented.

    Docstrings and comments are excluded deliberately. A docstring that says
    "Nursery/Primary/College" is explaining the flexibility; a string literal
    that says it is assuming a school system. Only the second is a defect, and
    a check that cannot tell them apart would push the examples out of the
    documentation, making the code harder to understand in the name of a rule
    about the code.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                found.append((f"string on line {node.lineno}", node.value))
        elif isinstance(node, ast.Name):
            found.append((f"name on line {node.lineno}", node.id))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.append((f"definition on line {node.lineno}", node.name))
        elif isinstance(node, ast.Attribute):
            found.append((f"attribute on line {node.lineno}", node.attr))
    return found


def test_no_product_code_names_a_particular_school_system() -> None:
    """The static half of the claim.

    Every difference above must live in rows. If any of it had leaked into the
    product as a branch or a constant, the vocabulary would appear here.
    """
    offenders: list[str] = []
    for path in PRODUCT_ROOT.rglob("*.py"):
        if "tests" in path.parts or "alembic" in path.parts:
            continue
        for where, text_value in _code_strings_and_names(path):
            for word in FORBIDDEN_IN_PRODUCT_CODE:
                if word in text_value.lower():
                    offenders.append(f"{path.relative_to(PRODUCT_ROOT)}: {word!r} in {where}")
    assert not offenders, (
        "Product code names a specific school system, which means the "
        "flexibility is documentation rather than architecture:\n"
        + "\n".join(offenders)
    )


def test_no_product_code_hard_codes_a_pass_mark() -> None:
    """A threshold in code is a threshold one school cannot change."""
    suspicious: list[str] = []
    for path in (PRODUCT_ROOT / "modules").rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            source = ast.unparse(node).lower()
            if any(
                token in source
                for token in ("score", "mark", "average", "gpa", "percentage", "credits")
            ) and any(
                isinstance(c, ast.Constant) and isinstance(c.value, (int, float))
                and c.value not in (0, 1)
                for c in node.comparators
            ):
                suspicious.append(f"{path.relative_to(PRODUCT_ROOT)}: {source}")
    assert not suspicious, (
        "A grading or progression threshold appears in product code:\n"
        + "\n".join(suspicious)
    )


def test_the_engine_knows_no_school_specific_metric() -> None:
    """The metric vocabulary must be general, not a union of four schools' needs."""
    from app.modules.academics.progression import METRICS

    for metric in METRICS:
        assert not any(word in metric for word in FORBIDDEN_IN_PRODUCT_CODE)
