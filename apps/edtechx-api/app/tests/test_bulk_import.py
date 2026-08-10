"""Bulk import, attacked with the files schools actually send.

The requirement this suite exists to hold is one sentence from the brief: *never
allow a malformed import to partially corrupt a school's records without an
explicit, well-designed workflow.* Most of what follows is an attempt to produce
exactly that corruption and fail.

The files are deliberately hostile in ordinary ways rather than exotic ones — a
byte-order mark, semicolons, a title row above the header, a duplicated column
heading, an admission number Excel turned into a float, a Nigerian phone number
beginning with `+`, the same child twice, a class code the school does not have.
Every one of those is a real export from a real system, and an importer that
handles only clean files is an importer nobody can use.
"""

from __future__ import annotations

import io
import uuid as _uuid
from datetime import date

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.modules.academics.models import AcademicYear, ClassGroup, Level
from app.modules.imports import readers, service
from app.modules.imports.models import BatchStatus, ImportBatch, ImportRow
from app.modules.imports.spec import PEOPLE, ImportOptions, propose_mapping
from app.modules.people.enrolment import Enrolment
from app.modules.people.models import GuardianRelationship, Person, StudentRelationship
from app.tests.conftest import TenantFixture, requires_db
from app.tests.test_people_enrolment import _provision
from app.tests.test_universal_education import BRITISH, LADDER, configure, configure_institution

pytestmark = requires_db


# --- files, as schools actually send them ---------------------------------


CLEAN_CSV = (
    "Full Name,Admission No,Date of Birth,Class,Parent Name,Relationship,Parent Phone\n"
    "Aisha Bello,ADM/001,04/03/2015,a,Fatima Bello,Mother,+2348012345678\n"
    "Daniel Okoye,ADM/002,17/11/2014,a,Grace Okoye,Mother,+2348098765432\n"
    "Sofia Rossi,ADM/003,29/02/2016,a,,,\n"
)


def csv_bytes(text_value: str, *, bom: bool = False) -> bytes:
    return (b"\xef\xbb\xbf" if bom else b"") + text_value.encode("utf-8")


def xlsx_bytes(rows: list[list[object]]) -> bytes:
    import openpyxl

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@pytest.fixture(scope="module")
def school() -> TenantFixture:
    fixture = _provision("import-school")
    configure(fixture, BRITISH)
    return fixture


@pytest.fixture(scope="module")
def college() -> TenantFixture:
    """A programme-based institution, to prove the importer is not school-shaped."""
    fixture = _provision("import-college")
    configure_institution(fixture, LADDER)
    return fixture


def staged(
    db: Session, data: bytes, *, filename: str = "students.csv", **options: object
) -> ImportBatch:
    return service.stage(
        db,
        kind="people",
        filename=filename,
        data=data,
        options=ImportOptions(**options) if options else None,
    )


# --- reading ---------------------------------------------------------------


def test_a_byte_order_mark_does_not_become_part_of_the_first_heading() -> None:
    """The single most common reason a mapping silently maps nothing."""
    table = readers.read_csv(csv_bytes(CLEAN_CSV, bom=True))
    assert table.columns[0] == "Full Name"


def test_semicolons_are_read_as_a_delimiter() -> None:
    """A European locale exports semicolons. That file is not malformed."""
    table = readers.read_csv(
        csv_bytes("Full Name;Admission No\nAisha Bello;ADM/001\n")
    )
    assert table.columns == ["Full Name", "Admission No"]
    assert table.rows[0].get("Admission No") == "ADM/001"


def test_a_title_row_above_the_header_is_skipped() -> None:
    table = readers.read_csv(
        csv_bytes("\n\nFull Name,Admission No\nAisha Bello,ADM/001\n")
    )
    assert table.columns == ["Full Name", "Admission No"]
    # And the line number still points at the file, not at the list.
    assert table.rows[0].line_number == 4


def test_a_repeated_heading_stays_addressable() -> None:
    table = readers.read_csv(csv_bytes("Name,Name\nA,B\n"))
    assert table.columns == ["Name", "Name (2)"]
    assert table.notes


def test_blank_lines_between_records_are_not_records() -> None:
    table = readers.read_csv(csv_bytes("Full Name\nAisha\n\n\nDaniel\n"))
    assert [r.get("Full Name") for r in table.rows] == ["Aisha", "Daniel"]
    assert [r.line_number for r in table.rows] == [2, 5]


def test_an_xlsx_file_reads_the_same_way() -> None:
    data = xlsx_bytes(
        [["Full Name", "Admission No"], ["Aisha Bello", "ADM/001"]]
    )
    table = readers.read_xlsx(data)
    assert table.columns == ["Full Name", "Admission No"]
    assert table.rows[0].get("Full Name") == "Aisha Bello"


def test_excel_does_not_turn_an_admission_number_into_a_float() -> None:
    """`004512` typed as a number comes back as `4512.0`. It must not stay that way."""
    table = readers.read_xlsx(xlsx_bytes([["Reference"], [4512]]))
    assert table.rows[0].get("Reference") == "4512"


def test_a_formula_is_flagged_but_a_phone_number_is_not() -> None:
    """The check that would otherwise break every import in Nigeria.

    Standard advice says to reject cells beginning `+` or `-`. A great many real
    phone numbers begin with `+`, so the rule is narrowed to what could actually
    start a function.
    """
    assert readers.looks_like_a_formula("=1+1")
    assert readers.looks_like_a_formula("@SUM(A1)")
    assert readers.looks_like_a_formula("+SUM(A1)")
    assert readers.looks_like_a_formula("-cmd|' /c calc'!A0")
    assert not readers.looks_like_a_formula("+2348012345678")
    assert not readers.looks_like_a_formula("-12.50")


def test_an_unsupported_file_type_is_refused_by_name() -> None:
    with pytest.raises(readers.ImportFileError):
        readers.read(b"MZ\x90\x00", filename="students.exe")


# --- mapping ---------------------------------------------------------------


def test_the_mapping_is_proposed_from_the_headings_a_school_uses() -> None:
    table = readers.read_csv(csv_bytes(CLEAN_CSV))
    mapping = propose_mapping(PEOPLE, table.columns)
    assert mapping["full_name"] == "Full Name"
    assert mapping["reference"] == "Admission No"
    assert mapping["date_of_birth"] == "Date of Birth"
    assert mapping["class_group_code"] == "Class"
    assert mapping["guardian_name"] == "Parent Name"


def test_a_mapping_naming_a_column_that_does_not_exist_is_refused(
    school: TenantFixture,
) -> None:
    """A typo here silently drops a whole column, and the preview looks fine."""
    session = school.session()
    try:
        batch = staged(session, csv_bytes(CLEAN_CSV))
        with pytest.raises(service.ImportRefused):
            service.set_mapping(session, batch, {"full_name": "Nonexistent Column"})
        with pytest.raises(service.ImportRefused):
            service.set_mapping(session, batch, {"invented_field": "Full Name"})
    finally:
        session.rollback()
        session.close()


# --- validation and preview -----------------------------------------------


def test_a_clean_file_validates_and_previews(school: TenantFixture) -> None:
    session = school.session()
    try:
        batch = staged(session, csv_bytes(CLEAN_CSV))
        preview = service.validate(session, batch)
        assert preview.row_count == 3
        assert preview.invalid_count == 0
        assert preview.can_apply
        assert preview.sample_rows, "a preview with no sample is not a preview"
        assert preview.mapping["full_name"] == "Full Name"
        session.commit()
    finally:
        session.close()


def test_every_problem_in_the_file_is_reported_at_once(school: TenantFixture) -> None:
    """One error at a time turns a ten-minute job into a morning."""
    session = school.session()
    try:
        bad = (
            "Full Name,Admission No,Date of Birth,Class\n"
            ",BAD/1,32/13/2015,nosuchclass\n"
        )
        batch = staged(session, csv_bytes(bad))
        preview = service.validate(session, batch)
        assert preview.invalid_count == 1
        errors = preview.problem_rows[0]["errors"]
        assert len(errors) >= 3, errors
        joined = " ".join(errors).lower()
        assert "full name is required" in joined
        assert "date" in joined
        assert "nosuchclass" in joined
        session.commit()
    finally:
        session.close()


def test_the_date_order_is_the_persons_choice_not_a_guess(
    school: TenantFixture,
) -> None:
    """03/04/2015 is two different birthdays and the file cannot say which."""
    session = school.session()
    try:
        content = csv_bytes("Full Name,Date of Birth\nAmbiguous Child,03/04/2015\n")
        day_first = staged(session, content, day_first_dates=True)
        service.validate(session, day_first)
        month_first = staged(
            session, content, filename="us.csv", day_first_dates=False
        )
        service.validate(session, month_first)

        first_row = session.execute(
            select(ImportRow).where(ImportRow.batch_id == day_first.id)
        ).scalars().one()
        second_row = session.execute(
            select(ImportRow).where(ImportRow.batch_id == month_first.id)
        ).scalars().one()
        assert first_row.values["date_of_birth"] == "2015-04-03"
        assert second_row.values["date_of_birth"] == "2015-03-04"
        session.commit()
    finally:
        session.close()


def test_a_class_code_the_school_does_not_have_is_a_row_error(
    school: TenantFixture,
) -> None:
    """Silently dropping it would enrol a child into no class while reporting success."""
    session = school.session()
    try:
        batch = staged(
            session, csv_bytes("Full Name,Class\nLost Child,zz9\n")
        )
        preview = service.validate(session, batch)
        assert preview.invalid_count == 1
        assert "zz9" in " ".join(preview.problem_rows[0]["errors"])
        session.commit()
    finally:
        session.close()


def test_the_same_person_twice_in_one_file_is_an_error(school: TenantFixture) -> None:
    """The person meant one of them. Choosing for them is not ours to do."""
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Admission No\n"
                "Repeated Child,DUP/1\n"
                "Repeated Child Again,DUP/1\n"
            ),
        )
        preview = service.validate(session, batch)
        assert preview.invalid_count == 1
        assert "line 2" in " ".join(preview.problem_rows[0]["errors"])
        assert not preview.can_apply
        session.commit()
    finally:
        session.close()


# --- the dry run and the transaction --------------------------------------


def _count(session: Session, model: type) -> int:
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def test_a_dry_run_writes_nothing(school: TenantFixture) -> None:
    """And is the same code path as the real run, which is the point of it."""
    session = school.session()
    try:
        before = _count(session, Person)
        batch = staged(session, csv_bytes(CLEAN_CSV), filename="dryrun.csv")
        service.validate(session, batch)
        preview = service.apply(session, batch, dry_run=True)
        session.commit()

        assert _count(session, Person) == before, "a dry run created records"
        assert batch.status is BatchStatus.validated
        # Three pupils (person + student relationship + enrolment) and two
        # guardians (person + guardianship): thirteen records that would have
        # been created, and were not.
        assert batch.summary["dry_run_created"] == "13"
        assert preview.invalid_count == 0
    finally:
        session.close()


def test_an_import_applies_everything_it_described(school: TenantFixture) -> None:
    session = school.session()
    try:
        batch = staged(session, csv_bytes(CLEAN_CSV), filename="apply.csv")
        service.validate(session, batch)
        service.apply(session, batch)
        session.commit()

        people_named = {
            p.full_name
            for p in session.execute(select(Person)).scalars().all()
            if p.deleted_at is None
        }
        assert {"Aisha Bello", "Daniel Okoye", "Sofia Rossi"} <= people_named
        # Guardians are people in their own right, with no account.
        assert {"Fatima Bello", "Grace Okoye"} <= people_named

        aisha = session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "ADM/001"
            )
        ).scalars().one()
        placement = session.execute(
            select(Enrolment).where(
                Enrolment.student_relationship_id == aisha.id
            )
        ).scalars().one()
        assert placement.class_group_id is not None
        assert placement.level_id is not None, "the class did not imply its level"
        assert placement.programme_id is None, "a school was given a programme"

        links = session.execute(select(GuardianRelationship)).scalars().all()
        assert {link.relationship_label for link in links} == {"Mother"}
        assert batch.status is BatchStatus.applied
        assert batch.created_count > 0
    finally:
        session.close()


def test_one_bad_row_prevents_the_whole_import(school: TenantFixture) -> None:
    """The requirement, stated as a test.

    Four good rows and one bad one. Nothing lands — not the four, not the one —
    because an import that half-succeeds cannot be safely re-run and cannot be
    unpicked by anyone who was not watching.
    """
    session = school.session()
    try:
        before = _count(session, Person)
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Admission No,Class\n"
                "Good One,PART/1,a\n"
                "Good Two,PART/2,a\n"
                ",PART/3,a\n"
                "Good Three,PART/4,a\n"
                "Good Four,PART/5,nosuchclass\n"
            ),
            filename="partial.csv",
        )
        preview = service.validate(session, batch)
        assert preview.invalid_count == 2
        assert not preview.can_apply

        with pytest.raises(service.ImportRefused):
            service.apply(session, batch)
        session.commit()

        assert _count(session, Person) == before, "rows landed from a refused import"
        assert session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference.in_(["PART/1", "PART/2", "PART/4"])
            )
        ).scalars().all() == []
    finally:
        session.close()


def test_a_failure_part_way_through_leaves_nothing_behind(
    school: TenantFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The case that matters most, forced.

    Validation cannot catch everything — a constraint can fire on row 300 for a
    reason no preview could predict. When it does, the rows already written must
    go with it. Here the third row is made to explode inside `apply`.
    """
    session = school.session()
    try:
        before = _count(session, Person)
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Admission No\n"
                "Survivor One,BOOM/1\n"
                "Survivor Two,BOOM/2\n"
                "Detonator,BOOM/3\n"
                "Survivor Three,BOOM/4\n"
            ),
            filename="boom.csv",
        )
        service.validate(session, batch)

        original = service.people.record_person

        def exploding(db, *, full_name, **fields):
            if full_name == "Detonator":
                raise RuntimeError("a constraint nobody predicted")
            return original(db, full_name=full_name, **fields)

        monkeypatch.setattr(service.people, "record_person", exploding)
        service.apply(session, batch)
        session.commit()

        assert batch.status is BatchStatus.failed
        assert "a constraint nobody predicted" in (batch.failure_reason or "")
        assert batch.created_count == 0
        assert _count(session, Person) == before, (
            "an import that failed part way through left records behind"
        )
        assert session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference.like("BOOM/%")
            )
        ).scalars().all() == []
    finally:
        session.close()


def test_an_already_applied_import_cannot_be_applied_again(
    school: TenantFixture,
) -> None:
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Admission No\nOnce Only,ONCE/1\n"),
            filename="once.csv",
        )
        service.validate(session, batch)
        service.apply(session, batch)
        session.commit()
        with pytest.raises(service.ImportRefused):
            service.apply(session, batch)
    finally:
        session.rollback()
        session.close()


def test_an_unvalidated_import_cannot_be_applied(school: TenantFixture) -> None:
    session = school.session()
    try:
        batch = staged(session, csv_bytes(CLEAN_CSV), filename="unchecked.csv")
        with pytest.raises(service.ImportRefused):
            service.apply(session, batch)
    finally:
        session.rollback()
        session.close()


# --- duplicates against what is already here ------------------------------


def test_somebody_already_here_is_skipped_rather_than_duplicated(
    school: TenantFixture,
) -> None:
    session = school.session()
    try:
        first = staged(
            session,
            csv_bytes("Full Name,Admission No\nExisting Pupil,EXIST/1\n"),
            filename="first.csv",
        )
        service.validate(session, first)
        service.apply(session, first)
        session.commit()

        again = staged(
            session,
            csv_bytes(
                "Full Name,Admission No\n"
                "Existing Pupil,EXIST/1\n"
                "Brand New Pupil,EXIST/2\n"
            ),
            filename="second.csv",
        )
        preview = service.validate(session, again)
        assert preview.duplicate_count == 1
        assert preview.invalid_count == 0
        service.apply(session, again)
        session.commit()

        matches = session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "EXIST/1"
            )
        ).scalars().all()
        assert len(matches) == 1, "the duplicate was imported anyway"
        assert session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "EXIST/2"
            )
        ).scalars().one()
    finally:
        session.close()


def test_a_duplicate_can_be_made_a_hard_error_instead(school: TenantFixture) -> None:
    session = school.session()
    try:
        first = staged(
            session,
            csv_bytes("Full Name,Admission No\nStrict Pupil,STRICT/1\n"),
            filename="strict-first.csv",
        )
        service.validate(session, first)
        service.apply(session, first)
        session.commit()

        again = staged(
            session,
            csv_bytes("Full Name,Admission No\nStrict Pupil,STRICT/1\n"),
            filename="strict-second.csv",
            on_duplicate="error",
        )
        preview = service.validate(session, again)
        assert preview.invalid_count == 1
        assert not preview.can_apply
        session.commit()
    finally:
        session.close()


def test_re_uploading_the_same_file_says_so(school: TenantFixture) -> None:
    """The most common way a school ends up with every student twice."""
    session = school.session()
    try:
        content = csv_bytes("Full Name,Admission No\nSame File Child,SAME/1\n")
        first = staged(session, content, filename="roll.csv")
        service.validate(session, first)
        service.apply(session, first)
        session.commit()

        second = staged(session, content, filename="roll.csv")
        assert any("already imported" in note for note in second.notes)
        session.commit()
    finally:
        session.close()


# --- reversal --------------------------------------------------------------


def test_an_untouched_import_can_be_reversed(school: TenantFixture) -> None:
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Admission No,Class\nMistaken Child,OOPS/1,a\n"),
            filename="mistake.csv",
        )
        service.validate(session, batch)
        service.apply(session, batch)
        session.commit()

        assert service.blockers(session, batch) == []
        service.reverse(session, batch)
        session.commit()

        assert batch.status is BatchStatus.reversed
        person = session.execute(
            select(Person).where(Person.full_name == "Mistaken Child")
        ).scalars().one()
        assert person.deleted_at is not None, "the person is still in every list"

        # The placement is withdrawn, not deleted: `enrolments` holds no DELETE
        # grant, and a placement that happened cannot be made not to have.
        student = session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "OOPS/1"
            )
        ).scalars().one()
        placement = session.execute(
            select(Enrolment).where(Enrolment.student_relationship_id == student.id)
        ).scalars().one()
        assert not placement.is_open
        assert placement.ended_on is not None
    finally:
        session.close()


def test_an_import_that_has_been_built_on_refuses_to_reverse(
    school: TenantFixture,
) -> None:
    """The explicit, well-designed workflow, rather than a choice between damages.

    Once a child has been moved, deleting the imported person would take real
    records with it. So the reversal refuses and says exactly what blocks it.
    """
    from app.modules.people import service as people
    from app.modules.people.service import Placement

    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Admission No,Class\nMoved Since,MOVED/1,a\n"),
            filename="moved.csv",
        )
        service.validate(session, batch)
        service.apply(session, batch)
        session.commit()

        student = session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "MOVED/1"
            )
        ).scalars().one()
        placement = people.open_enrolments(session, student)[0]

        year = session.execute(select(AcademicYear)).scalars().one()
        other_level = (
            session.execute(select(Level).order_by(Level.sequence)).scalars().all()[1]
        )
        group = ClassGroup(
            code=f"rev-{_uuid.uuid4().hex[:4]}", name="Other",
            level_id=other_level.id, academic_year_id=year.id,
        )
        session.add(group)
        session.flush()
        people.transfer(
            session,
            placement,
            to=Placement(level_id=other_level.id, class_group_id=group.id),
            on=date(2027, 1, 10),
        )
        session.commit()

        blocking = service.blockers(session, batch)
        assert blocking, "a reversal was offered over work done since"
        with pytest.raises(service.ImportRefused) as caught:
            service.reverse(session, batch)
        assert "cannot be reversed" in str(caught.value)
        session.rollback()

        # And the person is still there, which is the whole point of refusing.
        assert session.execute(
            select(Person).where(Person.full_name == "Moved Since")
        ).scalars().one().deleted_at is None
    finally:
        session.close()


# --- the importer is not school-shaped ------------------------------------


def test_the_same_importer_serves_a_programme_based_institution(
    college: TenantFixture,
) -> None:
    """No class group, no year group — a programme and a level, from the same file format.

    The importer asks the institution what its codes mean; it does not know
    which kind of institution it is talking to.
    """
    session = college.session()
    try:
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Matriculation Number,Programme,Level\n"
                "Ifeoma Chukwu,MAT/2026/001,bsc-cs,l100\n"
                "Yusuf Adamu,MAT/2026/002,bsc-cs,l100\n"
            ),
            filename="matriculation.csv",
        )
        preview = service.validate(session, batch)
        assert preview.mapping["reference"] == "Matriculation Number"
        assert preview.invalid_count == 0
        service.apply(session, batch)
        session.commit()

        student = session.execute(
            select(StudentRelationship).where(
                StudentRelationship.reference == "MAT/2026/001"
            )
        ).scalars().one()
        placement = session.execute(
            select(Enrolment).where(Enrolment.student_relationship_id == student.id)
        ).scalars().one()
        assert placement.programme_id is not None
        assert placement.level_id is not None
        assert placement.class_group_id is None, (
            "a class group was invented for an institution that has none"
        )
    finally:
        session.close()


def test_a_file_of_people_with_no_academic_columns_imports_people(
    college: TenantFixture,
) -> None:
    """A contact list is a valid import. It creates people and stops there."""
    session = college.session()
    try:
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Email\n"
                "Contact One,contact.one@example.test\n"
                "Contact Two,contact.two@example.test\n"
            ),
            filename="contacts.csv",
        )
        preview = service.validate(session, batch)
        assert preview.invalid_count == 0
        service.apply(session, batch)
        session.commit()

        person = session.execute(
            select(Person).where(Person.email == "contact.one@example.test")
        ).scalars().one()
        assert session.execute(
            select(StudentRelationship).where(
                StudentRelationship.person_id == person.id
            )
        ).scalars().all() == [], "a contact was made a student"
    finally:
        session.close()


# --- isolation and history -------------------------------------------------


def test_an_import_cannot_be_seen_by_another_institution(
    school: TenantFixture, college: TenantFixture
) -> None:
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Admission No\nPrivate Import,SECRET/1\n"),
            filename="private.csv",
        )
        service.validate(session, batch)
        session.commit()
        batch_id = batch.id
    finally:
        session.close()

    stranger = college.session()
    try:
        assert stranger.get(ImportBatch, batch_id) is None
        assert (
            stranger.execute(
                text("SELECT count(*) FROM import_batches WHERE id = :id"),
                {"id": batch_id},
            ).scalar_one()
            == 0
        )
        assert not any(b.filename == "private.csv" for b in service.history(stranger))
    finally:
        stranger.close()


def test_the_history_and_the_error_report_survive_the_session(
    school: TenantFixture,
) -> None:
    """Six months later, somebody asks why a date of birth is wrong."""
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes(
                "Full Name,Date of Birth\n"
                "Recorded Child,04/03/2011\n"
                "Broken Child,not a date\n"
            ),
            filename="year7-september.xlsx.csv",
        )
        service.validate(session, batch)
        session.commit()
        batch_id = batch.id
    finally:
        session.close()

    later = school.session()
    try:
        found = later.get(ImportBatch, batch_id)
        assert found is not None
        assert found.filename == "year7-september.xlsx.csv"
        report = service.error_report(later, found)
        assert len(report) == 1
        assert report[0]["line_number"] == 3
        # The raw value is kept, not just the complaint about it.
        assert report[0]["raw"]["Date of Birth"] == "not a date"

        recorded = later.execute(
            select(ImportRow).where(
                ImportRow.batch_id == batch_id, ImportRow.line_number == 2
            )
        ).scalars().one()
        assert recorded.raw["Date of Birth"] == "04/03/2011"
        assert recorded.values["date_of_birth"] == "2011-03-04"
    finally:
        later.close()


def test_every_import_leaves_an_audit_entry(school: TenantFixture) -> None:
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Admission No\nAudited Child,AUDIT/1\n"),
            filename="audited.csv",
        )
        service.validate(session, batch)
        service.apply(session, batch)
        session.commit()

        entries = session.execute(
            text(
                "SELECT action FROM audit_events WHERE resource_type = 'import_batch' "
                "AND resource_id = :id ORDER BY created_at"
            ),
            {"id": batch.id},
        ).scalars().all()
        assert "create" in entries
        assert len(entries) >= 2, "the upload and the application are two events"
    finally:
        session.close()


def test_the_institutions_own_word_is_recognised_in_a_heading(
    school: TenantFixture,
) -> None:
    """The mapping proposal reads the school's vocabulary, not a list we wrote.

    This school configured `class_group` as "form" (`test_universal_education`),
    so a column headed "Form" is recognised. That word appears nowhere in the
    product — the static alias list is sector-neutral on purpose, and a check in
    `test_universal_education.py` fails the commit that puts one back. A school
    calling the same thing an arm, a homeroom or a set gets the same treatment
    for the same reason: it told us.
    """
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,Form,Pupil Name\nUses Own Words,a,Uses Own Words\n"),
            filename="own-words.csv",
        )
        assert batch.mapping.get("class_group_code") == "Form", batch.mapping
        preview = service.validate(session, batch)
        assert preview.invalid_count == 0
        session.commit()
    finally:
        session.close()


def test_an_unmapped_column_is_shown_rather_than_silently_ignored(
    school: TenantFixture,
) -> None:
    """A column nobody mapped is data the school expected to import."""
    session = school.session()
    try:
        batch = staged(
            session,
            csv_bytes("Full Name,House,Bus Route\nUnmapped Child,Kestrel,Route 4\n"),
            filename="extra-columns.csv",
        )
        preview = service.validate(session, batch)
        assert set(preview.unmapped_columns) == {"House", "Bus Route"}
        session.commit()
    finally:
        session.close()
