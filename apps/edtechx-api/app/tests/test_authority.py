"""Signing authority, attacked.

The claim this suite exists to establish is narrow and worth stating exactly:
*a document EdirasX issues was certified by an officer the institution had
authorised to certify it, on the day it was issued, and says so permanently.*

Everything below is a way that could be false. The most important two are not
the obvious ones:

  * **Improvisation.** A system under deadline that finds no signatory and
    prints an empty rule, or reaches for last year's registrar, has forged a
    document on its owner's behalf. Half these tests exist to prove there is no
    such path — not that it is discouraged, that it does not exist.
  * **Retroactive invalidation.** A registrar who leaves must not invalidate the
    four thousand transcripts they signed. A guarantee that only holds while
    nothing changes is not a guarantee.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.modules.documents import service as documents
from app.modules.documents import signatories
from app.modules.documents.authority import (
    AppointmentStatus,
    AssetKind,
    AssetStatus,
    Seal,
    SealStatus,
    SignatoryAppointment,
    SignatureAsset,
    digest_of,
)
from app.modules.people import service as people
from app.tests.conftest import requires_db
from app.tests.test_documents import _build_school, platform  # noqa: F401

pytestmark = requires_db

ISSUE_DAY = date(2027, 1, 20)
A_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="


# --- a school with offices --------------------------------------------------


class Authority:
    def __init__(self, world, **ids: object) -> None:
        self.world = world
        self.__dict__.update(ids)

    def session(self):
        return self.world.fixture.session()


def _authority(world) -> Authority:
    """A registrar's office, a principal's office, and one holder each."""
    session = world.fixture.session()
    try:
        registrar_office = signatories.declare_office(
            session, code="registrar", name="Registrar",
            printed_title="Registrar", sequence=0,
        )
        principal_office = signatories.declare_office(
            session, code="principal", name="Principal", sequence=1,
        )

        holders = {}
        for name, office, kind, content in (
            ("Adaeze Umeh", registrar_office, AssetKind.image, A_PNG),
            ("Idris Kamara", principal_office, AssetKind.typeset, None),
        ):
            person = people.record_person(session, full_name=name)
            asset = signatories.record_asset(
                session, person_id=person.id, kind=kind,
                content=content, typeset_name=name,
            )
            signatories.approve_asset(session, asset, on=date(2026, 8, 1))
            appointment = signatories.appoint(
                session, office=office, person_id=person.id,
                on=date(2026, 9, 1), signature_asset_id=asset.id,
            )
            holders[name] = (person.id, asset.id, appointment.id)

        session.commit()
        return Authority(
            world,
            registrar_office_id=registrar_office.id,
            principal_office_id=principal_office.id,
            holders=holders,
        )
    finally:
        session.close()


@pytest.fixture
def signed() -> Authority:
    return _authority(_build_school(f"authority-{_uuid.uuid4().hex[:8]}"))


def _template(session, *, offices, purpose="transcript", code=None):
    draft = documents.define_template(
        session,
        code=code or f"t-{_uuid.uuid4().hex[:6]}",
        name="Academic Transcript",
        purpose_label="Transcript",
        purpose=purpose,
        sections=[{"key": "identity"}],
        numbering={"prefix": "TR", "scope": "institution"},
        custom={"signatories": list(offices)},
    )
    return documents.publish_template(session, draft)


def _issue(session, world, template, *, on=ISSUE_DAY):
    student = people.student(session, world.students["Ada Nwosu"])
    return documents.issue(
        session,
        template=template,
        student=student,
        permissions=frozenset({"reporting.transcript.create"}),
        issued_on=on,
    )


# --- the registry itself ----------------------------------------------------


def test_an_office_is_the_institutions_word(signed: Authority) -> None:
    session = signed.session()
    try:
        office = signatories.declare_office(
            session, code="shaykh", name="Shaykh al-Ma'had",
            printed_title="Shaykh al-Ma'had and Head of Instruction",
        )
        assert office.code == "shaykh"
        assert office.is_active
    finally:
        session.rollback()
        session.close()


def test_recording_a_signature_does_not_approve_it(signed: Authority) -> None:
    """Two acts, because "somebody uploaded a picture" is not "the institution
    accepted it as this officer's signature"."""
    session = signed.session()
    try:
        person = people.record_person(session, full_name="A Newcomer")
        asset = signatories.record_asset(
            session, person_id=person.id, kind=AssetKind.image, content=A_PNG
        )
        assert asset.status is AssetStatus.drafted
        assert not asset.is_usable(on=ISSUE_DAY)

        signatories.approve_asset(session, asset, on=date(2027, 1, 1))
        assert asset.is_usable(on=ISSUE_DAY)
        # And not before it was approved.
        assert not asset.is_usable(on=date(2026, 12, 31))
    finally:
        session.rollback()
        session.close()


def test_appointing_a_successor_closes_the_predecessor(signed: Authority) -> None:
    session = signed.session()
    try:
        from app.modules.documents.authority import SignatoryOffice

        office = session.get(SignatoryOffice, signed.registrar_office_id)
        successor = people.record_person(session, full_name="Fatima Bello")
        asset = signatories.record_asset(
            session, person_id=successor.id, typeset_name="Fatima Bello"
        )
        signatories.approve_asset(session, asset, on=date(2027, 3, 1))
        signatories.appoint(
            session, office=office, person_id=successor.id,
            on=date(2027, 3, 1), signature_asset_id=asset.id,
        )
        session.flush()

        rows = session.execute(
            select(SignatoryAppointment).where(
                SignatoryAppointment.office_id == office.id
            ).order_by(SignatoryAppointment.appointed_on)
        ).scalars().all()
        assert len(rows) == 2
        assert rows[0].status is AppointmentStatus.ended
        assert rows[0].ended_on == date(2027, 3, 1)
        assert rows[1].status is AppointmentStatus.active

        # And the record of who held the office when is intact in both eras.
        earlier = signatories.appointment_on(session, office, on=date(2027, 1, 1))
        later = signatories.appointment_on(session, office, on=date(2027, 6, 1))
        assert earlier is not None and later is not None
        assert earlier.id != later.id
    finally:
        session.rollback()
        session.close()


def test_two_people_cannot_hold_one_office_at_once(signed: Authority) -> None:
    """Enforced in the database, not only in the service that closes the first."""
    from sqlalchemy.exc import IntegrityError

    session = signed.session()
    try:
        person = people.record_person(session, full_name="An Interloper")
        session.add(
            SignatoryAppointment(
                office_id=signed.registrar_office_id,
                person_id=person.id,
                status=AppointmentStatus.active,
                appointed_on=date(2027, 1, 1),
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
    finally:
        session.rollback()
        session.close()


# --- vacancy refuses issuance ------------------------------------------------


def test_a_signed_template_issues_and_records_who_signed(signed: Authority) -> None:
    session = signed.session()
    try:
        template = _template(session, offices=["registrar", "principal"])
        document = _issue(session, signed.world, template)

        assert [s["office_code"] for s in document.signatures] == [
            "registrar", "principal",
        ]
        registrar = document.signatures[0]
        assert registrar["person_name"] == "Adaeze Umeh"
        assert registrar["asset_kind"] == "image"
        assert registrar["asset_digest"] == digest_of(A_PNG)
        # The typeset officer is a real signature block, not a missing image.
        assert document.signatures[1]["asset_kind"] == "typeset"
        # And the same block is inside the frozen payload, under the checksum.
        assert document.payload["authority"]["signatures"][0]["person_name"] == (
            "Adaeze Umeh"
        )
    finally:
        session.rollback()
        session.close()


def test_a_vacant_office_refuses_issuance(signed: Authority) -> None:
    """The centre of the whole registry. No blank rule, no substitution."""
    session = signed.session()
    try:
        template = _template(session, offices=["registrar"])
        appointment = session.get(
            SignatoryAppointment, signed.holders["Adaeze Umeh"][2]
        )
        signatories.end_appointment(
            session, appointment, on=date(2026, 12, 31), reason="Retired"
        )
        session.flush()

        with pytest.raises(signatories.SignatoryVacancyError) as raised:
            _issue(session, signed.world, template)
        assert raised.value.offices == ("registrar",)
        assert "Registrar" in str(raised.value)
        # And it names the office without naming the person who left.
        assert "Adaeze" not in str(raised.value)
        assert "Retired" not in str(raised.value)
    finally:
        session.rollback()
        session.close()


def test_a_vacancy_does_not_burn_a_document_number(signed: Authority) -> None:
    """Authority is checked before the sequence is drawn from.

    Otherwise a school with a vacant registrarship would tear a hole in its own
    numbering every time somebody pressed Issue — and a transcript series with
    gaps is a series an auditor asks about.
    """
    from app.modules.documents.models import DocumentSequence

    session = signed.session()
    try:
        template = _template(session, offices=["registrar"], code="gap-test")
        appointment = session.get(
            SignatoryAppointment, signed.holders["Adaeze Umeh"][2]
        )
        signatories.end_appointment(session, appointment, on=date(2026, 12, 31))
        session.flush()

        before = session.execute(select(DocumentSequence)).scalars().all()
        with pytest.raises(signatories.SignatoryVacancyError):
            _issue(session, signed.world, template)
        after = session.execute(select(DocumentSequence)).scalars().all()
        assert {(r.scope_key, r.next_value) for r in before} == {
            (r.scope_key, r.next_value) for r in after
        }
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        ("suspend", "suspended"),
        ("revoke", "revoked"),
        ("not_yet", "not_yet_active"),
        ("wrong_category", "wrong_category"),
        ("no_asset", "no_asset"),
        ("asset_unapproved", "asset_not_approved"),
        ("asset_revoked", "asset_revoked"),
        ("office_retired", "office_retired"),
    ],
)
def test_every_way_an_office_cannot_sign_refuses_issuance(
    signed: Authority, mutate: str, reason: str
) -> None:
    """Eight ways, one behaviour: refuse, and say which office and why.

    Parameterised rather than written eight times because the *uniformity* is
    the property under test. A registry with seven refusals and one silent
    substitution is a registry with one hole, and that hole is what somebody
    finds.
    """
    from app.modules.documents.authority import SignatoryOffice

    session = signed.session()
    try:
        template = _template(session, offices=["registrar"])
        appointment = session.get(
            SignatoryAppointment, signed.holders["Adaeze Umeh"][2]
        )
        asset = session.get(SignatureAsset, signed.holders["Adaeze Umeh"][1])
        office = session.get(SignatoryOffice, signed.registrar_office_id)

        if mutate == "suspend":
            appointment.status = AppointmentStatus.suspended
        elif mutate == "revoke":
            appointment.status = AppointmentStatus.revoked
        elif mutate == "not_yet":
            appointment.status = AppointmentStatus.pending
        elif mutate == "wrong_category":
            appointment.purposes = ["report_card"]
        elif mutate == "no_asset":
            appointment.signature_asset_id = None
        elif mutate == "asset_unapproved":
            asset.status = AssetStatus.drafted
        elif mutate == "asset_revoked":
            asset.revoked_on = date(2026, 12, 1)
        elif mutate == "office_retired":
            office.is_active = False
        session.flush()

        verdicts = signatories.readiness(session, template, on=ISSUE_DAY)
        assert [v.reason for v in verdicts] == [reason]
        assert not verdicts[0].ready
        assert verdicts[0].message

        with pytest.raises(signatories.SignatoryVacancyError):
            _issue(session, signed.world, template)
    finally:
        session.rollback()
        session.close()


def test_an_optional_office_is_dropped_rather_than_printed_empty(
    signed: Authority,
) -> None:
    """A blank rule above a printed name is a claim that somebody signed."""
    session = signed.session()
    try:
        template = _template(
            session,
            offices=[
                {"office": "registrar", "required": True},
                {"office": "principal", "required": False},
            ],
        )
        appointment = session.get(
            SignatoryAppointment, signed.holders["Idris Kamara"][2]
        )
        signatories.end_appointment(session, appointment, on=date(2026, 12, 31))
        session.flush()

        document = _issue(session, signed.world, template)
        assert [s["office_code"] for s in document.signatures] == ["registrar"]
        assert all(s["person_name"] for s in document.signatures)
    finally:
        session.rollback()
        session.close()


def test_a_template_cannot_be_published_requiring_an_office_that_does_not_exist(
    signed: Authority,
) -> None:
    session = signed.session()
    try:
        draft = documents.define_template(
            session,
            code="ghost",
            name="Certificate",
            purpose_label="Certificate",
            purpose="document",
            sections=[{"key": "identity"}],
            numbering={"prefix": "CE", "scope": "institution"},
            custom={"signatories": ["chancellor"]},
        )
        with pytest.raises(documents.DocumentError) as raised:
            documents.publish_template(session, draft)
        assert "chancellor" in str(raised.value)
    finally:
        session.rollback()
        session.close()


# --- historical validity -----------------------------------------------------


def test_a_document_stays_signed_after_the_signatory_leaves(
    signed: Authority,
) -> None:
    """The guarantee that only matters once something changes."""
    session = signed.session()
    try:
        template = _template(session, offices=["registrar"])
        document = _issue(session, signed.world, template)
        signed_by = document.signatures[0]["person_name"]

        appointment = session.get(
            SignatoryAppointment, signed.holders["Adaeze Umeh"][2]
        )
        signatories.end_appointment(
            session, appointment, on=date(2027, 6, 30), reason="Left the institution"
        )
        asset = session.get(SignatureAsset, signed.holders["Adaeze Umeh"][1])
        asset.status = AssetStatus.revoked
        asset.revoked_on = date(2027, 6, 30)
        session.flush()

        # The document is unchanged, still names its officer, and still verifies.
        session.refresh(document)
        assert document.signatures[0]["person_name"] == signed_by
        verdict = documents.verify(session, document.verification_code)
        assert verdict is not None
        assert verdict.content_verified
        assert not verdict.integrity_unknown
    finally:
        session.rollback()
        session.close()


def test_editing_the_frozen_signature_breaks_the_checksum(
    signed: Authority,
) -> None:
    """The signature block is inside the tamper-evident envelope, not beside it.

    A forger who leaves the grades alone and changes who certified them has
    changed the document, and the digest has to say so — otherwise the strongest
    claim on the page is the one nothing protects.
    """
    session = signed.session()
    try:
        template = _template(session, offices=["registrar"])
        document = _issue(session, signed.world, template)
        assert documents.verify(session, document.verification_code).content_verified

        payload = dict(document.payload)
        authority = dict(payload["authority"])
        blocks = [dict(b) for b in authority["signatures"]]
        blocks[0]["person_name"] = "Somebody Else"
        authority["signatures"] = blocks
        payload["authority"] = authority
        document.payload = payload
        session.flush()

        verdict = documents.verify(session, document.verification_code)
        assert verdict is not None
        assert not verdict.content_verified
        # And it is a tampering finding, not a deployment gap.
        assert not verdict.integrity_unknown
    finally:
        session.rollback()
        session.close()


def test_a_reprint_draws_the_officer_who_signed_it(signed: Authority) -> None:
    """Not the officer in post today. The renderer reads the payload only."""
    session = signed.session()
    try:
        from app.modules.documents.authority import SignatoryOffice

        template = _template(session, offices=["registrar"])
        document = _issue(session, signed.world, template)

        office = session.get(SignatoryOffice, signed.registrar_office_id)
        successor = people.record_person(session, full_name="Fatima Bello")
        asset = signatories.record_asset(
            session, person_id=successor.id, typeset_name="Fatima Bello"
        )
        signatories.approve_asset(session, asset, on=date(2027, 3, 1))
        signatories.appoint(
            session, office=office, person_id=successor.id,
            on=date(2027, 3, 1), signature_asset_id=asset.id,
        )
        session.flush()

        html = documents.render(session, document)
        assert "Adaeze Umeh" in html
        assert "Fatima Bello" not in html
    finally:
        session.rollback()
        session.close()


# --- seals -------------------------------------------------------------------


def _seal(session, *, code="great", status=SealStatus.approved, **fields) -> Seal:
    content = fields.pop("content", "data:image/svg+xml;base64,PHN2Zy8+")
    row = Seal(
        code=code,
        name="The Great Seal",
        content=content,
        digest=digest_of(content),
        status=status,
        in_force_from=fields.pop("in_force_from", date(2026, 1, 1)),
        **fields,
    )
    session.add(row)
    session.flush()
    return row


def test_a_sealed_document_records_the_seal_in_force(signed: Authority) -> None:
    session = signed.session()
    try:
        seal = _seal(session, approved_on=date(2026, 1, 1))
        draft = documents.define_template(
            session, code="sealed", name="Certificate",
            purpose_label="Certificate", purpose="transcript",
            sections=[{"key": "identity"}],
            numbering={"prefix": "SE", "scope": "institution"},
            custom={"signatories": ["registrar"], "seal": "great"},
        )
        template = documents.publish_template(session, draft)
        document = _issue(session, signed.world, template)

        assert document.seal_id == seal.id
        assert document.seal_digest == seal.digest
        assert document.payload["authority"]["seal"]["code"] == "great"
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize(
    "state",
    ["missing", "unapproved", "revoked", "not_yet_in_force", "expired"],
)
def test_a_missing_or_withdrawn_seal_refuses_issuance(
    signed: Authority, state: str
) -> None:
    """Never a fallback, never a placeholder, never last year's crest."""
    session = signed.session()
    try:
        if state != "missing":
            fields: dict = {}
            status = SealStatus.approved
            if state == "unapproved":
                status = SealStatus.drafted
            elif state == "revoked":
                status = SealStatus.revoked
            elif state == "not_yet_in_force":
                fields["in_force_from"] = date(2028, 1, 1)
            elif state == "expired":
                fields["in_force_until"] = date(2026, 12, 31)
            _seal(session, status=status, **fields)

        draft = documents.define_template(
            session, code=f"sealed-{state}", name="Certificate",
            purpose_label="Certificate", purpose="transcript",
            sections=[{"key": "identity"}],
            numbering={"prefix": "SX", "scope": "institution"},
            custom={"signatories": ["registrar"], "seal": "great"},
        )
        template = documents.publish_template(session, draft)
        with pytest.raises(signatories.SealUnavailableError):
            _issue(session, signed.world, template)
    finally:
        session.rollback()
        session.close()


def test_the_branding_crest_is_not_a_seal(signed: Authority) -> None:
    """Two marks, two governance regimes, and the issuance path reads one.

    `BrandingProfile.crest_url` is the mark at the top of a screen, changeable
    by whoever manages the brand. A seal on a degree certificate is a decision
    with a date attached. A template that asks to be sealed and finds only a
    branding crest is refused, because the crest asserts nothing.
    """
    from app.modules.customization import branding as branding_module

    session = signed.session()
    try:
        branding_module.publish(
            session, display_name="A School", crest_url="https://example.test/crest.svg"
        )
        draft = documents.define_template(
            session, code="crest-only", name="Certificate",
            purpose_label="Certificate", purpose="transcript",
            sections=[{"key": "identity"}],
            numbering={"prefix": "CO", "scope": "institution"},
            custom={"signatories": ["registrar"], "seal": "great"},
        )
        template = documents.publish_template(session, draft)
        with pytest.raises(signatories.SealUnavailableError):
            _issue(session, signed.world, template)
    finally:
        session.rollback()
        session.close()


# --- what the operator is told ----------------------------------------------


def test_readiness_reports_before_anybody_presses_issue(signed: Authority) -> None:
    session = signed.session()
    try:
        template = _template(session, offices=["registrar", "principal"])
        assert all(v.ready for v in signatories.readiness(session, template, on=ISSUE_DAY))

        appointment = session.get(
            SignatoryAppointment, signed.holders["Idris Kamara"][2]
        )
        signatories.end_appointment(session, appointment, on=date(2026, 12, 31))
        session.flush()

        verdicts = signatories.readiness(session, template, on=ISSUE_DAY)
        assert [(v.code, v.ready) for v in verdicts] == [
            ("registrar", True), ("principal", False),
        ]
        assert verdicts[1].message == "The Principal office is vacant."
    finally:
        session.rollback()
        session.close()


def test_a_template_requiring_nothing_signs_nothing(signed: Authority) -> None:
    """An internal progress report is not a certificate and needs no officer."""
    session = signed.session()
    try:
        template = _template(session, offices=[], purpose="report_card")
        student = people.student(session, signed.world.students["Ada Nwosu"])
        document = documents.issue(
            session, template=template, student=student,
            permissions=frozenset({"reporting.report_card.create"}),
            issued_on=ISSUE_DAY,
        )
        assert document.signatures == []
        assert document.payload["authority"]["signatures"] == []
    finally:
        session.rollback()
        session.close()
