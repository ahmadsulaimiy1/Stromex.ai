"""Render representative EdirasX experiences from real institutions.

Not mock-ups. Each page below is produced by provisioning an actual tenant,
configuring its academic world, and asking `experience.resolve` what that
person's interface contains. The nursery administrator's rail has no Programmes
item because that institution has no programme rows — not because this file
omitted one.

That distinction is the whole claim of ADR-031, and a design review is where it
either survives contact with a screen or does not.
"""

from __future__ import annotations

import pathlib
import sys
import uuid as _uuid
from datetime import UTC, date, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "edtechx-api"))

from app.core.context import Grant, Principal  # noqa: E402
from app.db.session import bind_tenant, get_session_factory  # noqa: E402
from app.modules.academics.models import (  # noqa: E402
    AcademicPeriod,
    AcademicStage,
    AcademicYear,
    ClassGroup,
    Course,
    GradingBand,
    GradingScale,
    Level,
    ScaleKind,
)
from app.modules.academics.structure import (  # noqa: E402
    AcademicUnit,
    CreditSystem,
    MilestoneDefinition,
    Programme,
    Qualification,
    SupervisionRole,
)
from app.modules.authz import permissions as perms  # noqa: E402
from app.modules.authz.system_roles import SYSTEM_ROLES_BY_KEY  # noqa: E402
from app.modules.billing import service as billing  # noqa: E402
from app.modules.customization import branding as branding_module  # noqa: E402
from app.modules.customization import terminology  # noqa: E402
from app.modules.design import components as ui  # noqa: E402
from app.modules.design.shell import shell  # noqa: E402
from app.modules.design.theme import for_institution  # noqa: E402
from app.modules.experience import service as experience  # noqa: E402
from app.modules.people import service as people  # noqa: E402
from app.modules.people.service import Placement  # noqa: E402
from app.modules.tenancy.service import provision_school  # noqa: E402

OUT = ROOT / "docs" / "edtechx" / "design"


# --- building institutions ---------------------------------------------------


def _tenant(slug: str, name: str):
    result = provision_school(
        slug=f"{slug}-{_uuid.uuid4().hex[:6]}",
        name=name,
        owner_email=f"owner@{slug}.test",
        owner_name="Owner",
        owner_password="Correct-Horse-Battery-9!",
        base_domain="edtechx.localhost",
    )
    return result.tenant_id


def _session(tenant_id):
    session = get_session_factory()()
    bind_tenant(session, tenant_id)
    return session


def _principal(tenant_id, role_key: str) -> Principal:
    template = SYSTEM_ROLES_BY_KEY[role_key]
    granted = perms.expand(set(template.permissions))
    return Principal(
        user_id=_uuid.uuid4(),
        membership_id=_uuid.uuid4(),
        tenant_id=tenant_id,
        permissions=granted,
        grants=(Grant(frozenset(granted), "tenant", ()),),
        session_id=_uuid.uuid4(),
        authenticated_at=datetime.now(UTC).timestamp(),
    )


def _brand(session, **fields):
    branding_module.publish(session, **fields)


def nursery() -> tuple:
    """Levels, classes, a year. No programmes, no credits, no qualifications."""
    tenant_id = _tenant("nursery", "Willowbrook Early Years")
    session = _session(tenant_id)
    billing.subscribe(session, plan_key="plan.standard")
    _brand(session, display_name="Willowbrook Early Years",
           legal_name="Willowbrook Early Years Centre",
           motto="Where every day is a discovery",
           primary_colour="#2F5D50", accent_colour="#C9A961")
    terminology.publish(session, terms={
        "student": {"singular": "child", "plural": "children"},
        "class_group": {"singular": "room", "plural": "rooms"},
        "guardian": {"singular": "parent", "plural": "parents"},
    })
    stage = AcademicStage(code="early", name="Early Years", sequence=0)
    session.add(stage); session.flush()
    year = AcademicYear(name="2026/27", code="2026", starts_on=date(2026, 9, 1),
                        ends_on=date(2027, 7, 20), is_current=True)
    session.add(year); session.flush()
    session.add(AcademicPeriod(academic_year_id=year.id, name="Autumn", kind_label="Term",
                               sequence=1, starts_on=date(2026, 9, 1),
                               ends_on=date(2026, 12, 18), is_current=True))
    for code, name in (("toddlers", "Toddlers"), ("preschool", "Pre-school")):
        level = Level(code=code, name=name, sequence=0, stage_id=stage.id)
        session.add(level); session.flush()
        session.add(ClassGroup(code=f"{code}-a", name=f"{name} Room",
                               kind_label="Room", level_id=level.id,
                               academic_year_id=year.id))
    for name in ("Amara Bello", "Theo Lindqvist", "Sana Qureshi", "Kofi Mensah"):
        person = people.record_person(session, full_name=name)
        student = people.register_student(session, person, reference="")
        placement = people.admit(session, student, on=date(2026, 9, 1),
                                 placement=Placement(academic_year_id=year.id))
        people.enrol(session, placement, on=date(2026, 9, 1))
    session.commit()
    return tenant_id, session


def secondary() -> tuple:
    tenant_id = _tenant("secondary", "Ashford Grange School")
    session = _session(tenant_id)
    billing.subscribe(session, plan_key="plan.institution")
    _brand(session, display_name="Ashford Grange School",
           legal_name="Ashford Grange School Trust",
           motto="Steady work, honestly done",
           address="14 Ashford Lane, Ikoyi, Lagos",
           contact_email="office@ashfordgrange.example",
           primary_colour="#1A3566", accent_colour="#C9A961",
           verification_url_template="https://verify.ashfordgrange.example/{code}")
    upper = AcademicStage(code="upper", name="Senior School", sequence=1)
    lower = AcademicStage(code="lower", name="Junior School", sequence=0)
    session.add_all([lower, upper]); session.flush()
    year = AcademicYear(name="2026/27", code="2026", starts_on=date(2026, 9, 1),
                        ends_on=date(2027, 7, 31), is_current=True)
    session.add(year); session.flush()
    session.add(AcademicPeriod(academic_year_id=year.id, name="Autumn Term",
                               kind_label="Term", sequence=1,
                               starts_on=date(2026, 9, 1), ends_on=date(2026, 12, 18),
                               is_current=True))
    scale = GradingScale(code="letters", name="School Grades", kind=ScaleKind.letter,
                         is_default=True)
    session.add(scale); session.flush()
    for i, (label, lo, hi, pts, ok) in enumerate((
            ("A", 70, 100, 5, True), ("B", 60, 69.99, 4, True),
            ("C", 50, 59.99, 3, True), ("F", 0, 49.99, 0, False))):
        session.add(GradingBand(scale_id=scale.id, label=label, min_value=lo,
                                max_value=hi, points=pts, is_pass=ok, sequence=i))
    for code, name in (("chem", "Chemistry"), ("hist", "History"),
                       ("math", "Mathematics"), ("eng", "English Literature")):
        session.add(Course(code=code, name=name, grading_scale_id=scale.id))
    for code, name, stage in (("y9", "Year 9", lower), ("y10", "Year 10", upper),
                              ("y11", "Year 11", upper)):
        level = Level(code=code, name=name, sequence=0, stage_id=stage.id)
        session.add(level); session.flush()
        for arm in ("A", "B"):
            session.add(ClassGroup(code=f"{code}{arm.lower()}", name=f"{name[-2:]}{arm}",
                                   level_id=level.id, academic_year_id=year.id))
    session.flush()
    group = session.query(ClassGroup).filter(ClassGroup.code == "y10a").one()
    for name, ref in (("Ada Nwosu", "S-001"), ("Bilal Haddad", "S-002"),
                      ("Chidera Okafor", "S-003"), ("Dina Farouk", "S-004")):
        person = people.record_person(session, full_name=name,
                                      date_of_birth=date(2011, 4, 2))
        student = people.register_student(session, person, reference=ref)
        placement = people.admit(session, student, on=date(2026, 9, 1),
                                 placement=Placement(academic_year_id=year.id,
                                                     level_id=group.level_id,
                                                     class_group_id=group.id))
        people.enrol(session, placement, on=date(2026, 9, 1))
    session.commit()
    return tenant_id, session


def university() -> tuple:
    tenant_id = _tenant("university", "Meridian University")
    session = _session(tenant_id)
    billing.subscribe(session, plan_key="plan.institution")
    _brand(session, display_name="Meridian University",
           legal_name="The University of Meridian",
           motto="Scientia et Integritas",
           address="Senate House, Meridian Campus",
           primary_colour="#2A1F4E", accent_colour="#9A7B4F")
    terminology.publish(session, terms={
        "course": {"singular": "module", "plural": "modules"},
        "class_group": {"singular": "seminar group", "plural": "seminar groups"},
        "academic_period": {"singular": "semester", "plural": "semesters"},
    })
    credits = CreditSystem(code="ects", name="ECTS", unit_label="ECTS credit",
                           unit_label_plural="ECTS credits", is_default=True)
    faculty = AcademicUnit(code="sci", name="Faculty of Science", kind_label="Faculty")
    session.add_all([credits, faculty]); session.flush()
    dept = AcademicUnit(code="cs", name="Department of Computer Science",
                        kind_label="Department", parent_id=faculty.id)
    session.add(dept); session.flush()
    qual = Qualification(code="bsc", name="Bachelor of Science", short_name="BSc",
                         category_label="Undergraduate", framework_level=6,
                         required_credits=360, credit_system_id=credits.id)
    session.add(qual); session.flush()
    year = AcademicYear(name="2026/27", code="2026", starts_on=date(2026, 9, 1),
                        ends_on=date(2027, 8, 31), is_current=True)
    session.add(year); session.flush()
    session.add(AcademicPeriod(academic_year_id=year.id, name="Semester 1",
                               kind_label="Semester", sequence=1,
                               starts_on=date(2026, 9, 21), ends_on=date(2027, 1, 29),
                               is_current=True))
    scale = GradingScale(code="gpa", name="Grade Points", kind=ScaleKind.gpa,
                         is_default=True)
    session.add(scale); session.flush()
    for i, (label, lo, hi, pts, ok) in enumerate((
            ("A", 70, 100, 4.0, True), ("B", 60, 69.99, 3.0, True),
            ("C", 50, 59.99, 2.0, True), ("F", 0, 49.99, 0.0, False))):
        session.add(GradingBand(scale_id=scale.id, label=label, min_value=lo,
                                max_value=hi, points=pts, is_pass=ok, sequence=i))
    for code, name in (("bsc-cs", "BSc Computer Science"),
                       ("bsc-phys", "BSc Physics"), ("ma-hist", "MA History")):
        programme = Programme(code=code, name=name, academic_unit_id=dept.id,
                              qualification_id=qual.id, credit_system_id=credits.id,
                              required_credits=360)
        session.add(programme); session.flush()
        level = Level(code=f"{code}-l4", name="Level 4", sequence=0,
                      programme_id=programme.id)
        session.add(level); session.flush()
        session.add(ClassGroup(code=f"{code}-g", name=f"{name} · Level 4",
                               kind_label="Seminar group", level_id=level.id,
                               academic_year_id=year.id))
        session.add(Course(code=f"{code}-101", name="Algorithms" if "cs" in code
                           else "Foundations", credits=20,
                           credit_system_id=credits.id, grading_scale_id=scale.id,
                           programme_id=programme.id))
    session.flush()
    group = session.query(ClassGroup).filter(ClassGroup.code == "bsc-cs-g").one()
    for name, ref in (("Nadia Rahman", "U-9001"), ("Omar Haddad", "U-9002"),
                      ("Priya Sharma", "U-9003")):
        person = people.record_person(session, full_name=name)
        student = people.register_student(session, person, reference=ref)
        placement = people.admit(session, student, on=date(2026, 9, 21),
                                 placement=Placement(academic_year_id=year.id,
                                                     programme_id=group.level_id and
                                                     session.get(Level, group.level_id).programme_id,
                                                     level_id=group.level_id,
                                                     class_group_id=group.id))
        people.enrol(session, placement, on=date(2026, 9, 21))
    session.commit()
    return tenant_id, session


def doctoral() -> tuple:
    tenant_id = _tenant("doctoral", "Meridian Institute for Advanced Study")
    session = _session(tenant_id)
    billing.subscribe(session, plan_key="plan.institution")
    _brand(session, display_name="Meridian Institute",
           legal_name="Meridian Institute for Advanced Study",
           motto="Ad Fontes", primary_colour="#3E1F2B", accent_colour="#C9A961")
    terminology.publish(session, terms={
        "student": {"singular": "researcher", "plural": "researchers"},
        "programme": {"singular": "research programme", "plural": "research programmes"},
    })
    credits = CreditSystem(code="none", name="Not counted", unit_label="unit",
                           unit_label_plural="units", is_default=True)
    school = AcademicUnit(code="grad", name="Graduate School", kind_label="School")
    session.add_all([credits, school]); session.flush()
    qual = Qualification(code="phd", name="Doctor of Philosophy", short_name="PhD",
                         category_label="Doctoral", framework_level=8,
                         typical_duration_periods=8)
    session.add(qual); session.flush()
    programme = Programme(code="phd-cs", name="PhD in Computer Science",
                          academic_unit_id=school.id, qualification_id=qual.id,
                          is_research=True)
    session.add(programme); session.flush()
    year = AcademicYear(name="2026/27", code="2026", starts_on=date(2026, 10, 1),
                        ends_on=date(2027, 9, 30), is_current=True)
    session.add(year); session.flush()
    session.add(AcademicPeriod(academic_year_id=year.id, name="Session",
                               kind_label="Session", sequence=1,
                               starts_on=date(2026, 10, 1), ends_on=date(2027, 9, 30),
                               is_current=True))
    level = Level(code="phd-y1", name="Year 1", sequence=0, programme_id=programme.id)
    session.add(level); session.flush()
    for i, (code, name, months) in enumerate((
            ("proposal", "Research proposal", 6),
            ("upgrade", "Upgrade viva", 18),
            ("submission", "Thesis submission", 42),
            ("viva", "Viva voce", 48))):
        session.add(MilestoneDefinition(programme_id=programme.id, code=code,
                                        name=name, sequence=i,
                                        expected_offset_months=months))
    for code, name, primary in (("principal", "Principal supervisor", True),
                                ("second", "Second supervisor", False)):
        session.add(SupervisionRole(code=code, name=name, is_primary=primary))
    for name, ref in (("Yusuf Al-Amin", "R-2026-01"), ("Ingrid Sørensen", "R-2026-02")):
        person = people.record_person(session, full_name=name)
        student = people.register_student(session, person, reference=ref,
                                          kind_label="Researcher")
        placement = people.admit(session, student, on=date(2026, 10, 1),
                                 placement=Placement(academic_year_id=year.id,
                                                     programme_id=programme.id,
                                                     level_id=level.id))
        people.enrol(session, placement, on=date(2026, 10, 1))
    session.commit()
    return tenant_id, session


# --- the pages ---------------------------------------------------------------


def _greeting(hour: int = 9) -> str:
    return "Good morning" if hour < 12 else "Good afternoon"


def administrator_page(session, exp, *, figures, headline, roster, agenda,
                       roster_label, roster_columns, notice="") -> str:
    return (
        ui.page_header(
            headline,
            eyebrow=_greeting() + " · " + date(2026, 11, 12).strftime("%A %-d %B"),
            lede=exp.self_description,
            actions=ui.button("Take today's register", variant="primary"),
        )
        + ui.figures(figures)
        + (ui.alert(notice, title="Needs your attention", tone="warning")
           if notice else "")
        + '<div class="ed-grid ed-grid--sidebar" style="margin-block-start:var(--space-8)">'
        + "<div>"
        + ui.section(roster_label, ui.data_table(roster_columns, roster, shape="roster"))
        + "</div>"
        + "<div>"
        + ui.section("Today", f'<ul class="ed-list">{agenda}</ul>', gold=False)
        + "</div></div>"
    )


def build_administrator(tenant_id, session, role_key: str, *, label: str,
                        figures, headline, roster, agenda, roster_label,
                        roster_columns, notice="") -> str:
    principal = _principal(tenant_id, role_key)
    exp = experience.resolve(session, principal, role_keys=[role_key])
    theme = for_institution(session)
    branding = branding_module.resolve(session)
    return shell(
        theme=theme,
        experience=exp,
        branding=branding,
        current="today.dashboard" if "today.dashboard" in exp.keys() else (
            exp.keys()[0] if exp.keys() else ""
        ),
        person=label,
        role=SYSTEM_ROLES_BY_KEY[role_key].name,
        notifications=3,
        title=f"{branding.display_name} — EdirasX",
        topbar_actions=ui.button("New", variant="quiet", size="sm"),
        body=administrator_page(
            session, exp, figures=figures, headline=headline, roster=roster,
            agenda=agenda, roster_label=roster_label,
            roster_columns=roster_columns, notice=notice,
        ),
        font_base="fonts",
    )


def agenda_items(rows) -> str:
    return "".join(
        ui.list_item(title, meta, lead=f'<span class="ed-quiet ed-numeric" '
                     f'style="font-size:var(--text-2xs);min-width:3.2rem">{when}</span>',
                     trail=trail)
        for when, title, meta, trail in rows
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pages: dict[str, str] = {}

    # --- nursery ---
    tenant_id, session = nursery()
    pages["01-nursery-administrator"] = build_administrator(
        tenant_id, session, "admin", label="Grace Odum",
        headline="Willowbrook, this morning",
        roster_label="Children",
        roster_columns=[("Child", "text"), ("Room", "text"), ("Parent", "text"),
                        ("Today", "text")],
        roster=[
            (ui.e(n), "Toddlers Room", g, ui.badge(s, tone=t))
            for n, g, s, t in (
                ("Amara Bello", "Ngozi Bello", "Present", "success"),
                ("Theo Lindqvist", "Marta Lindqvist", "Present", "success"),
                ("Sana Qureshi", "Bilal Qureshi", "Absent", "danger"),
                ("Kofi Mensah", "Akua Mensah", "Present", "success"),
            )
        ],
        figures=[
            ui.figure("Children", "4"),
            ui.figure("Here today", "3", unit="of 4"),
            ui.figure("Rooms", "2"),
            ui.figure("Messages", "1", note="From Sana's parent"),
        ],
        agenda=agenda_items([
            ("08:30", "Morning register — Toddlers Room", "Not yet taken",
             ui.badge("Due", tone="warning")),
            ("11:00", "Sana Qureshi absent", "Parent notified at 08:12", ""),
            ("15:30", "Collection — Kofi Mensah", "Grandparent listed", ""),
        ]),
        notice="This morning's register has not been taken.",
    )
    session.close()

    # --- secondary ---
    tenant_id, session = secondary()
    pages["02-secondary-administrator"] = build_administrator(
        tenant_id, session, "registrar", label="Adaeze Umeh",
        headline="Autumn Term, week nine",
        roster_label="Year 10A",
        roster_columns=[("Student", "text"), ("Class", "text"),
                        ("Attendance", "num"), ("Results", "text")],
        roster=[
            (ui.e(n), "10A", a, ui.badge(s, tone=t))
            for n, a, s, t in (
                ("Ada Nwosu", "98.2%", "Published", "success"),
                ("Bilal Haddad", "94.6%", "Published", "success"),
                ("Chidera Okafor", "88.1%", "In review", "warning"),
                ("Dina Farouk", "96.9%", "Published", "success"),
            )
        ],
        figures=[
            ui.figure("On roll", "412", delta="+18 this term", direction="up"),
            ui.figure("Attendance", "96.4", unit="%", delta="−0.8", direction="down"),
            ui.figure("Result sets", "7", unit="of 9", note="Two awaiting the board"),
            ui.figure("Documents issued", "1,284", delta="+96", direction="up"),
        ],
        agenda=agenda_items([
            ("09:00", "Year 11 results — board approval", "Awaiting the Principal",
             ui.badge("Blocked", tone="warning")),
            ("11:30", "Admissions panel", "Six applications", ""),
            ("14:00", "Report cards — Year 10", "412 ready to issue",
             ui.badge("Ready", tone="success")),
        ]),
        notice="Two result sets are waiting on approvals before they can be published.",
    )
    session.close()

    # --- university ---
    tenant_id, session = university()
    pages["03-university-administrator"] = build_administrator(
        tenant_id, session, "registrar", label="Dr Helena Vasquez",
        headline="Semester 1, week eleven",
        roster_label="BSc Computer Science · Level 4",
        roster_columns=[("Researcher", "text"), ("Programme", "text"),
                        ("Credits", "num"), ("Standing", "text")],
        roster=[
            (ui.e(n), p, c, ui.badge(s, tone=t))
            for n, p, c, s, t in (
                ("Nadia Rahman", "BSc Computer Science", "30", "Good standing", "success"),
                ("Omar Haddad", "BSc Computer Science", "20", "Good standing", "success"),
                ("Priya Sharma", "BSc Computer Science", "10", "Under review", "warning"),
            )
        ],
        figures=[
            ui.figure("Enrolled", "6,140", delta="+212", direction="up"),
            ui.figure("Programmes", "3"),
            ui.figure("Mean GPA", "3.24", note="Level 4, semester 1"),
            ui.figure("Transcripts issued", "418", delta="+64", direction="up"),
        ],
        agenda=agenda_items([
            ("10:00", "Examination Board — Faculty of Science", "Semester 1 results",
             ui.badge("Today", tone="accent")),
            ("13:00", "Credit transfer panel", "Four cases", ""),
            ("16:00", "Transcripts — graduating cohort", "418 to issue",
             ui.badge("Ready", tone="success")),
        ]),
    )
    session.close()

    # --- doctoral ---
    tenant_id, session = doctoral()
    pages["04-doctoral-administrator"] = build_administrator(
        tenant_id, session, "registrar", label="Prof. Idris Kamara",
        headline="Graduate School",
        roster_label="Researchers in candidature",
        roster_columns=[("Researcher", "text"), ("Programme", "text"),
                        ("Next milestone", "text"), ("Due", "text")],
        roster=[
            (ui.e(n), p, m, ui.badge(d, tone=t))
            for n, p, m, d, t in (
                ("Yusuf Al-Amin", "PhD in Computer Science", "Upgrade viva",
                 "In 4 months", "neutral"),
                ("Ingrid Sørensen", "PhD in Computer Science", "Research proposal",
                 "Overdue", "danger"),
            )
        ],
        figures=[
            ui.figure("In candidature", "2"),
            ui.figure("Milestones due", "1", unit="this term"),
            ui.figure("Supervisors", "2"),
            ui.figure("Submissions", "0", note="None expected before 2029"),
        ],
        agenda=agenda_items([
            ("—", "Ingrid Sørensen — research proposal", "Overdue by 3 weeks",
             ui.badge("Overdue", tone="danger")),
            ("—", "Yusuf Al-Amin — upgrade viva", "Panel not yet appointed", ""),
        ]),
        notice="One research proposal is overdue and no panel has been appointed.",
    )
    session.close()

    # --- the people who are not administrators ---
    tenant_id, session = secondary()
    pages["05-teacher-day"] = _frame(
        session, tenant_id, "teacher", person="Olamide Adeyemi",
        body=teacher_day(), notifications=2,
    )
    pages["06-teacher-register"] = _frame(
        session, tenant_id, "teacher", person="Olamide Adeyemi",
        body=teacher_register(), current="operations.attendance", notifications=2,
    )
    pages["07-student-day"] = _frame(
        session, tenant_id, "student", person="Ada Nwosu",
        body=student_day(university=False), notifications=1,
    )
    pages["08-parent-children"] = _frame(
        session, tenant_id, "guardian", person="Ngozi Bello",
        body=parent_overview(), notifications=1,
    )

    # --- workflows, shown over a real page rather than in isolation ---
    palette = ui.command_palette(
        "ada",
        [
            ("Students", [("Ada Nwosu", "10A · S-001", "#"),
                          ("Adaeze Umeh", "Registrar · staff", "#")]),
            ("Classes", [("10A", "Year 10 · 28 students", "#")]),
            ("Documents", [("RC/2026/0001", "Report card · Ada Nwosu", "#")]),
            ("Actions", [("Take today's register", "10A · 08:30", "#"),
                         ("Issue a report card", "Requires published results", "#")]),
        ],
    )
    pages["09-command-palette"] = _frame(
        session, tenant_id, "registrar", person="Adaeze Umeh",
        body=administrator_page(
            session,
            experience.resolve(session, _principal(tenant_id, "registrar"),
                               role_keys=["registrar"]),
            figures=[ui.figure("On roll", "412"), ui.figure("Attendance", "96.4", unit="%"),
                     ui.figure("Result sets", "7", unit="of 9"),
                     ui.figure("Documents issued", "1,284")],
            headline="Autumn Term, week nine", roster=[], agenda="",
            roster_label="Year 10A",
            roster_columns=[("Student", "text")],
        ) + palette,
    )

    notices = "".join([
        ui.notification("Two result sets are blocked",
                        "Year 11 autumn results are waiting on the Principal's approval.",
                        "09:04", priority="urgent", category="Results", unread=True),
        ui.notification("Chidera Okafor — third consecutive absence",
                        "Your school asks for a reason after three.",
                        "08:31", priority="important", category="Attendance", unread=True),
        ui.notification("412 report cards are ready to issue",
                        "Year 10, autumn term. Nothing is outstanding.",
                        "Yesterday", category="Documents"),
        ui.notification("Half-term closure published",
                        "Sent to 412 families.", "Mon", category="Communication"),
    ])
    pages["10-notifications"] = _frame(
        session, tenant_id, "registrar", person="Adaeze Umeh", notifications=2,
        body=ui.page_header("Notifications", eyebrow="2 unread",
                            lede="Urgent first, then what is worth knowing today.",
                            actions=ui.button("Notification settings", size="sm"))
        + ui.tabs([("All", True), ("Unread", False), ("Results", False),
                   ("Attendance", False)])
        + f'<div style="margin-block-start:var(--space-5)">{notices}</div>',
    )

    inspect = ui.drawer(
        "Ada Nwosu",
        ui.section("Placement", ui.data_table(
            [("Field", "text"), ("Value", "text")],
            [("Year group", "Year 10"), ("Class", "10A"),
             ("Admission number", "S-001"), ("Enrolled", "1 September 2026")],
            shape="ledger")) 
        + ui.section("This term", ui.figures([
            ui.figure("Attendance", "98.2", unit="%"),
            ui.figure("Results", "2", unit="of 4"),
        ]), gold=False),
        meta="Year 10 · 10A · S-001",
        actions=ui.button("Close", size="sm")
        + ui.button("Open full record", variant="primary", size="sm"),
    )
    pages["11-drawer"] = _frame(
        session, tenant_id, "registrar", person="Adaeze Umeh",
        body=administrator_page(
            session,
            experience.resolve(session, _principal(tenant_id, "registrar"),
                               role_keys=["registrar"]),
            figures=[ui.figure("On roll", "412"), ui.figure("Attendance", "96.4", unit="%"),
                     ui.figure("Result sets", "7", unit="of 9"),
                     ui.figure("Documents issued", "1,284")],
            headline="Autumn Term, week nine",
            roster=[(ui.e(n), "10A", a, ui.badge(s, tone=t)) for n, a, s, t in (
                ("Ada Nwosu", "98.2%", "Published", "success"),
                ("Bilal Haddad", "94.6%", "Published", "success"))],
            agenda="", roster_label="Year 10A",
            roster_columns=[("Student", "text"), ("Class", "text"),
                            ("Attendance", "num"), ("Results", "text")],
        ) + inspect,
    )

    pages["12-states"] = _frame(
        session, tenant_id, "registrar", person="Adaeze Umeh",
        body=ui.page_header(
            "States, in context",
            eyebrow="Empty · loading · error",
            lede="Each of these belongs to a real screen. None of them says "
                 "\u201cno data\u201d.")
        + ui.section("Waiting for a long publication", ui.panel(
            ui.progress(68, label="Publishing 412 results")
            + '<div style="margin-block-start:var(--space-5)">' + ui.skeleton(lines=4)
            + "</div>"))
        + ui.section("A place with nothing in it yet", ui.panel(ui.empty(
            "No documents issued yet",
            "When you issue a report card or a transcript it appears here, with "
            "its number and the code a parent uses to check it.",
            action=ui.button("Issue a report card", variant="ceremonial", size="sm"),
        ), quiet=True), gold=False)
        + ui.section("Something a person cannot reach", ui.panel(ui.error_state(
            "This is not available to you",
            "Your account does not include this. If you think it should, your "
            "school's administrator can change it \u2014 they will not need to "
            "contact us.",
            action=ui.button("Back to today", size="sm"),
            reference="7F2A-91C4",
        ), quiet=True), gold=False)
        + ui.section("Something that went wrong on our side", ui.panel(ui.error_state(
            "We could not load this just now",
            "Nothing has been lost and nothing was changed. Try again in a "
            "moment; if it keeps happening, quote the reference below.",
            action=ui.button("Try again", variant="primary", size="sm"),
            reference="B4E1-0D77",
        ), quiet=True), gold=False),
    )
    session.close()

    # --- a university student, to prove the same screens adapt ---
    tenant_id, session = university()
    pages["13-university-student"] = _frame(
        session, tenant_id, "student", person="Nadia Rahman",
        body=student_day(university=True), notifications=1,
    )
    session.close()

    for name, html in pages.items():
        target = OUT / f"{name}.html"
        target.write_text(html, encoding="utf-8")
        print(f"{target.name}  {target.stat().st_size/1024:.0f} KB")
    return 0



# --- the people who are not administrators ----------------------------------
#
# A teacher's screen is not "the administrator's, minus some menus". It is
# organised around a day: which classes, in what order, and what is outstanding.
# A student's is organised around what is due. A parent's answers one question —
# how are my children doing — and never shows them the institution's plumbing.


def _frame(session, tenant_id, role_key, *, person, body, current="",
           notifications=0, actions="", title="") -> str:
    exp = experience.resolve(session, _principal(tenant_id, role_key),
                             role_keys=[role_key])
    branding = branding_module.resolve(session)
    return shell(
        theme=for_institution(session),
        experience=exp,
        branding=branding,
        body=body,
        current=current or (exp.keys()[0] if exp.keys() else ""),
        person=person,
        role=SYSTEM_ROLES_BY_KEY[role_key].name,
        notifications=notifications,
        topbar_actions=actions,
        title=title or f"{branding.display_name} — EdirasX",
        font_base="fonts",
    )


def teacher_day() -> str:
    classes = "".join(
        ui.list_item(
            name, meta,
            lead=f'<span class="ed-quiet ed-numeric" style="font-size:var(--text-2xs);'
                 f'min-width:3.4rem">{when}</span>',
            trail=trail,
        )
        for when, name, meta, trail in (
            ("08:30", "10A · Registration", "28 students · Room 12",
             ui.button("Take register", variant="primary", size="sm")),
            ("09:15", "10A · Chemistry", "Practical — safety briefing due", ""),
            ("11:00", "9B · Chemistry", "Test 2 marks outstanding",
             ui.badge("6 to mark", tone="warning")),
            ("13:45", "11C · Chemistry", "Revision", ""),
        )
    )
    return (
        ui.page_header(
            "Thursday morning",
            eyebrow="Good morning, Ms Adeyemi",
            lede="Four classes today. One register outstanding and six papers to mark.",
            actions=ui.button("Take 10A register", variant="primary"),
        )
        + ui.figures([
            ui.figure("Classes today", "4"),
            ui.figure("Registers due", "1", note="10A at 08:30"),
            ui.figure("To mark", "6", unit="papers"),
            ui.figure("Attendance", "96.1", unit="%", note="Your classes, this term"),
        ])
        + '<div class="ed-grid ed-grid--sidebar" style="margin-block-start:var(--space-8)">'
        + "<div>"
        + ui.section("Today", f'<ul class="ed-list">{classes}</ul>')
        + ui.section("Needs you", (
            '<ul class="ed-list">'
            + ui.list_item("Chemistry Test 2 — 9B", "Six papers unmarked · due Friday",
                           trail=ui.button("Open", size="sm"))
            + ui.list_item("Safety briefing — 10A",
                           "Not yet acknowledged by 3 students",
                           trail=ui.badge("3", tone="warning"))
            + "</ul>"
        ), gold=False)
        + "</div><div>"
        + ui.section("Messages", (
            '<ul class="ed-list">'
            + ui.list_item("Ngozi Bello", "Ada will be collected early on Friday")
            + ui.list_item("Head of Science", "Moderation meeting moved to 15:30")
            + "</ul>"
        ), gold=False)
        + "</div></div>"
    )


def teacher_register() -> str:
    """The most repeated screen in the product, and the one that must be fastest.

    Whole-class marking first, then the exceptions — a register is twenty-eight
    taps if you start from nothing and four if you start from "everyone is
    here" (ADR-032).
    """
    def codes(mark):
        return (("P", "Present", mark == "P"),
                ("L", "Late", mark == "L"),
                ("A", "Absent", mark == "A"))

    rows = "".join(
        ui.register_row(name, meta=meta, codes=codes(mark))
        for name, meta, mark in (
            ("Ada Nwosu", "S-001 · 98.2% this term", "P"),
            ("Bilal Haddad", "S-002 · 94.6% this term", "P"),
            ("Chidera Okafor", "S-003 · 88.1% this term", "A"),
            ("Dina Farouk", "S-004 · 96.9% this term", "L"),
        )
    )
    return (
        ui.page_header(
            "10A · Registration",
            eyebrow="Thursday 12 November · 08:30",
            crumbs=[("Today", "#today"), ("10A", "#class"), ("Register", "")],
            actions=ui.button("Mark all present", size="sm"),
        )
        + ui.alert(
            "Chidera Okafor has been absent three sessions running. Your school "
            "asks for a reason after three.",
            title="One absence needs a reason", tone="warning",
        )
        + f'<div class="ed-register" style="margin-block-start:var(--space-6)">{rows}</div>'
        + '<div class="ed-sticky-bar">'
        + '<p class="ed-label">2 present · 1 absent · 1 late</p>'
        + ui.button("Submit register", variant="primary")
        + "</div>"
    )


def student_day(*, university: bool) -> str:
    word = "Module" if university else "Subject"
    items = "".join(
        ui.list_item(name, meta,
                     lead=f'<span class="ed-quiet ed-numeric" '
                          f'style="font-size:var(--text-2xs);min-width:3.4rem">{when}</span>',
                     trail=trail)
        for when, name, meta, trail in (
            ("09:15", "Chemistry", "Room 12 · practical", ""),
            ("11:00", "History", "Essay due today",
             ui.badge("Due today", tone="warning")),
            ("13:45", "Mathematics", "Room 4", ""),
        )
    )
    return (
        ui.page_header(
            "Today",
            eyebrow="Good morning, Ada",
            lede="Three lessons. One essay due at eleven.",
            actions=ui.button("Submit essay", variant="primary"),
        )
        + ui.figures([
            ui.figure("Due this week", "2"),
            ui.figure("Attendance", "98.2", unit="%"),
            ui.figure("Results published", "2", unit=f"of 4 {word.lower()}s"),
            ui.figure("Unread notices", "1"),
        ])
        + '<div class="ed-grid ed-grid--sidebar" style="margin-block-start:var(--space-8)">'
        + "<div>"
        + ui.section("Timetable", f'<ul class="ed-list">{items}</ul>')
        + ui.section("Recent results", ui.data_table(
            [(word, "text"), ("Detail", "text"), ("Grade", "num"), ("", "text")],
            [], shape="matrix",
            empty_state='<table class="ed-table ed-data" data-shape="matrix">'
            f"<thead><tr><th>{word}</th><th>Assessment</th>"
            '<th class="num">Grade</th><th></th></tr></thead><tbody>'
            + ui.matrix_row(subject="Chemistry", grade="A",
                            details=[("Mark", "82 / 100")])
            + ui.matrix_row(subject="History", grade="B",
                            details=[("Mark", "64 / 100")])
            + "</tbody></table>",
        ), gold=False)
        + "</div><div>"
        + ui.section("Notices", (
            '<ul class="ed-list">'
            + ui.list_item("Half-term closure", "School closed 20–24 October")
            + "</ul>"
        ), gold=False)
        + ui.section("Documents", ui.empty(
            "Nothing to collect yet",
            "Your report card appears here when the school publishes it at the "
            "end of term.",
        ), gold=False)
        + "</div></div>"
    )


def parent_overview() -> str:
    """One question, answered before anything else: how are my children doing?"""
    def child(name, klass, attendance, note, tone, actions):
        return ui.panel(
            '<div style="display:flex;align-items:flex-start;gap:var(--space-4)">'
            + ui.avatar(name, large=True)
            + "<div style='flex:1;min-width:0'>"
            + f'<h3 class="ed-heading">{ui.e(name)}</h3>'
            + f'<p class="ed-list__meta">{ui.e(klass)}</p></div>'
            + ui.badge(note, tone=tone)
            + "</div>"
            + ui.figures([
                ui.figure("Attendance", attendance, unit="%"),
                ui.figure("Due this week", "1"),
                ui.figure("Latest report", "Autumn", note="Published 18 Dec"),
            ])
            + '<div style="display:flex;gap:var(--space-2);flex-wrap:wrap;'
              f'margin-block-start:var(--space-4)">{actions}</div>',
            crowned=True,
        )

    return (
        ui.page_header(
            "Your children",
            eyebrow="Good morning, Mrs Bello",
            lede="Everything the school has shared with you, in one place.",
        )
        + '<div class="ed-grid" style="gap:var(--space-6)">'
        + child("Ada Nwosu", "Year 10 · 10A", "98.2", "All well", "success",
                ui.button("Report card", variant="ceremonial", size="sm")
                + ui.button("Message the school", size="sm"))
        + child("Sana Nwosu", "Year 7 · 7B", "91.4", "3 absences", "warning",
                ui.button("Explain an absence", variant="primary", size="sm")
                + ui.button("Report card", size="sm"))
        + "</div>"
        + ui.section("From the school", (
            '<ul class="ed-list">'
            + ui.list_item("Autumn term reports are ready",
                           "Both children · published 18 December")
            + ui.list_item("Parents' evening",
                           "Thursday 15 January · booking opens Monday")
            + "</ul>"
        ), gold=False)
    )

if __name__ == "__main__":
    raise SystemExit(main())
