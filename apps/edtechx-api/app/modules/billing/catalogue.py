"""Features, limits and meters — declared once, validated at boot.

The same discipline as the permission catalogue, for the same reason: a plan
referencing a feature nobody implemented should fail the boot, not fail a
request at 08:15 on results day.

**Three vocabularies, deliberately separate**, because they answer three
different questions and collapsing them is how a billing system starts refusing
things nobody meant it to refuse:

  A **feature** is a capability that either exists for this institution or does
  not. "Does the AI Design Studio appear at all?"

  A **limit** is a ceiling on a countable thing that persists — students on the
  roll, staff accounts, storage. Exceeding it is a state, not an event.

  A **meter** is a rate of consumption over a billing period — AI tokens,
  documents rendered, messages sent. Exceeding it is an event with a moment.

A limit and a meter look alike and behave differently: a school that has 400
students under a 300 limit is *over* its limit and must not be locked out of its
own records, whereas a school that has spent its AI tokens for the month simply
cannot spend more until the period rolls. Modelling them as one thing forces the
same answer to both, and one of those answers is always wrong.

**None of this is authorization.** A feature answers what the institution has;
a permission answers what the person may do. See ADR-030.
"""

from __future__ import annotations

from typing import Final


class UnknownFeature(ValueError):
    """A plan or a call named a feature outside the catalogue."""


class UnknownLimit(ValueError):
    pass


class UnknownMeter(ValueError):
    pass


# --- features --------------------------------------------------------------

FEATURES: Final[frozenset[str]] = frozenset(
    {
        # Core school operations — present on every plan including free, because
        # a school that cannot take a register is not using the product.
        "core.attendance",
        "core.assessment",
        "core.report_cards",
        "core.announcements",
        "core.bulk_import",
        # Finance
        "finance.invoicing",
        "finance.online_payments",
        # Customization
        "customization.theme",
        "customization.terminology",
        "customization.custom_domain",
        "customization.white_label",
        "customization.design_studio",
        "customization.ai_design_studio",
        # Intelligence
        "intelligence.assistants",
        "intelligence.own_api_keys",
        # Learning
        "learning.courses",
        "learning.quizzes",
        # Scale and operations
        "operations.sso",
        "operations.advanced_analytics",
        "operations.api_access",
        "operations.timetabling",
    }
)


# --- limits (a ceiling on a standing quantity) -----------------------------

LIMITS: Final[frozenset[str]] = frozenset(
    {
        "students.active",
        "staff.active",
        "storage.megabytes",
        "campuses",
        "custom_roles",
    }
)


# --- meters (consumption within a billing period) --------------------------

METERS: Final[frozenset[str]] = frozenset(
    {
        "ai.tokens",
        "ai.requests",
        "documents.rendered",
        "messages.sent",
        "exports.generated",
    }
)


def validate_feature(key: str) -> str:
    if key not in FEATURES:
        raise UnknownFeature(f"{key!r} is not in the feature catalogue")
    return key


def validate_limit(key: str) -> str:
    if key not in LIMITS:
        raise UnknownLimit(f"{key!r} is not in the limit catalogue")
    return key


def validate_meter(key: str) -> str:
    if key not in METERS:
        raise UnknownMeter(f"{key!r} is not in the meter catalogue")
    return key


def validate_catalogue() -> None:
    """Called at boot. The three vocabularies must not overlap.

    A key that is both a feature and a limit would be answerable by two
    different questions with two different types, and every call site would
    have to know which one it meant.
    """
    overlaps = (FEATURES & LIMITS) | (FEATURES & METERS) | (LIMITS & METERS)
    if overlaps:
        raise ValueError(
            "A key appears in more than one catalogue, which makes it "
            f"ambiguous: {sorted(overlaps)}"
        )
