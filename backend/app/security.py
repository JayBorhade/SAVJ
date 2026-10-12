import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import HTTPException, status

from .config import get_settings

_PASSWORD_ITERATIONS = 310_000
_MIN_PASSWORD_ITERATIONS = 100_000
_MAX_PASSWORD_ITERATIONS = 2_000_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return "pbkdf2_sha256$" + str(_PASSWORD_ITERATIONS) + "$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iteration_text, salt_text, expected = encoded.split("$", 3)
        iterations = int(iteration_text)
        if algorithm != "pbkdf2_sha256" or not _MIN_PASSWORD_ITERATIONS <= iterations <= _MAX_PASSWORD_ITERATIONS:
            return False
        salt = base64.b64decode(salt_text + "=" * (-len(salt_text) % 4), altchars=b"-_", validate=True)
        expected_bytes = base64.b64decode(expected + "=" * (-len(expected) % 4), altchars=b"-_", validate=True)
        if len(salt) != 16 or len(expected_bytes) != hashlib.sha256().digest_size:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(digest, expected_bytes)
    except (ValueError, TypeError, UnicodeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode_b64_json(value: str) -> dict:
    raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("JWT segment must be a JSON object")
    return result


def create_access_token(user_id: int) -> tuple[str, int]:
    settings = get_settings()
    expires = settings.access_token_expire_minutes * 60
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user_id), "iat": now, "exp": now + expires}, separators=(",", ":")).encode())
    unsigned = header + "." + payload
    signature = _b64(hmac.new(settings.jwt_secret.encode(), unsigned.encode(), hashlib.sha256).digest())
    return unsigned + "." + signature, expires


def decode_access_token(token: str) -> int:
    settings = get_settings()
    try:
        if not isinstance(token, str) or len(token) > 8192:
            raise ValueError("Invalid token length")
        header_segment, payload_segment, signature = token.split(".")
        header = _decode_b64_json(header_segment)
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("Unsupported JWT header")

        unsigned = header_segment + "." + payload_segment
        expected_signature = _b64(hmac.new(settings.jwt_secret.encode(), unsigned.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        claims = _decode_b64_json(payload_segment)
        now = int(time.time())
        subject = claims.get("sub")
        issued_at = claims.get("iat")
        expires_at = claims.get("exp")
        if not isinstance(subject, str) or not subject.isdecimal() or int(subject) <= 0:
            raise ValueError("Invalid subject")
        if not isinstance(issued_at, int) or isinstance(issued_at, bool) or issued_at > now + 60:
            raise ValueError("Invalid issued-at claim")
        if not isinstance(expires_at, int) or isinstance(expires_at, bool) or expires_at <= now or expires_at <= issued_at:
            raise ValueError("Invalid expiry claim")
        if expires_at - issued_at > settings.access_token_expire_minutes * 60:
            raise ValueError("Token lifetime exceeds configured maximum")
        return int(subject)
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
