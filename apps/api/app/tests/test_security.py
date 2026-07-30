from app.core.security import (
    TokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
import uuid

import pytest


def test_hash_and_verify_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_password_over_72_bytes_does_not_crash():
    # bcrypt's hard limit is 72 bytes; StromeX truncates rather than crashing
    # or (worse) silently accepting only part of the password without saying so
    # anywhere. This guards the actual production incident hit during MVP build.
    long_password = "x" * 200
    hashed = hash_password(long_password)
    assert verify_password("x" * 200, hashed)
    assert verify_password("x" * 72, hashed)  # truncation point is deterministic


def test_access_and_refresh_tokens_round_trip():
    user_id = uuid.uuid4()
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    assert decode_token(access, TokenType.ACCESS) == user_id
    assert decode_token(refresh, TokenType.REFRESH) == user_id


def test_access_token_rejected_as_refresh_token():
    user_id = uuid.uuid4()
    access = create_access_token(user_id)
    with pytest.raises(TokenError):
        decode_token(access, TokenType.REFRESH)


def test_garbage_token_is_rejected():
    with pytest.raises(TokenError):
        decode_token("not-a-real-token", TokenType.ACCESS)
