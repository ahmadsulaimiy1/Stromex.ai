#!/usr/bin/env python3
"""Verify SAJJIL's FLAC encoder against an independent decoder (libsndfile).

The Kotlin test `FlacFixtureTest` writes matched `.flac` / `.wav` pairs into
`core-audio/build/flac-fixtures/`. This script decodes both with libsndfile and asserts the
samples are identical. FLAC is lossless, so "identical" means bit-exact — not "close".

Usage:
    ./gradlew :core-audio:test --tests '*FlacFixtureTest*'
    python3 tools/verify-flac.py

Requires: pip install soundfile
"""

import sys
from pathlib import Path

try:
    import numpy as np
    import soundfile as sf
except ImportError:
    sys.exit("This script needs numpy and soundfile: pip install soundfile")

FIXTURES = Path(__file__).resolve().parent.parent / "core-audio" / "build" / "flac-fixtures"


def main() -> int:
    if not FIXTURES.is_dir():
        sys.exit(
            f"No fixtures at {FIXTURES}.\n"
            "Run: ./gradlew :core-audio:test --tests '*FlacFixtureTest*'"
        )

    flac_files = sorted(FIXTURES.glob("*.flac"))
    if not flac_files:
        sys.exit(f"No .flac fixtures found in {FIXTURES}")

    failures = 0
    for flac_path in flac_files:
        wav_path = flac_path.with_suffix(".wav")
        if not wav_path.exists():
            print(f"FAIL {flac_path.name}: no matching .wav reference")
            failures += 1
            continue

        try:
            decoded, decoded_rate = sf.read(flac_path, dtype="int16", always_2d=True)
        except Exception as error:
            print(f"FAIL {flac_path.name}: libsndfile could not decode it — {error}")
            failures += 1
            continue

        reference, reference_rate = sf.read(wav_path, dtype="int16", always_2d=True)

        if decoded_rate != reference_rate:
            print(f"FAIL {flac_path.name}: sample rate {decoded_rate} != {reference_rate}")
            failures += 1
            continue

        if decoded.shape != reference.shape:
            print(
                f"FAIL {flac_path.name}: shape {decoded.shape} != reference {reference.shape}"
            )
            failures += 1
            continue

        differences = np.count_nonzero(decoded != reference)
        if differences:
            worst = int(np.max(np.abs(decoded.astype(np.int32) - reference.astype(np.int32))))
            print(
                f"FAIL {flac_path.name}: {differences} of {decoded.size} samples differ "
                f"(worst {worst}) — FLAC must be bit-exact"
            )
            failures += 1
            continue

        ratio = flac_path.stat().st_size / max(1, wav_path.stat().st_size)
        print(
            f"OK   {flac_path.name}: {decoded.shape[0]} frames x {decoded.shape[1]}ch "
            f"bit-exact, {ratio:.0%} of WAV size"
        )

    print()
    if failures:
        print(f"{failures} of {len(flac_files)} fixtures failed")
        return 1
    print(f"All {len(flac_files)} fixtures decoded bit-exactly by libsndfile")
    return 0


if __name__ == "__main__":
    sys.exit(main())
