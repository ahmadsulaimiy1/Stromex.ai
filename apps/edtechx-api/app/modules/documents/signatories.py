"""Resolving who signs, and refusing to issue when nobody can.

Every function here answers one question — *may this document be signed today,
and by whom* — and the interesting half of the module is what it does when the
answer is no.

**It refuses, it does not improvise.** There is no code path that prints an
empty rule, reaches for the previous holder, promotes a colleague, or renders a
name with no appointment behind it. `readiness()` names what is missing;
`resolve()` raises. Between them there is no third behaviour, which is the only
way to be sure the third behaviour never appears under deadline.

**It tells the operator, not the world.** `SignatoryVacancyError` carries the
office's own name — "The Registrar's signature is required and the office is
vacant" — because a registrar staring at a failed batch of four hundred
transcripts needs to know which post to fill. It carries no holder names, no
dates of departure, and no reason: the person who left is not the operator's
business and is nobody else's either.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents.authority import (
    AppointmentStatus,
    AssetKind,
    Seal,
    SignatoryAppointment,
    SignatoryOffice,
    SignatureAsset,
    digest_of,
)
from app.modules.people import service as people

__all__ = [
    "REQUIREMENT_REASONS",
    "Requirement",
    "SealUnavailableError",
    "SignatoryVacancyError",
    "SignedBlock",
    "appoint",
    "approve_asset",
    "declare_office",
    "end_appointment",
    "readiness",
    "record_asset",
    "resolve",
    "seal_for",
    "template_offices",
]


class SignatoryVacancyError(ValueError):
    """A document requires an office that cannot sign it today.

    Deliberately one exception for every reason rather than five, because the
    caller's behaviour is identical in all of them — refuse — and because the
    *reason* belongs in the readiness report an operator reads, not in the
    class name a handler switches on.
    """

    def __init__(self, message: str, *, offices: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.offices = offices


class SealUnavailableError(ValueError):
    """A document requires a seal and no approved seal is in force."""


#: Why an office cannot sign. Written for the person who has to fix it, and
#: none of them names the individual concerned.
REQUIREMENT_REASONS: dict[str, str] = {
    "no_office": "This institution has not defined the {office} office.",
    "office_retired": "The {office} office is marked as no longer in use.",
    "vacant": "The {office} office is vacant.",
    "not_yet_active": "The {office} appointment has not started.",
    "suspended": "The {office} appointment is suspended.",
    "revoked": "The {office} appointment has been revoked.",
    "wrong_category": "The {office} is not authorised to sign this kind of document.",
    "no_asset": "The {office} has no approved signature on file.",
    "asset_not_approved": "The {office}'s signature has not been approved.",
    "asset_revoked": "The {office}'s signature has been withdrawn.",
}


@dataclass(frozen=True, slots=True)
class Requirement:
    """One office a template requires, and whether it can sign today."""

    code: str
    label: str
    required: bool
    ready: bool
    reason: str = ""

    @property
    def message(self) -> str:
        if self.ready:
            return ""
        template = REQUIREMENT_REASONS.get(self.reason, "The {office} cannot sign.")
        return template.format(office=self.label)


@dataclass(frozen=True, slots=True)
class SignedBlock:
    """What is frozen onto a document, and what the page draws.

    Everything here is a copy. The document keeps saying who signed it after the
    appointment closes, the asset is superseded and the office is renamed —
    which is the whole point of freezing it (ADR-034, applied to authority).
    """

    office_code: str
    office_name: str
    person_name: str
    printed_title: str
    asset_kind: str
    asset_digest: str
    asset_content: str | None
    appointment_id: str
    signed_on: str

    def as_dict(self) -> dict:
        return {
            "office_code": self.office_code,
            "office_name": self.office_name,
            "person_name": self.person_name,
            "printed_title": self.printed_title,
            "asset_kind": self.asset_kind,
            "asset_digest": self.asset_digest,
            "asset_content": self.asset_content,
            "appointment_id": self.appointment_id,
            "signed_on": self.signed_on,
        }


# --- the registry ----------------------------------------------------------


def declare_office(
    db: Session,
    *,
    code: str,
    name: str,
    printed_title: str = "",
    sequence: int = 0,
) -> SignatoryOffice:
    existing = db.execute(
        select(SignatoryOffice).where(SignatoryOffice.code == code)
    ).scalars().first()
    if existing is not None:
        existing.name = name
        existing.printed_title = printed_title or None
        existing.sequence = sequence
        existing.is_active = True
        db.flush()
        return existing
    row = SignatoryOffice(
        code=code,
        name=name,
        printed_title=printed_title or None,
        sequence=sequence,
    )
    db.add(row)
    db.flush()
    return row


def record_asset(
    db: Session,
    *,
    person_id: uuid.UUID,
    kind: AssetKind = AssetKind.typeset,
    content: str | None = None,
    typeset_name: str = "",
) -> SignatureAsset:
    """Record a specimen. Drafted, not approved: approval is a separate act.

    Two steps rather than one because "somebody uploaded a picture" and "the
    institution accepted it as this officer's signature" are different events,
    and a registry that conflates them cannot answer who approved a signature
    that later turns out to be wrong.
    """
    if kind is AssetKind.image and not content:
        raise ValueError("An image signature needs its content.")
    material = content if kind is AssetKind.image else (typeset_name or "")
    if not material:
        raise ValueError("A typeset signature needs the name it sets.")
    row = SignatureAsset(
        person_id=person_id,
        kind=kind,
        content=content if kind is AssetKind.image else None,
        digest=digest_of(material),
    )
    db.add(row)
    db.flush()
    return row


def approve_asset(
    db: Session,
    asset: SignatureAsset,
    *,
    on: date,
    membership_id: uuid.UUID | None = None,
) -> SignatureAsset:
    from app.modules.documents.authority import AssetStatus

    if asset.status is AssetStatus.revoked:
        raise ValueError("A withdrawn signature cannot be approved again.")
    asset.status = AssetStatus.approved
    asset.approved_on = on
    asset.approved_by_membership_id = membership_id
    db.flush()
    return asset


def appoint(
    db: Session,
    *,
    office: SignatoryOffice,
    person_id: uuid.UUID,
    on: date,
    signature_asset_id: uuid.UUID | None = None,
    purposes: tuple[str, ...] = (),
    printed_name: str = "",
    printed_title: str = "",
    staff_relationship_id: uuid.UUID | None = None,
    membership_id: uuid.UUID | None = None,
) -> SignatoryAppointment:
    """Appoint somebody to an office, closing whoever held it.

    Closing rather than replacing: the previous appointment keeps its dates and
    every document it signed keeps pointing at it.
    """
    live = live_appointment(db, office)
    if live is not None and live.person_id == person_id:
        return live
    if live is not None:
        end_appointment(db, live, on=on, reason="Succeeded")

    row = SignatoryAppointment(
        office_id=office.id,
        person_id=person_id,
        staff_relationship_id=staff_relationship_id,
        signature_asset_id=signature_asset_id,
        status=AppointmentStatus.active,
        appointed_on=on,
        purposes=list(purposes),
        printed_name=printed_name or None,
        printed_title=printed_title or None,
        authorised_at=on,
        authorised_by_membership_id=membership_id,
    )
    db.add(row)
    db.flush()
    return row


def end_appointment(
    db: Session,
    appointment: SignatoryAppointment,
    *,
    on: date,
    reason: str = "",
) -> SignatoryAppointment:
    appointment.status = AppointmentStatus.ended
    appointment.ended_on = on
    appointment.ended_reason = reason or None
    db.flush()
    return appointment


def live_appointment(
    db: Session, office: SignatoryOffice
) -> SignatoryAppointment | None:
    """The appointment currently attached to this office, whatever its status.

    Not "the one that may sign" — a suspended appointment is returned here and
    refused by `_assess`, because "the office is vacant" and "the officer is
    suspended" are different answers and an institution needs to be told which.
    """
    return db.execute(
        select(SignatoryAppointment).where(
            SignatoryAppointment.office_id == office.id,
            SignatoryAppointment.ended_on.is_(None),
            SignatoryAppointment.status != AppointmentStatus.ended,
        )
    ).scalars().first()


def appointment_on(
    db: Session, office: SignatoryOffice, *, on: date
) -> SignatoryAppointment | None:
    """Who held the office on a given date. For reprints and for auditors."""
    rows = db.execute(
        select(SignatoryAppointment)
        .where(
            SignatoryAppointment.office_id == office.id,
            SignatoryAppointment.appointed_on <= on,
        )
        .order_by(SignatoryAppointment.appointed_on.desc())
    ).scalars().all()
    for row in rows:
        if row.ended_on is None or row.ended_on >= on:
            return row
    return None


# --- what a template requires ----------------------------------------------


def template_offices(template) -> tuple[tuple[str, bool], ...]:
    """`(office_code, required)` for one template, from its own configuration.

    Held on the template as JSONB alongside `sections` rather than as a child
    table, for the reason the sections are: a template version is archived and
    must keep describing itself after the office row it named has been renamed
    or retired.
    """
    declared = (template.custom or {}).get("signatories") or []
    out: list[tuple[str, bool]] = []
    for entry in declared:
        if isinstance(entry, str):
            out.append((entry, True))
        elif isinstance(entry, dict) and entry.get("office"):
            out.append((str(entry["office"]), bool(entry.get("required", True))))
    return tuple(out)


def _assess(
    db: Session,
    office: SignatoryOffice | None,
    *,
    code: str,
    purpose: str,
    on: date,
) -> tuple[Requirement, SignatoryAppointment | None, SignatureAsset | None]:
    label = office.name if office is not None else code
    if office is None:
        return Requirement(code, label, True, False, "no_office"), None, None
    if not office.is_active:
        return Requirement(code, label, True, False, "office_retired"), None, None

    appointment = appointment_on(db, office, on=on)
    if appointment is None:
        return Requirement(code, label, True, False, "vacant"), None, None
    if appointment.status is AppointmentStatus.pending:
        return Requirement(code, label, True, False, "not_yet_active"), appointment, None
    if appointment.status is AppointmentStatus.suspended:
        return Requirement(code, label, True, False, "suspended"), appointment, None
    if appointment.status is AppointmentStatus.revoked:
        return Requirement(code, label, True, False, "revoked"), appointment, None
    if not appointment.is_live(on=on):
        return Requirement(code, label, True, False, "vacant"), appointment, None
    if not appointment.covers(purpose):
        return (
            Requirement(code, label, True, False, "wrong_category"),
            appointment,
            None,
        )

    if appointment.signature_asset_id is None:
        return Requirement(code, label, True, False, "no_asset"), appointment, None
    asset = db.get(SignatureAsset, appointment.signature_asset_id)
    if asset is None:
        return Requirement(code, label, True, False, "no_asset"), appointment, None
    if asset.revoked_on is not None and on >= asset.revoked_on:
        return Requirement(code, label, True, False, "asset_revoked"), appointment, asset
    if not asset.is_usable(on=on):
        return (
            Requirement(code, label, True, False, "asset_not_approved"),
            appointment,
            asset,
        )

    return Requirement(code, label, True, True), appointment, asset


def readiness(db: Session, template, *, on: date) -> tuple[Requirement, ...]:
    """Whether every office this template requires can sign, and why not.

    A report rather than an exception, because the screen that lists four
    hundred students ready to receive a transcript should say "the Registrar's
    office is vacant" *before* the operator presses Issue, not after.
    """
    offices = {
        row.code: row
        for row in db.execute(select(SignatoryOffice)).scalars()
    }
    out: list[Requirement] = []
    for code, required in template_offices(template):
        verdict, _appointment, _asset = _assess(
            db, offices.get(code), code=code, purpose=template.purpose, on=on
        )
        out.append(
            verdict if required else Requirement(
                verdict.code, verdict.label, False, verdict.ready, verdict.reason
            )
        )
    return tuple(out)


def resolve(db: Session, template, *, on: date) -> tuple[SignedBlock, ...]:
    """The signature blocks for a document being issued today, or a refusal.

    An optional office that cannot sign is dropped from the page rather than
    printed empty — an empty rule is a claim that somebody signed and did not.
    A required one that cannot sign stops the document.
    """
    offices = {
        row.code: row
        for row in db.execute(select(SignatoryOffice)).scalars()
    }
    blocks: list[SignedBlock] = []
    missing: list[Requirement] = []
    order: list[tuple[int, SignedBlock]] = []

    for code, required in template_offices(template):
        office = offices.get(code)
        verdict, appointment, asset = _assess(
            db, office, code=code, purpose=template.purpose, on=on
        )
        if not verdict.ready:
            if required:
                missing.append(verdict)
            continue
        assert appointment is not None and asset is not None and office is not None
        person = people.person(db, appointment.person_id)
        block = SignedBlock(
            office_code=office.code,
            office_name=office.name,
            person_name=appointment.printed_name
            or (person.full_name if person else ""),
            printed_title=appointment.printed_title
            or office.printed_title
            or office.name,
            asset_kind=asset.kind.value,
            asset_digest=asset.digest,
            asset_content=asset.content,
            appointment_id=str(appointment.id),
            signed_on=on.isoformat(),
        )
        order.append((office.sequence, block))

    if missing:
        raise SignatoryVacancyError(
            " ".join(requirement.message for requirement in missing),
            offices=tuple(requirement.code for requirement in missing),
        )
    blocks = [block for _sequence, block in sorted(order, key=lambda pair: pair[0])]
    return tuple(blocks)


# --- seals ------------------------------------------------------------------


def seal_for(db: Session, template, *, on: date) -> Seal | None:
    """The seal a template requires, or a refusal. `None` if it requires none.

    Never a fallback. If a template says it is sealed and no approved seal is in
    force on the issue date, the document does not exist — the alternative is a
    certificate carrying a mark the institution did not authorise, which is a
    forgery the institution committed against itself.
    """
    code = (template.custom or {}).get("seal")
    if not code:
        return None
    seal = db.execute(select(Seal).where(Seal.code == str(code))).scalars().first()
    if seal is None:
        raise SealUnavailableError(
            f"This template is sealed with {code!r} and no such seal is registered."
        )
    if not seal.is_usable(on=on):
        raise SealUnavailableError(
            f"The {seal.name} is not in force on {on.isoformat()}. A document is "
            "not sealed with a mark the institution has withdrawn."
        )
    return seal
