"""What an import *is*: the fields it accepts and what makes a row valid.

A specification rather than a function per import kind, for the same reason the
academic model is rows rather than branches. "Import students" and "import
staff" differ in their fields, not in their machinery — the reading, mapping,
validation, duplicate detection, preview, transaction and reporting are
identical, and writing them twice guarantees they diverge.

Field validation returns *messages*, never exceptions, because a row that fails
must not stop the file. The person needs every problem in one report, not the
first one, and an import that surfaces errors one at a time takes a morning
instead of ten minutes.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

# Deliberately permissive. This is an institution's own record of a person, not
# a login credential, and refusing an unusual but real address is a worse
# failure than accepting an odd one.
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Formats a person might reasonably type, in the order they are tried. Ambiguity
# between the second and third is real and unresolvable from the value alone,
# which is why the chosen format is an import option rather than a guess.
DATE_FORMATS_DAY_FIRST = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y")
DATE_FORMATS_MONTH_FIRST = ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%b %d %Y", "%B %d %Y")


@dataclass(frozen=True, slots=True)
class Field:
    """One target field: what it is called, whether it is needed, how it is read."""

    key: str
    label: str
    required: bool = False
    # Header names an export is likely to use, matched case- and
    # punctuation-insensitively when a mapping is proposed.
    aliases: tuple[str, ...] = ()
    parse: Callable[[str, ImportOptions], tuple[object | None, list[str]]] | None = None
    max_length: int | None = None
    help_text: str = ""

    def read(self, raw: str, options: ImportOptions) -> tuple[object | None, list[str]]:
        value = raw.strip()
        if not value:
            if self.required:
                return None, [f"{self.label} is required."]
            return None, []
        if self.max_length and len(value) > self.max_length:
            return None, [
                f"{self.label} is longer than {self.max_length} characters."
            ]
        if self.parse is None:
            return value, []
        return self.parse(value, options)


@dataclass(frozen=True, slots=True)
class ImportOptions:
    """Choices the person makes before an import runs, not guesses we make for them."""

    # Whether 03/04/2020 is the third of April or the fourth of March. The file
    # cannot say, the two readings are both common, and picking one silently
    # produces records that are wrong by months for a subset of rows.
    day_first_dates: bool = True
    # What to do when a row matches a record already here.
    #
    # There is deliberately no "update" option yet. Merging two records is a
    # decision with consequences — whose date of birth wins, what happens to the
    # enrolment history of the record being absorbed — and offering it as a
    # checkbox before that workflow is designed would quietly overwrite correct
    # data with a spreadsheet's.
    on_duplicate: str = "skip"  # "skip" | "error"
    # A duplicate *inside the file* is always an error: the person meant one of
    # them, and choosing for them is not our decision to make.


def parse_date(value: str, options: ImportOptions) -> tuple[object | None, list[str]]:
    formats = (
        DATE_FORMATS_DAY_FIRST if options.day_first_dates else DATE_FORMATS_MONTH_FIRST
    )
    from datetime import datetime

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date(), []
        except ValueError:
            continue
    order = "day/month/year" if options.day_first_dates else "month/day/year"
    return None, [f"{value!r} is not a date this import recognises (expected {order})."]


def parse_past_date(value: str, options: ImportOptions) -> tuple[object | None, list[str]]:
    parsed, errors = parse_date(value, options)
    if errors or parsed is None:
        return parsed, errors
    assert isinstance(parsed, date)
    if parsed > date.today():
        return None, [f"{value!r} is in the future."]
    return parsed, []


def parse_email(value: str, _options: ImportOptions) -> tuple[object | None, list[str]]:
    if not EMAIL.match(value):
        return None, [f"{value!r} does not look like an email address."]
    return value.lower(), []


def parse_boolean(value: str, _options: ImportOptions) -> tuple[object | None, list[str]]:
    lowered = value.strip().lower()
    if lowered in {"y", "yes", "true", "1", "t"}:
        return True, []
    if lowered in {"n", "no", "false", "0", "f"}:
        return False, []
    return None, [f"{value!r} is not a yes/no value."]


@dataclass(frozen=True, slots=True)
class ImportSpec:
    """A kind of import: its fields, and the rule that makes two rows the same person."""

    kind: str
    title: str
    fields: tuple[Field, ...]
    # Field keys that identify a record. The first tuple whose fields are all
    # present is used; a row matching none is always treated as new.
    identity_keys: tuple[tuple[str, ...], ...] = ()
    description: str = ""

    def field_for(self, key: str) -> Field | None:
        return next((f for f in self.fields if f.key == key), None)

    @property
    def required_keys(self) -> tuple[str, ...]:
        return tuple(f.key for f in self.fields if f.required)

    def identity_of(self, values: dict[str, object]) -> tuple[str, tuple] | None:
        """The natural key of a row, or `None` when it carries no identity.

        Returns the key set's name alongside the values so a report can say
        *which* identity matched — "the same admission number" and "the same
        name and date of birth" are very different levels of confidence, and a
        person deciding whether to merge needs to know which one fired.
        """
        for keys in self.identity_keys:
            if all(values.get(key) not in (None, "") for key in keys):
                return "+".join(keys), tuple(str(values[key]).lower() for key in keys)
        return None


def _normalise_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


# Which configured term describes each field, where one does. This is how an
# institution's *own* vocabulary becomes recognisable in a spreadsheet heading
# without any word of any particular education system appearing here: a school
# that configured `class_group` as "arm" gets a column headed "Arm" recognised,
# and one that configured it as "homeroom" gets "Homeroom", because each told
# us what it calls the thing.
TERM_FOR_FIELD: dict[str, str] = {
    "full_name": "student",
    "class_group_code": "class_group",
    "level_code": "level",
    "programme_code": "programme",
    "cohort_code": "cohort",
    "guardian_name": "guardian",
    "kind_label": "student",
    "started_on": "enrolment",
}


def _vocabulary_aliases(field_key: str, vocabulary: object | None) -> tuple[str, ...]:
    """Headings an institution's own words would produce, for one field."""
    term_key = TERM_FOR_FIELD.get(field_key)
    if vocabulary is None or term_key is None:
        return ()
    try:
        singular = vocabulary.word(term_key)          # type: ignore[attr-defined]
        plural = vocabulary.word(term_key, plural=True)  # type: ignore[attr-defined]
    except (AttributeError, KeyError):
        return ()
    forms = {singular, plural}
    if field_key.endswith("_name") or field_key == "full_name":
        return tuple(f"{word} name" for word in forms) + tuple(
            f"name of {word}" for word in forms
        )
    if field_key.endswith("_code"):
        return tuple(forms) + tuple(f"{word} code" for word in forms)
    return tuple(forms)


def propose_mapping(
    spec: ImportSpec, columns: list[str], vocabulary: object | None = None
) -> dict[str, str]:
    """Guess which column feeds which field, for the person to correct.

    A proposal, never a decision: the result is shown in the preview and can be
    changed before anything is validated. Guessing silently is how an import
    puts telephone numbers in the date-of-birth column.

    The static aliases below are deliberately sector-neutral. Anything specific
    to how one country names its year groups comes from `vocabulary` — the
    institution's own configured terminology — so this function recognises what
    a school actually calls things without the platform having an opinion about
    what schools are called.
    """
    by_normal = {_normalise_header(column): column for column in columns}
    mapping: dict[str, str] = {}
    for target in spec.fields:
        candidates = (
            target.key,
            target.label,
            *target.aliases,
            *_vocabulary_aliases(target.key, vocabulary),
        )
        for candidate in candidates:
            column = by_normal.get(_normalise_header(candidate))
            if column and column not in mapping.values():
                mapping[target.key] = column
                break
    return mapping


# --- the people import ----------------------------------------------------

PEOPLE = ImportSpec(
    kind="people",
    title="People and student records",
    description=(
        "Creates a person record and, where a reference or start date is given, "
        "the student relationship and enrolment that go with it. Nothing about "
        "an academic structure is assumed: the placement columns are optional "
        "and an institution that uses none of them imports people alone."
    ),
    fields=(
        Field(
            key="full_name",
            label="Full name",
            required=True,
            aliases=("name", "student name", "learner name", "fullname"),
            max_length=200,
            help_text="Written as the person writes it.",
        ),
        Field(key="given_names", label="Given names",
              aliases=("first name", "forename", "given name"), max_length=120),
        Field(key="family_name", label="Family name",
              aliases=("surname", "last name"), max_length=120),
        Field(key="preferred_name", label="Preferred name",
              aliases=("known as", "nickname"), max_length=120),
        Field(key="date_of_birth", label="Date of birth",
              aliases=("dob", "birth date", "birthday"), parse=parse_past_date),
        Field(key="gender_label", label="Gender", aliases=("sex",), max_length=60),
        Field(key="email", label="Email address",
              aliases=("email address", "e-mail"), parse=parse_email, max_length=320),
        Field(key="phone", label="Telephone", aliases=("phone number", "mobile", "tel"),
              max_length=40),
        Field(key="address", label="Address", aliases=("home address", "residence")),
        # The institution's own identifier for the learner.
        Field(key="reference", label="Reference",
              aliases=("reference", "reference number", "admission number",
                       "admission no", "student number", "matriculation number",
                       "registration number", "student id", "learner id",
                       "candidate number"),
              max_length=64,
              help_text="Admission, matriculation, registration or candidate number."),
        Field(key="kind_label", label="Described as",
              aliases=("student type", "learner type"), max_length=60,
              help_text="The institution's own word — defaults to Student."),
        Field(key="started_on", label="Start date",
              aliases=("date joined", "enrolment date", "admission date",
                       "date of admission"),
              parse=parse_date),
        # Placement, all optional, matched by the institution's own codes.
        Field(key="programme_code", label="Programme code",
              aliases=("programme", "program", "course of study", "track")),
        Field(key="level_code", label="Level code",
              aliases=("level", "level code", "study level")),
        Field(key="class_group_code", label="Class code",
              aliases=("class", "class code", "group", "section")),
        Field(key="cohort_code", label="Cohort code", aliases=("cohort", "intake")),
        # A guardian, created as a person in their own right if named.
        Field(key="guardian_name", label="Guardian name",
              aliases=("parent name", "guardian", "parent/guardian",
                       "next of kin"), max_length=200),
        Field(key="guardian_relationship", label="Guardian relationship",
              aliases=("relationship", "relation"), max_length=60,
              help_text='Free text — "Mother", "Uncle", "Sponsor", anything.'),
        Field(key="guardian_email", label="Guardian email",
              aliases=("parent email", "guardian email address"),
              parse=parse_email, max_length=320),
        Field(key="guardian_phone", label="Guardian telephone",
              aliases=("parent phone", "guardian phone", "contact number"),
              max_length=40),
    ),
    identity_keys=(
        ("reference",),
        ("email",),
        ("full_name", "date_of_birth"),
    ),
)

SPECS: dict[str, ImportSpec] = {PEOPLE.kind: PEOPLE}
