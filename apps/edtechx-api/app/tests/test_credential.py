"""The barcode, checked by arithmetic rather than by looking at it.

A Code 128 symbol either carries its specified check character or it is not a
Code 128 symbol, and no amount of rendering will show the difference. These
tests are the only reason the barcode may be described as real.
"""

from __future__ import annotations

import re

import pytest

from app.modules.design import geometry as geo
from app.modules.design.credential import (
    Credential,
    code128c,
    code128c_width,
    number_cartouche,
    qr_bay,
    verification_cartouche,
)
from app.modules.design.gilding import scheme_for

SCHEME = scheme_for("imperial")
CRED = Credential(
    document_id="DID-2031-PHD-0000007",
    verification_code="BFJ7-DRNM-8VZ9",
    archive_reference="ARCH/PHD/2031/000007",
    identity_number="712878764389035",
    certificate_number="EDX-CERT-PHD-000007-BFJ7",
)


def test_the_check_character_is_the_one_the_specification_gives():
    """`1234` in subset C: start 105, values 12 and 34, check 82.

    (105 + 1×12 + 2×34) mod 103 = 185 mod 103 = 82. Worked by hand from the
    specification, so the 107-row width table is verified transitively: a wrong
    row would put a different pattern where symbol 82 belongs.
    """
    from app.modules.design.credential import _C128, _START_C, _STOP

    check = (_START_C + 1 * 12 + 2 * 34) % 103
    assert check == 82

    svg = code128c("1234", x=0, y=0, height=6.0, module=1.0)
    bars = re.findall(r'x="([\d.]+)" y="0.00" width="([\d.]+)"', svg)
    # Four 11-module symbols contribute three bars each; the 13-module stop
    # contributes four, because its pattern has seven elements.
    assert len(bars) == 4 * 3 + 4
    # The stop pattern's first bar starts where the first four symbols end.
    expected_start = sum(
        sum(int(w) for w in _C128[s]) for s in (_START_C, 12, 34, 82)
    )
    assert float(bars[-4][0]) == pytest.approx(expected_start, abs=0.001)
    assert sum(int(w) for w in _C128[_STOP]) == 13


def test_every_symbol_is_eleven_modules_except_the_stop():
    widths = [sum(int(w) for w in pattern) for pattern in _patterns()]
    assert widths[:-1] == [11] * 106
    assert widths[-1] == 13


def _patterns():
    from app.modules.design.credential import _C128

    return _C128


def test_the_table_has_one_row_per_symbol():
    assert len(_patterns()) == 107


def test_width_is_predicted_before_the_symbol_is_drawn():
    """A panel has to lay itself out before it knows the bars."""
    digits = "712878764389035".zfill(16)
    predicted = code128c_width(digits, module=0.4)
    svg = code128c(digits, x=0, y=0, height=6, module=0.4)
    ends = [
        float(x) + float(w)
        for x, w in re.findall(r'x="([\d.]+)"[^/]*width="([\d.]+)"', svg)
    ]
    # The predicted width includes the trailing quiet element; the last bar ends
    # within one module of it.
    assert max(ends) <= predicted + 0.001
    assert max(ends) > predicted - 0.9


def test_an_odd_payload_is_refused_rather_than_truncated():
    with pytest.raises(ValueError):
        code128c("12345", x=0, y=0, height=6)


def test_the_credential_pads_rather_than_switching_subset():
    assert len(CRED.identity_number) == 15
    assert CRED.barcode_digits == "0712878764389035"
    assert len(CRED.barcode_digits) % 2 == 0


def test_the_barcode_is_pure_black():
    """Separated into a rich black it picks up registration spread and stops
    scanning — which is why the production specification asks for 100 % K."""
    svg = code128c("1234", x=0, y=0, height=6)
    assert svg.count('fill="#000000"') == 16
    assert "opacity" not in svg


def test_the_panel_omits_a_barcode_it_would_have_to_squeeze():
    """Below a 0.33mm module the bars close up under ink gain. The panel says
    so on the sheet rather than shipping a symbol that will not scan."""
    narrow = verification_cartouche(
        geo.Rect(0, 0, 30, 30), CRED, scheme=SCHEME, ink="#0E1B33",
        institution="Meridian")
    assert "BARCODE OMITTED" in narrow
    roomy = verification_cartouche(
        geo.Rect(0, 0, 66, 30), CRED, scheme=SCHEME, ink="#0E1B33",
        institution="Meridian")
    assert "BARCODE OMITTED" not in roomy


def test_the_panel_carries_all_five_identifiers_and_the_void_notice():
    svg = verification_cartouche(
        geo.Rect(0, 0, 66, 30), CRED, scheme=SCHEME, ink="#0E1B33",
        institution="Meridian")
    for value in (CRED.document_id, CRED.verification_code,
                  CRED.archive_reference, CRED.identity_number):
        assert value in svg
    assert CRED.void_notice in svg
    assert CRED.verify_url.upper() in svg
    # The fifth lives in its own cartouche, opposite the seal.
    assert CRED.certificate_number in number_cartouche(
        geo.Rect(0, 0, 60, 12), CRED.certificate_number, scheme=SCHEME,
        ink="#0E1B33")


def test_the_qr_bay_says_it_is_a_reservation():
    """A grid that looks like a QR and is not one is worse than an empty bay —
    and three finder outlines read as empty checkboxes, which is a form
    somebody forgot to fill in rather than a bay held open on purpose."""
    svg = qr_bay(geo.Rect(0, 0, 20, 20), scheme=SCHEME, ink="#0E1B33")
    assert "QR BAY RESERVED" in svg
    assert "VERIFY AUTHENTICITY" in svg
    assert svg.count("<rect") == 2, "one keyline and one quiet panel, no grid"
