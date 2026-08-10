"""TOTP (RFC 6238), implemented rather than imported.

Thirty lines of HMAC is not worth a dependency, and writing it here means the
two decisions that actually matter are visible and testable rather than buried
in a library's defaults:

  * **the drift window**, which trades usability against the size of an
    attacker's guessing surface, and
  * **replay rejection**, which most implementations leave to the caller and
    most callers forget — without it a code observed over a shoulder or
    captured in a proxy log is valid for its whole step.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from urllib.parse import quote

DIGITS = 6
STEP_SECONDS = 30

# One step either side. Two steps (the other common choice) triples the
# guessing surface to buy tolerance for clocks that are already unusual; one
# step covers ordinary phone drift and the seconds a person takes to type.
DRIFT_STEPS = 1

SECRET_BYTES = 20  # 160 bits, the RFC 4226 recommendation


def generate_secret() -> str:
    """A fresh base32 secret, in the form authenticator apps expect."""
    return base64.b32encode(secrets.token_bytes(SECRET_BYTES)).decode().rstrip("=")


def _decode(secret: str) -> bytes:
    padded = secret.strip().replace(" ", "").upper()
    padded += "=" * (-len(padded) % 8)
    return base64.b32decode(padded, casefold=True)


def counter_at(moment: float | None = None) -> int:
    return int((moment if moment is not None else time.time()) // STEP_SECONDS)


def code_for(secret: str, counter: int) -> str:
    digest = hmac.new(_decode(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    (truncated,) = struct.unpack(">I", digest[offset : offset + 4])
    return str((truncated & 0x7FFFFFFF) % (10**DIGITS)).zfill(DIGITS)


@dataclass(frozen=True, slots=True)
class Verification:
    valid: bool
    counter: int | None = None

    def __bool__(self) -> bool:
        return self.valid


def verify(
    secret: str, code: str, *, last_used_counter: int | None = None, moment: float | None = None
) -> Verification:
    """Check a code, rejecting replays of one already used.

    `last_used_counter` is the caller's record of the last counter this account
    accepted. Anything at or below it is refused even when the arithmetic says
    the code is correct — so a code seen once cannot be used again within its
    window, which is the whole point of a *one-time* password.

    Comparison is constant-time. A timing side channel on a six-digit code is a
    small leak, but it is a free one to close.
    """
    cleaned = code.strip().replace(" ", "")
    if len(cleaned) != DIGITS or not cleaned.isdigit():
        return Verification(False)

    current = counter_at(moment)
    for offset in range(-DRIFT_STEPS, DRIFT_STEPS + 1):
        candidate = current + offset
        if last_used_counter is not None and candidate <= last_used_counter:
            continue
        if hmac.compare_digest(code_for(secret, candidate), cleaned):
            return Verification(True, candidate)
    return Verification(False)


def provisioning_uri(secret: str, *, account: str, issuer: str) -> str:
    """The `otpauth://` URI an authenticator app scans."""
    label = quote(f"{issuer}:{account}", safe="")
    return (
        f"otpauth://totp/{label}"
        f"?secret={secret}&issuer={quote(issuer, safe='')}"
        f"&algorithm=SHA1&digits={DIGITS}&period={STEP_SECONDS}"
    )


def generate_recovery_codes(count: int = 10) -> list[str]:
    """Single-use codes for a lost device.

    Formatted in groups because they are read off paper and typed by someone
    who has already had a bad morning.
    """
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(6).upper()
        codes.append(f"{raw[:4]}-{raw[4:8]}-{raw[8:]}")
    return codes
