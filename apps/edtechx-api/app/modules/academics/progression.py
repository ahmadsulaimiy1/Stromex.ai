"""Evaluating whether a student moves up.

This is where a Western K–12 assumption would hide most comfortably: a function
called `should_promote` containing `if average >= 50 and attendance >= 0.75`.
It would work for one school, be quietly wrong for a credit-bearing
institution, and be impossible to dislodge later.

So the rule is data. The engine knows how to *combine* conditions and how to
read a small set of named metrics; it knows nothing about what a passing
student looks like. Four genuinely different institutions are four rows.

Every evaluation returns its reasoning. A promotion decision a registrar cannot
explain to a parent is not a feature, and "the system decided" is not an answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.modules.academics.models import ProgressionOutcome


class RuleError(ValueError):
    """A rule that cannot be evaluated. Raised at configuration time, not run time."""


# The metrics a rule may reference. Deliberately a closed set: an open
# expression language would be a scripting engine inside the product, with the
# security and support burden that implies. Adding a metric is a small, visible
# change here rather than a school writing code.
METRICS: frozenset[str] = frozenset(
    {
        "average_percentage",   # mean mark across assessed subjects
        "gpa",                  # mean grade points
        "credits_earned",       # sum of credits for passed subjects
        "courses_passed",       # count of courses whose band passes
        "courses_failed",
        "core_courses_passed",  # count restricted to courses the institution marks core
        "core_courses_failed",
        "attendance_rate",      # 0..1
        "position_in_class",    # 1 = top
        "class_size",
        "periods_completed",
        # Tertiary and research. Present for every institution and simply
        # unreferenced by rules that do not need them — computing a metric only
        # when some rule asks for it would make the engine's behaviour depend
        # on the rule, which is how special cases begin.
        "cumulative_gpa",           # CGPA across the programme so far
        "credits_attempted",
        "credits_required_met",     # 1 when the programme's credit bar is cleared
        "milestones_completed",
        "milestones_required",
        "supervisor_approved",      # 1 or 0
        "board_approved",           # 1 or 0
        "placement_completed",      # 1 or 0
        "competencies_met",         # competency-based institutions
        "competencies_required",
    }
)

OPERATORS = {
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


@dataclass(frozen=True, slots=True)
class Check:
    """One evaluated condition, with enough detail to explain it."""

    metric: str
    operator: str
    expected: float
    actual: float | None
    passed: bool

    def describe(self, term_for: dict[str, str] | None = None) -> str:
        label = (term_for or {}).get(self.metric, self.metric.replace("_", " "))
        actual = "not recorded" if self.actual is None else f"{self.actual:g}"
        return f"{label} {self.operator} {self.expected:g} — {actual}"


@dataclass(frozen=True, slots=True)
class Evaluation:
    outcome: ProgressionOutcome
    passed: bool
    checks: tuple[Check, ...] = field(default_factory=tuple)
    rule_code: str = ""

    @property
    def failed_checks(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.passed)

    def explain(self, term_for: dict[str, str] | None = None) -> list[str]:
        return [c.describe(term_for) for c in self.checks]


def validate(conditions: dict[str, Any]) -> None:
    """Reject a malformed rule when it is saved, not when a child is promoted.

    A rule that fails at evaluation time fails during end-of-year processing,
    for one student, in front of a registrar. Validating on write moves that
    failure to the person who can fix it.
    """
    if not isinstance(conditions, dict) or not conditions:
        raise RuleError("A progression rule needs at least one condition.")

    key = next(iter(conditions))
    if key in ("all", "any"):
        clauses = conditions[key]
        if not isinstance(clauses, list) or not clauses:
            raise RuleError(f"{key!r} needs a non-empty list of conditions.")
        for clause in clauses:
            validate(clause)
        return
    if key == "not":
        validate(conditions["not"])
        return

    metric = conditions.get("metric")
    operator = conditions.get("op")
    value = conditions.get("value")
    if metric not in METRICS:
        raise RuleError(
            f"Unknown metric {metric!r}. Available: {', '.join(sorted(METRICS))}"
        )
    if operator not in OPERATORS:
        raise RuleError(f"Unknown operator {operator!r}.")
    if not isinstance(value, (int, float, Decimal)):
        raise RuleError(f"Condition value must be a number, got {value!r}.")


def _evaluate(
    conditions: dict[str, Any], metrics: dict[str, float | None], checks: list[Check]
) -> bool:
    key = next(iter(conditions))

    if key == "all":
        # Every clause is evaluated even once one has failed, so the explanation
        # lists all reasons rather than only the first. A parent asking "why"
        # deserves the whole answer.
        results = [_evaluate(clause, metrics, checks) for clause in conditions["all"]]
        return all(results)
    if key == "any":
        results = [_evaluate(clause, metrics, checks) for clause in conditions["any"]]
        return any(results)
    if key == "not":
        return not _evaluate(conditions["not"], metrics, checks)

    metric = conditions["metric"]
    operator = conditions["op"]
    expected = float(conditions["value"])
    actual = metrics.get(metric)

    if actual is None:
        # Missing data is not a pass. A student with no recorded attendance has
        # not met an attendance requirement; treating absence of evidence as
        # evidence would promote on incomplete records.
        checks.append(Check(metric, operator, expected, None, False))
        return False

    passed = OPERATORS[operator](float(actual), expected)
    checks.append(Check(metric, operator, expected, float(actual), passed))
    return passed


def evaluate(
    conditions: dict[str, Any],
    metrics: dict[str, float | None],
    *,
    on_pass: ProgressionOutcome = ProgressionOutcome.promote,
    on_fail: ProgressionOutcome = ProgressionOutcome.repeat,
    rule_code: str = "",
) -> Evaluation:
    """Evaluate one rule against one student's metrics."""
    validate(conditions)
    checks: list[Check] = []
    passed = _evaluate(conditions, metrics, checks)
    return Evaluation(
        outcome=on_pass if passed else on_fail,
        passed=passed,
        checks=tuple(checks),
        rule_code=rule_code,
    )


# --- metric computation ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class CourseResult:
    """One course's outcome for one student, already banded."""

    course_code: str
    is_core: bool
    credits: float | None
    score: float | None
    points: float | None
    passed: bool


def compute_metrics(
    results: list[CourseResult],
    *,
    attendance_rate: float | None = None,
    position_in_class: int | None = None,
    class_size: int | None = None,
    periods_completed: int | None = None,
    cumulative_gpa: float | None = None,
    credits_required: float | None = None,
    milestones_completed: int | None = None,
    milestones_required: int | None = None,
    supervisor_approved: bool | None = None,
    board_approved: bool | None = None,
    placement_completed: bool | None = None,
    competencies_met: int | None = None,
    competencies_required: int | None = None,
) -> dict[str, float | None]:
    """Derive the metric set from a student's results.

    Every metric is computed for every school; a rule simply ignores the ones
    it does not reference. Computing only what a rule asks for would make the
    engine's behaviour depend on the rule, which is how special cases start.
    """
    scored = [r for r in results if r.score is not None]
    pointed = [r for r in results if r.points is not None]

    return {
        "average_percentage": (
            sum(r.score for r in scored) / len(scored) if scored else None
        ),
        "gpa": (sum(r.points for r in pointed) / len(pointed) if pointed else None),
        "credits_earned": sum(
            float(r.credits or 0) for r in results if r.passed and r.credits
        )
        or (0.0 if results else None),
        "courses_passed": float(sum(1 for r in results if r.passed)),
        "courses_failed": float(sum(1 for r in results if not r.passed)),
                # "Core" here is the model's `is_core` flag. A university that says
        # "compulsory" and a school that says "core" mean the same thing, and
        # the terminology layer renders whichever word the institution uses —
        # two metrics for one idea would be two things to keep in step.
        "core_courses_passed": float(sum(1 for r in results if r.is_core and r.passed)),
        "core_courses_failed": float(
            sum(1 for r in results if r.is_core and not r.passed)
        ),
        "credits_attempted": sum(float(r.credits or 0) for r in results) or (
            0.0 if results else None
        ),
        "credits_required_met": _flag(
            None
            if credits_required is None
            else sum(float(r.credits or 0) for r in results if r.passed) >= credits_required
        ),
        "attendance_rate": attendance_rate,
        "position_in_class": float(position_in_class) if position_in_class else None,
        "class_size": float(class_size) if class_size else None,
        "periods_completed": float(periods_completed) if periods_completed else None,
        "cumulative_gpa": cumulative_gpa,
        "milestones_completed": (
            float(milestones_completed) if milestones_completed is not None else None
        ),
        "milestones_required": (
            float(milestones_required) if milestones_required is not None else None
        ),
        "supervisor_approved": _flag(supervisor_approved),
        "board_approved": _flag(board_approved),
        "placement_completed": _flag(placement_completed),
        "competencies_met": (
            float(competencies_met) if competencies_met is not None else None
        ),
        "competencies_required": (
            float(competencies_required) if competencies_required is not None else None
        ),
    }


def _flag(value: bool | None) -> float | None:
    """Booleans become 1/0 so one comparison operator set serves every metric.

    `None` stays `None` rather than becoming 0: "not yet approved" and
    "explicitly refused" are different, and only the second should read as a
    definite zero to a rule.
    """
    return None if value is None else (1.0 if value else 0.0)
