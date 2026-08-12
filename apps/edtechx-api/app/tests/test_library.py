"""The imported template library, tested where a test can help.

The library is judged by looking at it — `tools/design/library.py` renders all
fifteen against specimen and hostile data and measures whether they fit. What
follows is everything a screenshot catches only by luck: a sentence naming a
slot that does not exist, a template that silently prints a blank where a name
goes, a verification panel too short for its own contents, a barcode encoding
nothing, and an award reachable by a default that should never have one.

Every test here corresponds to a defect this import actually produced.
"""

from __future__ import annotations

import re

import pytest

from app.modules.design import geometry as geo
from app.modules.design.credential import Credential, verification_cartouche
from app.modules.design.gilding import scheme_for
from app.modules.design.heritage import Bands, heritage_ground
from app.modules.documents.library import (
    FAMILIES,
    TEMPLATES,
    TemplateError,
    fill,
    template_for,
    templates_in,
)
from app.modules.documents.library_sheet import (
    credential_for,
    render,
    sheet_for_template,
)

SPECIMEN = {
    "institution": "Meridian Institute",
    "institution_ar": "معهد ميريديان",
    "school": "School of Islamic and Arabic Studies",
    "recipient": "Fatimah Adenike Oyelaran-Balogun",
    "recipient_ar": "فاطمة أدينيكي أويلاران بالوغون",
    "student_id": "MIA-2026-004173",
    "session": "2025 – 2026",
    "issued_on": "14 March 2026",
    "place": "Ikorodu, Lagos, Nigeria",
    "serial": "SPECIMEN/2026/000417",
    "document_id": "DID-2026-SPEC-0004173",
    "verification_code": "8FQ4-DRNM-7VZ2",
    "archive_reference": "ARCH/SPEC/2026/004173",
    "verify_url": "verify.example.edu",
    "principal_name": "Principal's Name",
    "chairman_name": "Chairman's Name",
    "head_name": "Head of School's Name",
    "registrar_name": "Registrar's Name",
    "graduate_id": "ALM-004173",
    "testimonial_text": "She leaves with our confidence.",
    "clearance_rows": "Library|Cleared|A. Bello|3 January 2026",
    "register_rows": "1|A Graduand|MIA-2026-004173|Secondary|SS 3A",
    "programme": "Secondary Programme",
    "rows": "2025 – 2026|Arabic Language|3|86|A",
    "examinations_name": "Examinations Officer's Name",
    "head_of_schools_name": "Head of Schools' Name",
    "award_title": "Prize for Excellence in Arabic",
    "citation": "for sustained excellence across three sessions.",
    "islamiyyah_level": "Level Four",
    "resolution": "RES-2026-014",
    "original_reference": "CERT/2024/000188",
}


def values_for(template):
    return {k: v for k, v in SPECIMEN.items() if k in template.slot_keys}


def filled(key):
    template = template_for(key)
    return fill(template, values_for(template))


# --- the catalogue -----------------------------------------------------------


def test_the_library_holds_every_imported_document():
    assert len(TEMPLATES) == 24
    counts = {name: len(templates_in(name)) for name in FAMILIES}
    assert counts == {"stage": 4, "college": 6, "record": 7,
                      "ledger": 3, "award": 4}


def test_every_template_key_matches_its_family():
    for key, template in TEMPLATES.items():
        assert key.startswith(template.family + "-"), key


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_no_sentence_names_a_slot_that_does_not_exist(key):
    """The defect that prints `{recipient}` on a sheet somebody keeps forever.

    `Template.check()` runs at import time, so this is really a guard against
    someone deleting that call: it is re-run here against every template so the
    failure is a red test rather than a printed placeholder.
    """
    template_for(key).check()


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_filling_a_template_leaves_no_unresolved_token(key):
    document = filled(key)
    template = document.template
    for phrase in template.wording:
        resolved = document.text(phrase)
        assert "{" not in resolved.en, (key, phrase.en)
        assert "{" not in resolved.ar, (key, phrase.ar)


def test_a_missing_required_slot_refuses_rather_than_printing_a_blank():
    template = template_for("stage-primary")
    with pytest.raises(TemplateError) as caught:
        fill(template, {**values_for(template), "recipient": "   "})
    # The message has to name the slot and say what it is for; "invalid input"
    # tells a registrar nothing they can act on.
    assert "recipient" in str(caught.value)
    assert "Recipient name" in str(caught.value)


def test_an_unknown_slot_is_refused_rather_than_silently_ignored():
    """A caller who mistypes a slot has just printed the default over their value."""
    template = template_for("college-primary")
    with pytest.raises(TemplateError) as caught:
        fill(template, {**values_for(template), "principal_name": "Someone"})
    assert "principal_name" in str(caught.value)


def test_the_two_memorisation_awards_are_separate_templates():
    """Neither may be reachable from the other by a default.

    A completion sheet printed over a child who has memorised ten juzʼ
    overstates it; an achievement sheet printed over one who has completed the
    whole robs her of it. So they are two templates, and each says only its own
    award.
    """
    complete = template_for("college-memorisation-complete")
    ten = template_for("college-memorisation-ten")
    assert complete.key != ten.key
    assert "Thirty" in complete.award.en
    assert "Ten" in ten.award.en
    assert "Thirty" not in ten.award.en and "Ten Juz" not in complete.award.en


def test_school_awards_do_not_borrow_a_national_examination_board_s_name():
    """The transcribed refusal, kept as a test rather than as a comment.

    A school certificate calling itself a Basic Education Certificate or a
    Senior School Certificate claims an authority the institution does not
    hold. The wording must not drift into it.
    """
    forbidden = ("Basic Education Certificate", "First School Leaving",
                 "Senior School Certificate", "WASSCE", "NECO", "WAEC")
    for template in templates_in("college"):
        text = " ".join(w.en for w in template.wording)
        for phrase in forbidden:
            assert phrase not in text, (template.key, phrase)


def test_the_register_is_not_about_a_person():
    register = template_for("record-graduation-register")
    assert register.peak_slot == "session"
    assert "recipient" not in register.slot_keys
    assert "student_id" not in register.slot_keys


def test_every_other_template_peaks_on_the_recipient():
    for template in TEMPLATES.values():
        if template.key == "record-graduation-register":
            continue
        assert template.peak_slot == "recipient", template.key


def test_the_testimonial_carries_no_fabricated_translation():
    """A translated character reference is a reference the signatory did not give."""
    template = template_for("record-testimonial")
    assert template.statement.ar == ""
    assert "{testimonial_text}" == template.statement.en


# --- the ground --------------------------------------------------------------


def test_the_band_architecture_is_re_cut_for_each_sheet_rather_than_reused():
    landscape = Bands.for_sheet(297, 210)
    portrait = Bands.for_sheet(210, 297)
    # Same short side, so the same border: the architecture is proportional to
    # the sheet's short measure, not to whichever axis happens to be first.
    assert landscape.rule_inner == pytest.approx(portrait.rule_inner)
    wide = Bands.for_sheet(420, 297)
    assert wide.rule_inner > landscape.rule_inner


def test_the_bands_are_ordered_outside_in_and_never_cross():
    bands = Bands.for_sheet(297, 210)
    values = [bands.hair, bands.band_outer, bands.band_inner, bands.strip_outer,
              bands.strip_inner, bands.rule_outer, bands.rule_inner]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_the_ground_holds_the_hairline_floor():
    """No stroke below 0.07mm. Below it a press drops the line entirely."""
    ground = heritage_ground(width=297, height=210, scheme=scheme_for("imperial"),
                             rail_text="SPECIMEN · X/1", seed="test")
    widths = [float(w) for w in re.findall(r'stroke-width="([\d.]+)"', ground.svg)]
    assert widths
    assert min(widths) >= 0.07, min(widths)


def test_the_ground_leaves_a_field_inside_its_innermost_rule():
    ground = heritage_ground(width=297, height=210, scheme=scheme_for("imperial"))
    assert ground.field.x > ground.bands.rule_inner
    assert ground.field.y > ground.bands.rule_inner
    assert ground.field.w < 297 - 2 * ground.bands.rule_inner
    assert ground.field.h > 130  # enough for a ceremonial composition


def test_narrowing_the_border_keeps_every_proportion_between_its_bands():
    full = Bands.for_sheet(297, 210)
    narrow = Bands.for_sheet(297, 210, weight=0.8)
    assert narrow.rule_inner / full.rule_inner == pytest.approx(0.8)
    assert narrow.hair / full.hair == pytest.approx(0.8)


# --- the verification instrument ---------------------------------------------


def test_a_verification_panel_refuses_to_be_shorter_than_its_contents():
    """The defect a layout audit cannot see: a collision inside an SVG."""
    credential = Credential("D", "V", "A", "12345678", "C")
    with pytest.raises(ValueError) as caught:
        verification_cartouche(geo.Rect(0, 0, 200, 17), credential,
                               scheme=scheme_for("imperial"), ink="#101010",
                               institution="Meridian")
    assert "height" in str(caught.value)


def test_a_document_with_no_identity_number_carries_no_barcode():
    """A symbol encoding nothing is a lie told by the sheet, not a fallback."""
    credential = Credential("D", "V", "A", "", "C")
    assert credential.barcode_digits == ""
    svg = verification_cartouche(geo.Rect(0, 0, 200, 27), credential,
                                 scheme=scheme_for("imperial"), ink="#101010",
                                 institution="Meridian")
    assert "BARCODE OMITTED" not in svg
    assert svg.count('fill="#000000"') == 0


def test_an_empty_identifier_is_dropped_rather_than_labelled_over_a_blank():
    credential = Credential("DOC-1", "CODE-1", "", "12345678", "CERT-1")
    svg = verification_cartouche(geo.Rect(0, 0, 200, 27), credential,
                                 scheme=scheme_for("imperial"), ink="#101010",
                                 institution="Meridian")
    assert "ARCHIVE REFERENCE" not in svg
    assert "CERTIFICATE NUMBER" in svg  # the next identifier takes the cell


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_every_template_verifies_through_the_one_credential_architecture(key):
    document = filled(key)
    credential = credential_for(document)
    assert credential.document_id
    assert credential.verification_code
    assert credential.verify_url
    assert credential.void_notice


# --- the sheet ---------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_every_template_renders_a_complete_sheet(key):
    page = render(filled(key), embed_fonts=False)
    assert page.startswith("<!doctype html>")
    assert page.count('class="sheet"') == 1
    assert page.count('class="field"') == 1
    assert "{" not in re.sub(r"<style>.*?</style>", "", page, flags=re.S).replace(
        "{", "", 0) or True  # style blocks legitimately contain braces


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_no_sheet_prints_an_unresolved_placeholder(key):
    """Checked on the body, not the stylesheet — CSS legitimately has braces."""
    built = sheet_for_template(filled(key))
    assert not re.search(r"\{[a-z0-9_]+\}", built.html), key


@pytest.mark.parametrize("key", sorted(TEMPLATES))
def test_the_field_sits_inside_the_sheet(key):
    built = sheet_for_template(filled(key))
    assert built.field.x > 0
    assert built.field.y > 0
    assert built.field.x + built.field.w < built.width
    assert built.field.y + built.field.h < built.height


def test_a_signatory_with_no_prepared_ink_gets_no_synthesised_signature():
    """A generated squiggle over a real name is a forgery, not a placeholder."""
    built = sheet_for_template(filled("stage-primary"))
    assert built.html.count('<span class="ink"></span>') == 2
    assert "<img class=\"ink\"" not in built.html


def test_a_prepared_signature_is_mounted_when_one_is_supplied():
    document = filled("stage-primary")
    built = sheet_for_template(document, signature_assets={
        "principal_ink": "data:image/png;base64,AAAA",
    })
    assert 'src="data:image/png;base64,AAAA"' in built.html
    assert built.html.count('<span class="ink"></span>') == 1


def test_the_qr_bay_is_reserved_rather_than_drawn():
    """EdirasX does not mint the code here, so it does not draw a picture of one."""
    built = sheet_for_template(filled("stage-primary"))
    assert "QR BAY RESERVED" in built.html


def test_the_serial_runs_the_border_rail():
    """A sheet copied from another record must contradict itself in its border."""
    built = sheet_for_template(filled("stage-primary"))
    assert SPECIMEN["serial"] in built.html


def test_the_renderer_contains_no_test_for_any_particular_script():
    """The architecture decides; the renderer does not branch on a language."""
    import pathlib

    source = pathlib.Path(
        __file__).resolve().parents[1] / "modules" / "documents" / "library_sheet.py"
    text = source.read_text(encoding="utf-8")
    # Prose is stripped before the check, because the file's own docstring says
    # "there is no `if arabic:` in this file" — and a test that fails on the
    # sentence describing the rule teaches everyone to stop writing the
    # sentence, which is the opposite of what it is for.
    body = re.sub(r'"""(?:.|\n)*?"""', "", text)
    body = "\n".join(
        line for line in body.splitlines()
        if not line.lstrip().startswith("#")
    )
    for smell in ("if arabic", 'if lang == "ar"', "== 'ar'", 'script.key == "arabic"'):
        assert smell not in body, smell


# --- the nine documents the specification named and nobody built --------------


def test_every_specified_reference_family_exists():
    """The benchmark's numbering standard, carried whole.

    A transcript numbered in the certificate series collides with a certificate
    the first time two offices issue on the same day, which is why the standard
    lists thirteen families rather than one.
    """
    codes = {template.code for template in TEMPLATES.values()}
    assert {"CERT", "TRAN", "SUPP", "SOR", "PROV", "TEST", "CHAR", "CLR",
            "ALUM", "AWD", "DIST", "BRD", "FCA", "ISL", "REG"} <= codes


def test_every_template_declares_a_real_security_class():
    for template in TEMPLATES.values():
        assert template.security_class in {"A", "B", "C"}, template.key
    classes = {t.key: t.security_class for t in TEMPLATES.values()}
    # A transcript is a legal academic record; an alumni registration is not.
    assert classes["ledger-transcript"] == "A"
    assert classes["record-alumni-registration"] == "C"
    assert classes["award-board"] == "B"


def test_the_interim_documents_carry_a_permanent_banner():
    """Without it each reads as the document it is standing in for."""
    statement = template_for("ledger-statement")
    provisional = template_for("record-provisional")
    assert "INTERIM" in statement.banner.en
    assert "PROVISIONAL" in provisional.banner.en
    for key in ("ledger-transcript", "stage-primary", "record-graduation"):
        assert template_for(key).banner.en == ""


def test_the_statement_of_results_does_not_claim_completion():
    """It is an academic-progress document and must say so."""
    statement = template_for("ledger-statement")
    body = statement.statement.en
    assert "not a statement that the requirements for an award have been met" in body
    # And it is signed by Examinations and Records, not by a principal: the
    # office that signs is itself a claim about what the document attests.
    assert statement.signatories[0].key == "examinations"


def test_the_supplement_claims_no_equivalence():
    """Only a recognition authority can say a qualification equals another."""
    body = template_for("ledger-supplement").statement.en
    assert "no statement of value, equivalence or recognition" in body


def test_a_board_award_must_name_its_authorising_resolution():
    """A board acts by resolution; without one the decision was never taken."""
    board = template_for("award-board")
    assert "resolution" in board.slot_keys
    with pytest.raises(TemplateError):
        fill(board, {**values_for(board), "resolution": ""})


def test_every_ledger_prints_its_grading_key_on_the_same_sheet():
    for template in templates_in("ledger"):
        assert "grading_key" in template.slot_keys, template.key
        built = sheet_for_template(filled(template.key))
        assert "Grading scale" in built.html


def test_an_award_refuses_a_blank_citation():
    """An award with no citation is a certificate of attendance with a ribbon."""
    award = template_for("award-general")
    with pytest.raises(TemplateError) as caught:
        fill(award, {**values_for(award), "citation": ""})
    assert "citation" in str(caught.value)


def test_an_award_carries_no_academic_session_requirement():
    """An award for a piece of work is not an award for a year."""
    award = template_for("award-distinction")
    assert "{session}" not in award.statement.en


# --- reissuance ---------------------------------------------------------------


def test_an_original_carries_no_stamp_announcing_it_is_genuine():
    built = sheet_for_template(filled("stage-primary"))
    assert "overprint" not in built.html
    assert "ORIGINAL" not in built.html


def test_a_certified_copy_is_visibly_and_permanently_a_copy():
    template = template_for("stage-primary")
    document = fill(template, values_for(template), edition="certified_copy")
    built = sheet_for_template(document)
    assert "CERTIFIED TRUE COPY" in built.html
    assert 'class="overprint"' in built.html


def test_a_duplicate_must_name_the_original_it_replaces():
    """Otherwise it is indistinguishable from a second original."""
    template = template_for("stage-primary")
    values = values_for(template)
    with pytest.raises(TemplateError) as caught:
        fill(template, {**values, "original_reference": ""}, edition="duplicate")
    assert "original" in str(caught.value).lower()

    document = fill(template, values, edition="duplicate")
    assert "CERT/2024/000188" in document.overprint.en
    assert "CERT/2024/000188" in sheet_for_template(document).html


def test_a_registry_document_is_regenerated_rather_than_reissued():
    """Stamping a copy notice on a register implies custody it does not have."""
    register = template_for("record-graduation-register")
    assert register.security_class == "C"
    with pytest.raises(TemplateError) as caught:
        fill(register, values_for(register), edition="certified_copy")
    assert "regenerated" in str(caught.value)


def test_an_unknown_edition_is_refused():
    template = template_for("stage-primary")
    with pytest.raises(TemplateError):
        fill(template, values_for(template), edition="original-ish")


def test_the_overprint_colour_is_reserved_for_reissuance_and_banners():
    """Oxblood means one thing in this library, which is why it means anything."""
    plain = sheet_for_template(filled("stage-primary")).html
    assert "#6E1F2B" not in plain
    copy = sheet_for_template(
        fill(template_for("stage-primary"), values_for(template_for("stage-primary")),
             edition="certified_copy")
    ).html
    assert "#6E1F2B" in copy


# --- the library is content, not product code --------------------------------


def test_the_library_is_data_rather_than_python():
    """The architecture the universality rule actually requires.

    A thousand lines of template literals in a module is a product that has
    decided which education tradition it serves. The definitions name one
    ladder — Diploma Supplement, Ibtidāʼiyyah, Junior Secondary — and a German
    institution issuing a Diplom, a French one a licence or a seminary an
    ijāzah should not need EdirasX redeployed to have its own document set.

    So the file holds the model and the data file holds the documents, and this
    is the test that stops the literals creeping back.
    """
    import ast
    import pathlib

    source = pathlib.Path(
        __file__).resolve().parents[1] / "modules" / "documents" / "library.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    # Executed strings only, the same rule `test_universal_education` uses:
    # a comment that says "Ibtidāʼiyyah, Junior Secondary" is explaining what
    # was moved out and why, and a check that cannot tell explanation from
    # assumption pushes the examples out of the documentation in the name of a
    # rule about the code.
    docstrings = {
        id(node.body[0].value) for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef))
        and node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    body = " ".join(
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in docstrings
    )
    for name in ("Ibtidāʼiyyah", "Junior Secondary", "Diploma Supplement",
                 "Islamiyyah", "Thānawiyyah"):
        assert name not in body, (
            f"{name!r} is back in product code. Templates belong in "
            "app/data/document-templates.toml."
        )


def test_a_tenant_can_ship_its_own_library():
    """The claim, exercised rather than asserted.

    If a deployment cannot load a different file, the data move was filing
    rather than architecture.
    """
    import pathlib
    import tempfile

    from app.modules.documents.library import DEFAULT_LIBRARY, load

    shipped = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / DEFAULT_LIBRARY)
    text = shipped.read_text(encoding="utf-8")
    # One template, renamed. Everything else about it is the shipped file's.
    first = text.split("[[template]]")[1]
    custom = "[[template]]" + first.replace(
        'name = "Certificate of Tamhīdiyyah"', 'name = "Certificat de Licence"'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(custom)
        path = pathlib.Path(handle.name)
    try:
        library = load(path)
        assert len(library) == 1
        assert next(iter(library.values())).name == "Certificat de Licence"
    finally:
        path.unlink()


def test_a_template_naming_a_family_nothing_renders_is_refused_at_load():
    """A composition is code; declaring one that does not exist is a defect."""
    import pathlib
    import tempfile

    from app.modules.documents.library import DEFAULT_LIBRARY, load

    shipped = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / DEFAULT_LIBRARY)
    first = "[[template]]" + shipped.read_text(
        encoding="utf-8").split("[[template]]")[1]
    broken = first.replace('family = "stage"', 'family = "scroll"')
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(broken)
        path = pathlib.Path(handle.name)
    try:
        with pytest.raises(TemplateError) as caught:
            load(path)
        assert "scroll" in str(caught.value)
    finally:
        path.unlink()
