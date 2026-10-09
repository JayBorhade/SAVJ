import base64, hashlib, hmac, json, secrets, time
from fastapi import HTTPException, status
from .config import get_settings

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return "pbkdf2_sha256$310000$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256": return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def create_access_token(user_id: int) -> tuple[str, int]:
    settings = get_settings()
    expires = settings.access_token_expire_minutes * 60
    now = int(time.time())
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",",":")).encode())
    payload = _b64(json.dumps({"sub":str(user_id),"iat":now,"exp":now+expires}, separators=(",",":")).encode())
    unsigned = header + "." + payload
    signature = _b64(hmac.new(settings.jwt_secret.encode(), unsigned.encode(), hashlib.sha256).digest())
    return unsigned + "." + signature, expires

def decode_access_token(token: str) -> int:
    settings = get_settings()
    try:
        header, payload, signature = token.split(".")
        expected = _b64(hmac.new(settings.jwt_secret.encode(), (header+"."+payload).encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data.get("exp", 0) <= int(time.time()) or data.get("sub") is None: raise ValueError()
        return int(data["sub"])
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token.") from None
