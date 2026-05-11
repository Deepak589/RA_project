from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, decode_token


def test_decode_token_rejects_wrong_issuer() -> None:
    """A token signed with a different issuer must fail decode."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "some-user-id",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": "malicious-issuer",
    }
    bad_token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(ValueError):
        decode_token(bad_token)


def test_decode_token_accepts_correct_issuer() -> None:
    """A token with the correct issuer must decode successfully."""
    token = create_access_token("test-user-id")
    decoded = decode_token(token)
    assert decoded["sub"] == "test-user-id"
    assert decoded["iss"] == settings.jwt_issuer
