"""The import pipeline: read, map, validate, preview, apply, reverse.

The rule this module exists to keep is one sentence: **a malformed import must
never partially corrupt a school's records.** Everything below follows from it.

*Validation is separate from application.* A file is read and checked without
touching anything, and the result is a preview the person can act on. Reading a
file is not a decision.

*Application is one transaction.* Every row lands or none does. There is no
state in which the first four hundred students exist and the rest do not,
because that state is unrecoverable by anyone who was not watching: the operator
cannot tell which rows to re-run, and re-running the file creates four hundred
duplicates.

*A dry run is the same code as the real run.* It executes the identical writes
inside a savepoint and rolls back. A dry run that follows a different path
proves nothing about the path that matters — it is a rehearsal in a different
building.

*A reversal is explicit, and refuses when it cannot be honest.* An import that
has since been built upon — a child marked present, a mark entered, a placement
progressed — cannot be undone by deleting rows, and pretending otherwise would
destroy records that are not the import's to destroy. So the reversal checks,
and says what blocks it.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.academics import service as academics
from app.modules.audit.service import AuditAction, record
from app.modules.customization import terminology
from app.modules.imports import readers
from app.modules.imports.models import (
    BatchStatus,
    ImportBatch,
    ImportRow,
    RowStatus,
)
from app.modules.imports.spec import SPECS, ImportOptions, ImportSpec, propose_mapping
from app.modules.people import service as people
from app.modules.people.service import Placement


class ImportRefused(ValueError):
    """A refusal about the import as a whole, not about one row."""


@dataclass(slots=True)
class RowOutcome:
    """What happened to one row, before anything is written down."""

    line_number: int
    status: RowStatus
    values: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    matched_by: str | None = None
    created: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class Preview:
    """What the person is shown before deciding.

    Deliberately not "the first ten rows". A preview whose sample happens to
    contain no errors is worse than no preview, so the sample is drawn from the
    problems first.
    """

    batch_id: uuid.UUID
    kind: str
    filename: str
    columns: list[str]
    mapping: dict[str, str]
    unmapped_columns: list[str]
    missing_required: list[str]
    row_count: int
    valid_count: int
    invalid_count: int
    duplicate_count: int
    notes: list[str]
    problem_rows: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]

    @property
    def can_apply(self) -> bool:
        return self.invalid_count == 0 and not self.missing_required and self.row_count > 0


def _options_of(batch: ImportBatch) -> ImportOptions:
    stored = batch.options or {}
    return ImportOptions(
        day_first_dates=bool(stored.get("day_first_dates", True)),
        on_duplicate=str(stored.get("on_duplicate", "skip")),
    )


def _spec_of(batch: ImportBatch) -> ImportSpec:
    spec = SPECS.get(batch.kind)
    if spec is None:
        raise ImportRefused(f"{batch.kind!r} is not a kind of import this system knows.")
    return spec


def _jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


# --- 1. staging -----------------------------------------------------------


def stage(
    db: Session,
    *,
    kind: str,
    filename: str,
    data: bytes,
    membership_id: uuid.UUID | None = None,
    options: ImportOptions | None = None,
) -> ImportBatch:
    """Read a file and keep it, without interpreting or applying anything.

    Raises only when the file cannot be read at all. A file full of bad rows is
    not a failure here — it is a preview with four hundred messages, which is
    exactly what the person needs.
    """
    spec = SPECS.get(kind)
    if spec is None:
        raise ImportRefused(f"{kind!r} is not a kind of import this system knows.")

    table = readers.read(data, filename=filename)
    chosen = options or ImportOptions()
    digest = hashlib.sha256(data).hexdigest()

    notes = list(table.notes)
    previous = db.execute(
        select(ImportBatch).where(
            ImportBatch.content_hash == digest,
            ImportBatch.status == BatchStatus.applied,
        )
    ).scalars().first()
    if previous is not None:
        # Not a refusal: re-importing a corrected copy of the same file is
        # legitimate, and the duplicate detection below will handle the rows
        # that are genuinely the same. But it is the most common way a school
        # ends up with every student twice, so it is said out loud.
        notes.append(
            f"This exact file was already imported on "
            f"{previous.applied_at:%d %B %Y} and created "
            f"{previous.created_count} records."
        )

    batch = ImportBatch(
        kind=kind,
        filename=filename[:255],
        content_hash=digest,
        status=BatchStatus.draft,
        columns=list(table.columns),
        # The proposal consults this institution's own vocabulary, so a column
        # headed with whatever word it uses is recognised without that word
        # appearing anywhere in the product.
        mapping=propose_mapping(spec, table.columns, terminology.resolve(db)),
        options={
            "day_first_dates": chosen.day_first_dates,
            "on_duplicate": chosen.on_duplicate,
        },
        notes=notes,
        row_count=table.row_count,
        uploaded_by_membership_id=membership_id,
    )
    db.add(batch)
    db.flush()

    for row in table.rows:
        db.add(
            ImportRow(
                batch_id=batch.id,
                line_number=row.line_number,
                raw=dict(row.values),
                status=RowStatus.pending,
            )
        )
    db.flush()
    record(
        db,
        action=AuditAction.create,
        resource_type="import_batch",
        resource_id=batch.id,
        after={"kind": kind, "filename": batch.filename, "rows": str(table.row_count)},
    )
    return batch


def set_mapping(db: Session, batch: ImportBatch, mapping: dict[str, str]) -> ImportBatch:
    """Replace the proposed mapping with the person's own.

    Refuses a mapping naming a field or a column that does not exist, because a
    typo here silently drops a whole column and the loss is invisible in the
    preview — every row simply looks as though the file did not contain a date
    of birth.
    """
    spec = _spec_of(batch)
    unknown_fields = [key for key in mapping if spec.field_for(key) is None]
    unknown_columns = [c for c in mapping.values() if c not in (batch.columns or [])]
    if unknown_fields:
        raise ImportRefused(f"Unknown fields in the mapping: {sorted(unknown_fields)}")
    if unknown_columns:
        raise ImportRefused(f"The file has no such columns: {sorted(unknown_columns)}")
    batch.mapping = dict(mapping)
    batch.status = BatchStatus.draft
    db.flush()
    return batch


# --- 2. validation --------------------------------------------------------


def _rows_of(db: Session, batch: ImportBatch) -> list[ImportRow]:
    return list(
        db.execute(
            select(ImportRow)
            .where(ImportRow.batch_id == batch.id)
            .order_by(ImportRow.line_number)
        )
        .scalars()
        .all()
    )


def validate(db: Session, batch: ImportBatch) -> Preview:
    """Check every row, and write down what is wrong with each.

    Three kinds of problem, kept distinct because they need different decisions:
    a *field* problem is the person's typo, a *duplicate* is a decision about
    merging, and a *structure* problem — a level code the institution does not
    have — is usually a mapping mistake affecting the whole file.
    """
    spec = _spec_of(batch)
    options = _options_of(batch)
    mapping = batch.mapping or {}
    rows = _rows_of(db, batch)

    missing_required = [
        key for key in spec.required_keys if key not in mapping
    ]

    seen_identities: dict[tuple[str, tuple], int] = {}
    valid = invalid = duplicates = 0

    for row in rows:
        values: dict[str, Any] = {}
        errors: list[str] = []
        for field_key, column in mapping.items():
            target = spec.field_for(field_key)
            if target is None:
                continue
            raw_value = (row.raw or {}).get(column, "")
            if readers.looks_like_a_formula(str(raw_value)):
                errors.append(
                    f"{target.label} begins with a formula character and was not "
                    "imported. Remove the leading = + - or @."
                )
                continue
            parsed, problems = target.read(str(raw_value), options)
            errors.extend(problems)
            if parsed is not None:
                values[field_key] = parsed
        for key in missing_required:
            target = spec.field_for(key)
            errors.append(f"{target.label if target else key} has no column mapped to it.")

        # Structure: codes must name rows this institution actually has.
        placement = academics.resolve_placement(
            db,
            programme_code=str(values.get("programme_code", "") or ""),
            level_code=str(values.get("level_code", "") or ""),
            class_group_code=str(values.get("class_group_code", "") or ""),
            cohort_code=str(values.get("cohort_code", "") or ""),
        )
        errors.extend(placement.problems)

        status = RowStatus.invalid if errors else RowStatus.valid
        matched_by: str | None = None

        if not errors:
            identity = spec.identity_of(values)
            if identity is not None:
                if identity in seen_identities:
                    # A duplicate *within the file* is always an error: the
                    # person meant one of the two rows, and choosing on their
                    # behalf is not a decision this system gets to make.
                    status = RowStatus.invalid
                    errors.append(
                        f"The same record appears on line {seen_identities[identity]} "
                        f"of this file (matched on {identity[0].replace('+', ' and ')})."
                    )
                else:
                    seen_identities[identity] = row.line_number
                    existing = _find_existing(db, values)
                    if existing is not None:
                        matched_by = existing
                        if options.on_duplicate == "error":
                            status = RowStatus.invalid
                            errors.append(
                                f"A record already exists with the same {existing}."
                            )
                        else:
                            status = RowStatus.duplicate

        row.values = {k: _jsonable(v) for k, v in values.items()}
        row.errors = errors
        row.status = status
        row.matched_by = matched_by
        if status is RowStatus.invalid:
            invalid += 1
        elif status is RowStatus.duplicate:
            duplicates += 1
        else:
            valid += 1

    batch.valid_count = valid
    batch.invalid_count = invalid
    batch.duplicate_count = duplicates
    batch.status = BatchStatus.validated if not missing_required else BatchStatus.draft
    db.flush()
    return preview(db, batch, missing_required=missing_required)


def _find_existing(db: Session, values: dict[str, Any]) -> str | None:
    """Whether this row is somebody already here, and on what evidence."""
    reference = str(values.get("reference", "") or "")
    if reference and people.find_student_by_reference(db, reference) is not None:
        return f"reference {reference!r}"
    email = str(values.get("email", "") or "")
    if email and people.find_person_by_email(db, email) is not None:
        return f"email address {email!r}"
    name = str(values.get("full_name", "") or "")
    born = values.get("date_of_birth")
    if isinstance(born, date) and people.find_person_by_name_and_birth(db, name, born):
        return "name and date of birth"
    return None


# --- 3. preview -----------------------------------------------------------


def preview(
    db: Session,
    batch: ImportBatch,
    *,
    limit: int = 10,
    missing_required: list[str] | None = None,
) -> Preview:
    spec = _spec_of(batch)
    rows = _rows_of(db, batch)
    mapping = batch.mapping or {}
    if missing_required is None:
        missing_required = [key for key in spec.required_keys if key not in mapping]

    def describe(row: ImportRow) -> dict[str, Any]:
        return {
            "line_number": row.line_number,
            "status": row.status.value,
            "values": row.values,
            "errors": row.errors,
            "matched_by": row.matched_by,
        }

    problems = [describe(r) for r in rows if r.errors][:limit]
    # The sample is drawn from rows *without* problems, because the problem rows
    # are already shown above and a preview that repeats them hides what a
    # successful row will look like.
    clean = [describe(r) for r in rows if not r.errors][:limit]

    return Preview(
        batch_id=batch.id,
        kind=batch.kind,
        filename=batch.filename,
        columns=list(batch.columns or []),
        mapping=dict(mapping),
        unmapped_columns=[c for c in (batch.columns or []) if c not in mapping.values()],
        missing_required=[
            (spec.field_for(k).label if spec.field_for(k) else k) for k in missing_required
        ],
        row_count=batch.row_count,
        valid_count=batch.valid_count,
        invalid_count=batch.invalid_count,
        duplicate_count=batch.duplicate_count,
        notes=list(batch.notes or []),
        problem_rows=problems,
        sample_rows=clean,
    )


# --- 4. application -------------------------------------------------------


def apply(
    db: Session,
    batch: ImportBatch,
    *,
    dry_run: bool = False,
    membership_id: uuid.UUID | None = None,
) -> Preview:
    """Create the records, all of them or none.

    The work happens inside a savepoint. A dry run rolls it back; a real run
    commits it — and a real run that hits an unexpected failure rolls it back
    too, marks the batch `failed`, and records why. The outcome of every row is
    then written to `import_rows` on the outer transaction, so the report
    survives whichever way the data went.
    """
    if batch.status is BatchStatus.applied:
        raise ImportRefused("This import has already been applied.")
    if batch.status is BatchStatus.reversed:
        raise ImportRefused("This import was reversed; upload the file again.")
    if batch.status is not BatchStatus.validated:
        raise ImportRefused("Validate the import before applying it.")
    if batch.invalid_count:
        raise ImportRefused(
            f"{batch.invalid_count} row(s) have problems. Correct the file and "
            "upload it again, or fix the mapping — an import with known bad rows "
            "is not applied in part."
        )

    rows = _rows_of(db, batch)
    outcomes: list[RowOutcome] = []
    failure: str | None = None

    savepoint = db.begin_nested()
    try:
        for row in rows:
            outcomes.append(_apply_row(db, batch, row))
        db.flush()
    except Exception as exc:  # deliberately wide: the reason is reported, not swallowed
        savepoint.rollback()
        failure = f"{type(exc).__name__}: {exc}"
    else:
        if dry_run:
            savepoint.rollback()
        else:
            savepoint.commit()

    created = sum(len(o.created) for o in outcomes) if failure is None else 0

    if failure is not None:
        batch.status = BatchStatus.failed
        batch.failure_reason = failure
        batch.created_count = 0
        batch.summary = {"applied": "nothing", "reason": failure}
        db.flush()
        record(
            db,
            action=AuditAction.update,
            resource_type="import_batch",
            resource_id=batch.id,
            after={"status": BatchStatus.failed.value},
            reason=failure,
        )
        return preview(db, batch)

    for row, outcome in zip(rows, outcomes, strict=True):
        row.status = outcome.status
        row.errors = outcome.errors
        row.created = outcome.created

    if dry_run:
        # The batch stays validated: nothing happened, and the person is being
        # shown what would.
        batch.summary = {"dry_run_created": str(created)}
    else:
        batch.status = BatchStatus.applied
        batch.created_count = created
        batch.applied_at = datetime.now(UTC)
        batch.applied_by_membership_id = membership_id
        batch.summary = {"created": str(created)}
        record(
            db,
            action=AuditAction.create,
            resource_type="import_batch",
            resource_id=batch.id,
            after={"status": BatchStatus.applied.value, "created": str(created)},
        )
    db.flush()
    return preview(db, batch)


def _apply_row(db: Session, batch: ImportBatch, row: ImportRow) -> RowOutcome:
    """Create what one row describes. Raising here aborts the whole import."""
    options = _options_of(batch)
    values = dict(row.values or {})

    if row.status is RowStatus.duplicate and options.on_duplicate == "skip":
        return RowOutcome(
            line_number=row.line_number,
            status=RowStatus.skipped,
            values=values,
            errors=[f"Left unchanged: already here ({row.matched_by})."],
            matched_by=row.matched_by,
        )

    created: list[dict[str, str]] = []

    person = people.record_person(
        db,
        full_name=str(values["full_name"]),
        given_names=values.get("given_names"),
        family_name=values.get("family_name"),
        preferred_name=values.get("preferred_name"),
        gender_label=values.get("gender_label"),
        date_of_birth=_as_date(values.get("date_of_birth")),
        email=values.get("email"),
        phone=values.get("phone"),
        address=values.get("address"),
    )
    created.append({"type": "person", "id": str(person.id)})

    started_on = _as_date(values.get("started_on"))
    placement_codes = {
        "programme_code": str(values.get("programme_code", "") or ""),
        "level_code": str(values.get("level_code", "") or ""),
        "class_group_code": str(values.get("class_group_code", "") or ""),
        "cohort_code": str(values.get("cohort_code", "") or ""),
    }
    resolved = academics.resolve_placement(db, **placement_codes)

    # A student relationship is created when the row says anything about being
    # a student — a reference, a start date, or a placement. A file of contacts
    # with none of those imports people and stops there, which is correct.
    if values.get("reference") or started_on or any(placement_codes.values()):
        student = people.register_student(
            db,
            person,
            reference=values.get("reference"),
            kind_label=str(values.get("kind_label") or "Student"),
            started_on=started_on,
        )
        created.append({"type": "student_relationship", "id": str(student.id)})

        if started_on or resolved.names_anything:
            enrolment = people.admit(
                db,
                student,
                on=started_on or date.today(),
                placement=Placement(
                    academic_year_id=resolved.academic_year_id,
                    programme_id=resolved.programme_id,
                    level_id=resolved.level_id,
                    class_group_id=resolved.class_group_id,
                    cohort_id=resolved.cohort_id,
                ),
                reason=f"Imported from {batch.filename} line {row.line_number}",
            )
            people.enrol(db, enrolment, on=started_on or date.today())
            created.append({"type": "enrolment", "id": str(enrolment.id)})

    guardian_name = str(values.get("guardian_name", "") or "")
    if guardian_name:
        guardian = people.record_person(
            db,
            full_name=guardian_name,
            email=values.get("guardian_email"),
            phone=values.get("guardian_phone"),
        )
        link = people.link_guardian(
            db,
            guardian=guardian,
            student=person,
            relationship_label=str(values.get("guardian_relationship") or "Guardian"),
            is_primary_contact=True,
        )
        created.append({"type": "person", "id": str(guardian.id)})
        created.append({"type": "guardian_relationship", "id": str(link.id)})

    return RowOutcome(
        line_number=row.line_number,
        status=RowStatus.applied,
        values=values,
        matched_by=row.matched_by,
        created=created,
    )


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


# --- 5. reversal ----------------------------------------------------------


def blockers(db: Session, batch: ImportBatch) -> list[str]:
    """Why this import cannot simply be undone, if it cannot.

    An import is reversible while nothing has been built on top of it. Once a
    child has been marked present, moved, or graded, deleting the person would
    take real records with them — so the reversal refuses and says which rows
    are involved, rather than choosing between two kinds of damage on its own.
    """
    reasons: list[str] = []
    rows = _rows_of(db, batch)
    enrolment_ids = [
        uuid.UUID(item["id"])
        for row in rows
        for item in (row.created or [])
        if item["type"] == "enrolment"
    ]
    for enrolment_id in enrolment_ids:
        placement = people.enrolment(db, enrolment_id)
        if placement is None:
            continue
        if not placement.is_open:
            reasons.append(
                f"An enrolment created by this import has since ended "
                f"({placement.outcome.value if placement.outcome else 'closed'})."
            )
            continue
        events = people.events_for(db, enrolment_id)
        # Admission and enrolment are this import's own two events. Anything
        # further is somebody else's work.
        if len(events) > 2:
            reasons.append(
                "An enrolment created by this import has been changed since "
                f"(there are {len(events)} events on it)."
            )
    return sorted(set(reasons))


def reverse(
    db: Session, batch: ImportBatch, *, membership_id: uuid.UUID | None = None
) -> ImportBatch:
    """Undo an import that nothing has been built on, or refuse and say why.

    People are soft-deleted rather than erased, and enrolments are withdrawn
    rather than deleted — `enrolments` holds no `DELETE` grant precisely so that
    a placement which happened cannot be made not to have happened, and an
    import's mistake does not change that. What reversal restores is the
    *working* state: the wrongly imported people are gone from every list, and
    the record of their brief existence remains where an auditor can find it.
    """
    if batch.status is not BatchStatus.applied:
        raise ImportRefused("Only an applied import can be reversed.")
    blocking = blockers(db, batch)
    if blocking:
        raise ImportRefused(
            "This import cannot be reversed automatically because work has been "
            "done on top of it:\n" + "\n".join(f"  · {b}" for b in blocking)
        )

    today = date.today()
    rows = _rows_of(db, batch)
    for row in rows:
        for item in reversed(row.created or []):
            identifier = uuid.UUID(item["id"])
            if item["type"] == "enrolment":
                placement = people.enrolment(db, identifier)
                if placement is not None and placement.is_open:
                    people.withdraw(
                        db,
                        placement,
                        on=max(today, placement.started_on),
                        reason=f"Import {batch.filename} reversed",
                        actor_membership_id=membership_id,
                        end_relationship=False,
                    )
            elif item["type"] == "guardian_relationship":
                people.unlink_guardian(db, identifier)
            elif item["type"] == "student_relationship":
                relationship = people.student(db, identifier)
                if relationship is not None:
                    people.end_student(db, relationship, on=today)
            elif item["type"] == "person":
                subject = people.person(db, identifier)
                if subject is not None:
                    people.forget_person(db, subject)
        row.status = RowStatus.reversed

    batch.status = BatchStatus.reversed
    batch.reversed_at = datetime.now(UTC)
    db.flush()
    record(
        db,
        action=AuditAction.rollback,
        resource_type="import_batch",
        resource_id=batch.id,
        after={"status": BatchStatus.reversed.value},
        reason=f"Reversed import of {batch.filename}",
    )
    return batch


# --- history --------------------------------------------------------------


def history(db: Session, *, kind: str | None = None, limit: int = 50) -> list[ImportBatch]:
    statement = select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(limit)
    if kind:
        statement = statement.where(ImportBatch.kind == kind)
    return list(db.execute(statement).scalars().all())


def error_report(db: Session, batch: ImportBatch) -> list[dict[str, Any]]:
    """Every problem in the file, in line order, ready to be shown or exported."""
    return [
        {
            "line_number": row.line_number,
            "status": row.status.value,
            "errors": list(row.errors or []),
            "raw": dict(row.raw or {}),
        }
        for row in _rows_of(db, batch)
        if row.errors
    ]
