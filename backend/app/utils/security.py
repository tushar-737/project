"""Security helpers: password hashing and stateless access tokens.

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib). Tokens are compact
HMAC-signed payloads (alg = HS256-style) with an expiry timestamp.

Production notes: swap in bcrypt/argon2 and a real JWT library when moving
beyond the prototype - the interfaces used by the API layer stay the same.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from ..config import SECRET_KEY, TOKEN_TTL_HOURS

_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, hash_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(user_id: int, role: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(
        json.dumps(
            {"uid": user_id, "role": role, "exp": int(time.time()) + TOKEN_TTL_HOURS * 3600}
        ).encode()
    )
    signature = _b64url(hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> dict | None:
    try:
        header, payload, signature = token.split(".")
        expected = hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_decode(signature), expected):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except (ValueError, json.JSONDecodeError):
        return None
