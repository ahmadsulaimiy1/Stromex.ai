"""Application-level encryption for the sensitive set.

Disk encryption protects a stolen disk. It does nothing about a leaked backup,
an over-broad database grant, or a SQL injection that reads a column — which is
what actually happens. MFA secrets, AI provider credentials, and safeguarding
notes are therefore encrypted by the application before they reach a column
(EDIRASX_SECURITY.md §4).

AES-256-GCM, so a tampered ciphertext fails to decrypt rather than silently
yielding altered plaintext. Keys are derived per purpose, so a key that leaks
from one context cannot open another.
"""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

NONCE_BYTES = 12
VERSION = b"\x01"


class DecryptionFailed(ValueError):
    """Ciphertext could not be decrypted, or was tampered with."""


def _key_for(purpose: str) -> bytes:
    """Derive a 256-bit key bound to a purpose string.

    Separate keys per purpose mean the MFA secret key cannot open an AI
    credential. HKDF's `info` parameter is exactly this: domain separation from
    one root secret, with no extra key material to manage.
    """
    settings = get_settings()
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"edirasx.kdf.v1",
        info=purpose.encode(),
    ).derive(settings.secret_key.encode())


def encrypt(plaintext: str, *, purpose: str) -> str:
    """Encrypt to a self-describing, URL-safe string.

    The purpose is bound as additional authenticated data, so a ciphertext
    moved from one column to another fails to decrypt instead of quietly
    working.
    """
    aes = AESGCM(_key_for(purpose))
    nonce = os.urandom(NONCE_BYTES)
    sealed = aes.encrypt(nonce, plaintext.encode(), purpose.encode())
    return base64.urlsafe_b64encode(VERSION + nonce + sealed).decode()


def decrypt(token: str, *, purpose: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode())
    except Exception as exc:
        raise DecryptionFailed("not a valid ciphertext") from exc
    if not raw.startswith(VERSION) or len(raw) < 1 + NONCE_BYTES + 16:
        raise DecryptionFailed("unrecognised ciphertext format")

    nonce = raw[1 : 1 + NONCE_BYTES]
    sealed = raw[1 + NONCE_BYTES :]
    try:
        return AESGCM(_key_for(purpose)).decrypt(nonce, sealed, purpose.encode()).decode()
    except InvalidTag as exc:
        raise DecryptionFailed("ciphertext failed authentication") from exc


# Purpose labels, not secrets: they are the HKDF `info` string and the AEAD
# additional data, and are safe to read.
MFA_SECRET = "mfa.totp.secret"  # noqa: S105
AI_CREDENTIAL = "ai.provider.credential"
SAFEGUARDING = "people.safeguarding"
