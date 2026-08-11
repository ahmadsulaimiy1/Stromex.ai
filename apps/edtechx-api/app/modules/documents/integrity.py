"""Tamper-evidence for an issued document, and the number that checks itself.

What this replaces, and why it had to be replaced. An issued EdirasX document
previously carried a plain SHA-256 of its own payload. That detects our own
record changing, which is worth something — and it is *not* tamper-evidence,
because anybody can recompute it. A forger who invents a document computes its
digest with one line of code and presents a document whose checksum matches
perfectly. The field looked like a security feature and was an integrity check
against ourselves.

This module makes it real: an HMAC over a canonical field set, keyed by a secret
the institution's deployment holds. A forger cannot compute it. That change is
the single most valuable thing taken from studying the Sultan Hanafi Royal
Schools credential architecture, along with four ideas that are less obvious and
matter as much:

**A rotated key must not turn genuine documents into forgeries.** A certificate
is permanent. Rotating the signing secret with nothing recorded would make every
document ever issued report "integrity check failed" — the platform publicly
accusing real graduates because an operator did the right thing with a secret.
So each document records the key version that signed it, and verification uses
*that* key.

**A missing key is a deployment gap, not tampering, and the two must never be
reported as the same thing.** If the retired key for a document's era is not
configured in this environment, that is an operator's problem. Saying "this
document may have been altered" because an environment variable is unset would
be a false accusation about somebody's degree.

**A retired key may never sign again.** Fail-closed, and not arguable at 2am.

**The document number checks itself.** The last segment is derived from the HMAC
over the rest of it, so a forger can invent a plausible-looking number and
cannot compute a matching suffix. A number that is merely a counter tells a
verifier nothing until they reach the database; a self-checking number is
refused before the lookup happens.

**An honest boundary, stated once.** None of this makes a *rendered page*
unforgeable. Anybody can draw a picture that looks like a transcript. What this
guarantees is that a document presented as ours either matches a record we
issued or is detectably not one — which is what verification is for, and is the
only thing cryptography can offer here. Watermarks and lattices are deterrents
against casual reproduction and are never claimed as more than that.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Final

__all__ = [
    "RETIRED_KEY_VERSIONS",
    "IntegrityError",
    "Verdict",
    "compute",
    "current_key_version",
    "hash_ip",
    "serial_suffix",
    "verify",
    "verify_serial",
]


class IntegrityError(RuntimeError):
    """The signing configuration will not permit an honest signature."""


#: Key versions that must never sign again, with the reason a maintainer needs.
#: A retired key stays *verifiable* forever — the documents it signed are
#: genuine — but signing with it is refused outright.
RETIRED_KEY_VERSIONS: Final[dict[int, str]] = {}

# The *name* of the variable, not a secret. Ruff flags the assignment on the
# spelling alone; the value it names never appears in this repository.
_SIGNING_SECRET = "EDIRASX_DOCUMENT_HASH_SECRET"  # noqa: S105
_KEY_VERSION = "EDIRASX_DOCUMENT_HASH_KEY_VERSION"
#: Retired keys arrive as `EDIRASX_DOCUMENT_HASH_SECRET_V<n>`, from the
#: environment like any other secret and never from the repository.
_RETIRED_PREFIX = "EDIRASX_DOCUMENT_HASH_SECRET_V"


def _canonical(fields: dict[str, Any]) -> bytes:
    """A stable serialisation, so the same content always hashes identically.

    Sorted keys and no whitespace, and every value coerced to a string. A digest
    that depends on dict ordering or on whether a date arrived as a `date` or as
    its ISO string is a digest that reports tampering when somebody refactors a
    call site.
    """
    ordered = {str(key): ("" if value is None else str(value))
               for key, value in sorted(fields.items())}
    return json.dumps(ordered, sort_keys=True, separators=(",", ":")).encode()


def current_key_version(env: dict[str, str] | None = None) -> int:
    source = env if env is not None else os.environ
    raw = source.get(_KEY_VERSION) or "1"
    try:
        version = int(raw)
    except ValueError:
        raise IntegrityError(
            f"{_KEY_VERSION} must be a positive integer; got {raw!r}."
        ) from None
    if version < 1:
        raise IntegrityError(f"{_KEY_VERSION} must be a positive integer; got {raw!r}.")
    return version


def _signing_key(env: dict[str, str] | None = None) -> tuple[bytes, int]:
    source = env if env is not None else os.environ
    version = current_key_version(source)
    if version in RETIRED_KEY_VERSIONS:
        raise IntegrityError(
            f"{_KEY_VERSION} is {version}, which is retired and must never sign "
            f"another document. {RETIRED_KEY_VERSIONS[version]}"
        )
    secret = source.get(_SIGNING_SECRET)
    if not secret:
        raise IntegrityError(
            f"{_SIGNING_SECRET} is not configured, so a document cannot be given "
            "tamper-evidence. Refusing to issue one with a predictable digest "
            "that would look like a security feature and be none."
        )
    return (secret.encode(), version)


def _verification_key(version: int, env: dict[str, str] | None = None) -> bytes | None:
    """The key that verifies a document signed under `version`, or `None`.

    `None` means *not configured here*, which the caller must report as a
    deployment gap rather than as a failed integrity check.
    """
    source = env if env is not None else os.environ
    if version == current_key_version(source):
        secret = source.get(_SIGNING_SECRET)
    else:
        secret = source.get(f"{_RETIRED_PREFIX}{version}")
    return secret.encode() if secret else None


@dataclass(frozen=True, slots=True)
class Signature:
    digest: str
    key_version: int

    @property
    def short(self) -> str:
        """What is printed on the document — twelve characters, read aloud."""
        return self.digest[:12].upper()


def compute(fields: dict[str, Any], *, env: dict[str, str] | None = None) -> Signature:
    """Sign a document's canonical field set."""
    key, version = _signing_key(env)
    digest = hmac.new(key, _canonical(fields), hashlib.sha256).hexdigest()
    return Signature(digest=digest, key_version=version)


@dataclass(frozen=True, slots=True)
class Verdict:
    """The outcome of an integrity check, and why.

    `reason` carries the whole point. `mismatch` means the record does not match
    its signature and is a real tamper signal. `key_unavailable` means this
    environment has no key for that document's era, which is an operator's
    problem and must never be shown to a member of the public as a failed
    integrity check on somebody's degree.
    """

    ok: bool
    reason: str          # "match" | "mismatch" | "key_unavailable" | "unsigned"
    detail: str = ""

    @property
    def is_deployment_gap(self) -> bool:
        return self.reason == "key_unavailable"

    @property
    def accuses(self) -> bool:
        """Whether this verdict is evidence against the document itself."""
        return self.reason == "mismatch"

    def __bool__(self) -> bool:
        return self.ok


def verify(
    fields: dict[str, Any],
    stored: str,
    *,
    key_version: int = 1,
    env: dict[str, str] | None = None,
) -> Verdict:
    """Recompute the signature under the key that *signed* this document."""
    if not stored:
        return Verdict(False, "unsigned", "This document carries no signature.")
    key = _verification_key(int(key_version or 1), env)
    if key is None:
        return Verdict(
            False,
            "key_unavailable",
            f"No key is configured for signature version {key_version} in this "
            f"environment. Set {_RETIRED_PREFIX}{key_version}. This is a "
            "deployment gap and says nothing about the document.",
        )
    digest = hmac.new(key, _canonical(fields), hashlib.sha256).hexdigest()
    # Constant-time, because the comparison is on a security-relevant value and
    # a timing side-channel here would let a forger tune a digest byte by byte.
    if hmac.compare_digest(digest, str(stored)):
        return Verdict(True, "match")
    return Verdict(False, "mismatch", "This record does not match its signature.")


# --- the number that checks itself ------------------------------------------

#: The alphabet a suffix is drawn from — hex, uppercased, which reads cleanly
#: aloud and cannot be confused with the numeric segments around it.
SUFFIX_LENGTH: Final[int] = 5


def serial_suffix(
    base: str, fields: dict[str, Any], *, env: dict[str, str] | None = None
) -> str:
    """The anti-forgery segment of a document number.

    Derived from the HMAC over the document's canonical fields *including the
    base number itself*, so the suffix belongs to that one number and cannot be
    lifted onto another. A forger can invent `TR/00042`; they cannot compute the
    five characters that make it `TR/00042-9F3A1`, and a verifier can refuse it
    before touching the database.
    """
    signed = compute({**fields, "serial": base}, env=env)
    return signed.digest[:SUFFIX_LENGTH].upper()


def verify_serial(
    number: str,
    fields: dict[str, Any],
    *,
    key_version: int = 1,
    env: dict[str, str] | None = None,
) -> Verdict:
    """Check a document number's own suffix before any lookup.

    Cheap, and it is the check that answers a fabricated number without
    consulting the database at all — which matters, because a verification
    endpoint that queries on every string it is handed is a verification
    endpoint somebody will enumerate.
    """
    base, separator, suffix = str(number or "").rpartition("-")
    if not separator or len(suffix) != SUFFIX_LENGTH:
        return Verdict(False, "unsigned", "That is not a self-checking number.")
    key = _verification_key(int(key_version or 1), env)
    if key is None:
        return Verdict(
            False, "key_unavailable",
            f"No key is configured for signature version {key_version}.",
        )
    expected = hmac.new(
        key, _canonical({**fields, "serial": base}), hashlib.sha256
    ).hexdigest()[:SUFFIX_LENGTH].upper()
    if hmac.compare_digest(expected, suffix.upper()):
        return Verdict(True, "match")
    return Verdict(False, "mismatch", "That document number does not check out.")


def hash_ip(address: str | None) -> str | None:
    """A verifier's address, for the institution's own anomaly review.

    SHA-256 rather than HMAC, deliberately: this value is never compared against
    a secret-keyed input and exists only so an institution can notice the same
    address checking four hundred certificates in an hour. A plain digest is the
    correct and simpler tool, and a raw address is never stored.
    """
    if not address:
        return None
    return hashlib.sha256(str(address).encode()).hexdigest()
