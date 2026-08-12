"""Preparing an uploaded signature: lifting the ink off the paper.

An officer signs a sheet of paper, somebody photographs it with a phone, and
that image has to end up on a certificate looking as though it was written on
the certificate. Between those two things is this file.

**The problem, stated properly.** A photographed signature is dark strokes on a
light field, but the field is not white: it is a photograph of paper, with a
shadow down one side, a colour cast from whatever light was in the room, and
JPEG noise. Dropping that onto an ivory certificate puts a grey rectangle on it.
Every certificate that has one is instantly recognisable.

So the ink is separated from the paper and everything that is not ink becomes
transparent. The method is deliberately simple and deliberately explainable,
because a registrar has to be able to look at the result and agree with it:

1. **Estimate the paper.** The brightest few per cent of pixels are paper by
   definition — a signature covers a small fraction of a page. Sampling the
   border rather than the whole image would fail on a tightly cropped scan, so
   the estimate is a high percentile of the whole.
2. **Measure each pixel's distance below the paper.** Not its absolute
   darkness: a signature photographed on grey card is *lighter* than one
   scanned on white, and an absolute threshold destroys one or the other.
3. **Ramp the alpha across a band**, not a step. A hard threshold leaves a
   jagged one-pixel edge that looks cut out with scissors; a ramp keeps the
   pen's own antialiasing and the stroke stays a stroke.
4. **Recolour to the document's ink.** A blue biro on an ivory certificate set
   in midnight is wrong twice over. The stroke keeps its shape and alpha and
   takes the document's colour, which is what an engraver would do.

**What this does not do, said plainly.** It does not vectorise. The result is a
transparent raster and it is subject to the same resolution arithmetic as any
other supplied bitmap — `signature_resolution_note()` gives the numbers. It does
not repair a signature that was photographed badly; a blurred or blown-out
capture comes out blurred and blown-out, and `assess()` says so before anybody
puts it on a certificate rather than after. And it does not authenticate
anything: this is image processing, and whether the officer holding that pen was
in office on the day is `documents.authority`'s question, not this file's.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

__all__ = [
    "Assessment",
    "assess",
    "signature_resolution_note",
    "strip_background",
]


@dataclass(frozen=True, slots=True)
class Assessment:
    """What the uploaded capture is actually like, before it is used.

    Returned so a studio can refuse a bad capture at upload — while the officer
    is still there and can sign again — rather than after it is on a hundred
    certificates.
    """

    width: int
    height: int
    #: Estimated paper level, 0–255. A very low value means the capture is
    #: underexposed and there is no clean paper to subtract.
    paper: int
    #: Proportion of pixels that are ink. A signature is a few per cent; far
    #: more than that means the crop includes something that is not signature.
    ink_fraction: float
    #: Separation between paper and ink, 0–255. Below about 40 the two are not
    #: distinguishable and any threshold will take paper with the ink.
    contrast: int
    problems: tuple[str, ...] = ()

    @property
    def usable(self) -> bool:
        return not self.problems


def _load(data: bytes):
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover - environment
        raise RuntimeError(
            "Signature preparation needs Pillow. It is declared in "
            "requirements.txt; install it rather than skipping this step, "
            "because the alternative is a grey rectangle on a certificate."
        ) from exc
    return Image.open(io.BytesIO(data)).convert("RGBA")


def _luma_histogram(image) -> list[int]:
    grey = image.convert("L")
    return grey.histogram()


def _percentile(histogram: list[int], fraction: float) -> int:
    total = sum(histogram) or 1
    target = total * fraction
    running = 0
    for level, count in enumerate(histogram):
        running += count
        if running >= target:
            return level
    return 255


def assess(data: bytes) -> Assessment:
    """Look at a capture and say whether it can be used, before it is.

    Every problem is phrased as something the person can *do* — sign again on
    white paper, photograph in better light, crop tighter — because "invalid
    image" tells a registrar nothing they can act on.
    """
    image = _load(data)
    histogram = _luma_histogram(image)
    paper = _percentile(histogram, 0.94)
    ink = _percentile(histogram, 0.02)
    contrast = max(0, paper - ink)
    threshold = paper - max(28, contrast * 0.45)
    dark = sum(histogram[: max(0, int(threshold))])
    fraction = dark / (image.width * image.height or 1)

    problems: list[str] = []
    if image.width < 600:
        problems.append(
            f"The capture is {image.width}px wide. A signature printed 60mm "
            "across needs 710px for 300 DPI — photograph it larger or scan it."
        )
    if paper < 110:
        problems.append(
            "The paper reads dark, so the capture is underexposed. Photograph "
            "it again in brighter, even light."
        )
    if contrast < 40:
        problems.append(
            "The ink and the paper are too close in tone to separate. Sign "
            "again in black or dark blue on white paper."
        )
    if fraction > 0.22:
        problems.append(
            "More than a fifth of the image is dark, so the crop is including "
            "something that is not signature. Crop closer to the strokes."
        )
    if fraction < 0.002:
        problems.append(
            "Almost nothing in the image reads as ink. Check the right file "
            "was uploaded."
        )
    return Assessment(width=image.width, height=image.height, paper=paper,
                      ink_fraction=fraction, contrast=contrast,
                      problems=tuple(problems))


def strip_background(data: bytes, *, ink: str = "#101826",
                     softness: float = 0.45, trim: bool = True) -> bytes:
    """Lift the strokes off the paper and return a transparent PNG.

    `softness` is the width of the alpha ramp as a fraction of the measured
    paper-to-ink separation. At 0 it is a hard threshold and the stroke looks
    cut out with scissors; at 1 the paper starts coming through. The default
    keeps the pen's own antialiasing.

    `trim` crops to the strokes, so a signature photographed in the middle of an
    A4 sheet does not arrive as a mostly-empty image whose real content is a
    twentieth of its stated size — which is how a signature ends up rendering
    at 4mm inside a 60mm box.
    """
    image = _load(data)
    from PIL import Image

    grey = image.convert("L")
    histogram = grey.histogram()
    paper = _percentile(histogram, 0.94)
    floor = _percentile(histogram, 0.02)
    spread = max(24, paper - floor)
    # Fully opaque at `solid`, fully transparent at `paper`. Measuring the ramp
    # from the paper *down* rather than from black *up* is what makes this work
    # on a scan and on a phone photograph of grey card alike.
    #
    # The ramp's *width* is `softness × spread`, so 0 is a hard threshold and
    # 0.95 is nearly the whole tonal range. The first version computed
    # `spread × (1 − softness)`, which inverted the parameter against its own
    # documentation: asking for a hard edge produced the softest possible one.
    span = max(1.0, spread * min(max(softness, 0.0), 0.95))
    solid = paper - span

    alpha = grey.point(
        lambda value: 0 if value >= paper
        else 255 if value <= solid
        else int(255 * (paper - value) / span)
    )
    red, green, blue = (int(ink.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    flat = Image.new("RGBA", image.size, (red, green, blue, 0))
    flat.putalpha(alpha)

    if trim:
        box = flat.getbbox()
        if box:
            pad = max(2, min(flat.width, flat.height) // 100)
            flat = flat.crop((
                max(0, box[0] - pad), max(0, box[1] - pad),
                min(flat.width, box[2] + pad), min(flat.height, box[3] + pad),
            ))

    out = io.BytesIO()
    flat.save(out, format="PNG", optimize=True)
    return out.getvalue()


def signature_resolution_note(width_mm: float, pixels: int) -> str:
    """Whether a prepared signature is big enough for the box it will sit in."""
    needed_300 = round(width_mm / 25.4 * 300)
    needed_600 = round(width_mm / 25.4 * 600)
    verdict = (
        "sufficient for 600 DPI" if pixels >= needed_600
        else "sufficient for 300 DPI" if pixels >= needed_300
        else "TOO SMALL — it will print soft"
    )
    return (
        f"This signature prints {width_mm:.0f}mm wide and is {pixels}px across: "
        f"{verdict}. It needs {needed_300}px for 300 DPI and {needed_600}px "
        "for 600."
    )
