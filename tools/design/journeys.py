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
from app.modules.billing.plans import PLANS  # noqa: E402
from app.modules.customization import branding as branding_module  # noqa: E402
from app.modules.customization import terminology  # noqa: E402
from app.modules.design import components as ui  # noqa: E402
from app.modules.design import ornament  # noqa: E402
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

    for name, html in pages.items():
        target = OUT / f"{name}.html"
        target.write_text(html, encoding="utf-8")
        print(f"{target.name}  {target.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
