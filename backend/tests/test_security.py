import base64
import json
import time

import pytest
from fastapi import HTTPException

from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_uses_unique_salts_and_verifies():
    first = hash_password("correct-horse-battery")
    second = hash_password("correct-horse-battery")
    assert first != second
    assert verify_password("correct-horse-battery", first)
    assert not verify_password("wrong-password", first)


def test_password_hash_rejects_unsupported_or_extreme_work_factor():
    assert not verify_password("password", "pbkdf2_sha256$999999999$YWJj$YWJj")
    assert not verify_password("password", "unknown$310000$YWJj$YWJj")
    assert not verify_password("password", "not-a-hash")


def test_access_token_round_trip_and_expiry():
    token, expires_in = create_access_token(42)
    assert expires_in > 0
    assert decode_access_token(token) == 42


@pytest.mark.parametrize("token", [
    "",
    "one.two",
    "a.b.c",
    "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiI0MiIsImlhdCI6MSwiZXhwIjo5OTk5OTk5OTk5fQ.",
    "x" * 9000,
])
def test_access_token_rejects_malformed_tokens(token):
    with pytest.raises(HTTPException) as exc:
        decode_access_token(token)
    assert exc.value.status_code == 401


def test_access_token_rejects_modified_signature():
    token, _ = create_access_token(42)
    parts = token.split(".")
    parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
    with pytest.raises(HTTPException):
        decode_access_token(".".join(parts))


def test_access_token_rejects_wrong_algorithm_even_with_valid_signature(monkeypatch):
    from app import security

    settings = security.get_settings()
    header = security._b64(json.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":")).encode())
    now = int(time.time())
    payload = security._b64(json.dumps({"sub": "42", "iat": now, "exp": now + 60}, separators=(",", ":")).encode())
    unsigned = header + "." + payload
    signature = security._b64(security.hmac.new(settings.jwt_secret.encode(), unsigned.encode(), security.hashlib.sha256).digest())
    with pytest.raises(HTTPException):
        decode_access_token(unsigned + "." + signature)


def test_api_responses_include_security_headers():
    from fastapi.testclient import TestClient
    from app.main import app

    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
