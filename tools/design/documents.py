"""Render one report card, one transcript and one certificate from one engine.

Three documents, two institutions, one `issue()` call. Nothing here knows which
of them is a transcript — they differ only in which sections their template
lists (ADR-034), and this file exists so that claim can be checked by looking
rather than believed by reading.

The output carries its typefaces as data URIs, so each file is several megabytes
and is deliberately not committed; the screenshots in `shots/` are the record.
Run this, then `shots.py`, to reproduce them.
"""

from __future__ import annotations

import pathlib
import sys
import uuid
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))
OUT = ROOT / "docs" / "edtechx" / "design"


def _seed_plans() -> None:
    from app.db.session import bind_tenant, get_session_factory
    from app.modules.billing import service as billing
    from app.modules.billing.plans import PLANS

    session = get_session_factory()()
    bind_tenant(session, None)
    try:
        billing.seed_plans(session, PLANS)
        session.commit()
    finally:
        session.close()


def main() -> None:
    from app.modules.customization import branding as branding_module
    from app.modules.documents import service as documents
    from app.modules.people import service as people
    from app.tests import test_documents as suite

    # The suite seeds plans from a fixture, which nothing invokes when this
    # file is run on its own. Without it the first `subscribe` fails and the
    # samples are silently the ones from the last run.
    _seed_plans()
    school = suite._build_school(f"sample-school-{uuid.uuid4().hex[:6]}")
    suite._publish_marks(
        school, course_id=school.chemistry_id, period_id=school.autumn_id,
        marks={"Ada Nwosu": 82, "Bilal Haddad": 55}, code="chem-exam",
        kind_label="Examination",
    )
    suite._publish_marks(
        school, course_id=school.history_id, period_id=school.autumn_id,
        marks={"Ada Nwosu": 64, "Bilal Haddad": 41}, code="hist-exam",
        kind_label="Examination",
    )

    session = school.session()
    try:
        branding_module.publish(
            session,
            display_name="Ashford Grange School",
            legal_name="Ashford Grange School Trust",
            motto="Steady work, honestly done",
            address="14 Ashford Lane, Ikoyi, Lagos",
            contact_email="office@ashfordgrange.example",
            contact_phone="+234 1 555 0142",
            primary_colour="#1F3A5F",
            accent_colour="#B08D57",
            footer_note="This report is issued by Ashford Grange School and is "
                        "valid only with the school's document number.",
            verification_url_template="https://verify.ashfordgrange.example/{code}",
        )
        template = suite._report_card_template(session, code="sample-report-card")
        card = documents.issue(
            session, template=template,
            student=people.student(session, school.students["Ada Nwosu"]),
            permissions=suite.REGISTRAR, period_ids=[school.autumn_id],
            issued_on=date(2026, 12, 18),
            comments={
                "class_teacher": "Ada has worked with real care this term. Her "
                                 "practical write-ups are the strongest in the set.",
                "head": "A pleasing report. Well done.",
            },
            signatories={"tutor": "Miss O. Adeyemi", "head": "Dr N. Achebe"},
        )
        (OUT / "01-school-report-card.html").write_text(documents.render(session, card))

        cert_template = documents.define_template(
            session, code="sample-certificate", name="Certificate of Enrolment",
            purpose_label="Certificate of Enrolment", purpose="document",
            sections=[
                {"key": "identity", "title": "Issued to"},
                {"key": "narrative", "options": {"text":
                    "This is to certify that {student_name}, admission number "
                    "{reference}, is enrolled as a student of {institution} and "
                    "is in good standing as at {date}.\n\n"
                    "This certificate is issued at the request of the student's "
                    "family and may be verified using the code below."}},
                {"key": "placement", "title": "Current placement"},
                {"key": "signatures", "options": {"signatories": (
                    {"key": "registrar", "title": "Registrar"},
                )}},
                {"key": "verification"},
            ],
            numbering={"format": "{prefix}-{sequence:04d}", "prefix": "CERT",
                       "scope": "institution"},
        )
        documents.publish_template(session, cert_template)
        certificate = documents.issue(
            session, template=cert_template,
            student=people.student(session, school.students["Bilal Haddad"]),
            permissions=suite.REGISTRAR, issued_on=date(2027, 3, 2),
            signatories={"registrar": "Mr K. Balogun"},
        )
        (OUT / "03-certificate.html").write_text(documents.render(session, certificate))
        session.commit()
    finally:
        session.close()

    university = suite._build_university(f"sample-university-{uuid.uuid4().hex[:6]}")
    suite._publish_marks(
        university, course_id=university.algorithms_id,
        period_id=university.first_id, marks={"Nadia Rahman": 74},
        code="alg", kind_label="Examination",
    )
    suite._publish_marks(
        university, course_id=university.databases_id,
        period_id=university.first_id, marks={"Nadia Rahman": 62},
        code="db", kind_label="Examination",
    )
    session = university.session()
    try:
        branding_module.publish(
            session,
            display_name="Meridian University",
            legal_name="The University of Meridian",
            address="Senate House, Meridian Campus",
            contact_email="records@meridian.example",
            primary_colour="#2A1F4E",
            accent_colour="#9A7B4F",
            footer_note="An official transcript of the University of Meridian. "
                        "Issued under seal; unsealed copies are not official.",
            verification_url_template="https://records.meridian.example/v/{code}",
        )
        template = suite._transcript_template(session, code="sample-transcript")
        transcript = documents.issue(
            session, template=template,
            student=people.student(session, university.students["Nadia Rahman"]),
            permissions=suite.REGISTRAR, issued_on=date(2027, 7, 14),
        )
        (OUT / "02-university-transcript.html").write_text(
            documents.render(session, transcript)
        )
        session.commit()
    finally:
        session.close()

    for path in sorted(OUT.glob("*.html")):
        print(f"{path.name}  {path.stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    main()
