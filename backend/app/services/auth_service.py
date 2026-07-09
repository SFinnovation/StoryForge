"""轻量认证服务。

MVP 使用标准库实现 bearer token，避免新增认证依赖。Token 结构类似
`base64url(payload).signature`，签名使用 HMAC-SHA256。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from backend.app.core.config import settings
from backend.app.core.exceptions import StoryForgeError

PASSWORD_PREFIX = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000
LEGACY_PASSWORD_ITERATIONS = 120_000


@dataclass
class TokenPayload:
    user_id: int
    username: str
    exp: int


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    )
    return f"{PASSWORD_PREFIX}${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def is_password_hash(stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    parts = stored_hash.split("$")
    return len(parts) in (3, 4) and parts[0] == PASSWORD_PREFIX


def is_legacy_plaintext_password(stored_hash: str | None) -> bool:
    return bool(stored_hash) and not is_password_hash(stored_hash)


def verify_legacy_plaintext_password(password: str, stored_hash: str | None) -> bool:
    if not is_legacy_plaintext_password(stored_hash):
        return False
    return hmac.compare_digest(password, stored_hash or "")


def needs_password_rehash(stored_hash: str | None) -> bool:
    if not is_password_hash(stored_hash):
        return True
    parts = (stored_hash or "").split("$")
    if len(parts) == 3:
        return True
    try:
        iterations = int(parts[1])
    except (TypeError, ValueError):
        return True
    return iterations < PASSWORD_ITERATIONS


def verify_password(password: str, stored_hash: str) -> bool:
    parts = stored_hash.split("$")
    if len(parts) == 3:
        prefix, salt, expected = parts
        iterations = LEGACY_PASSWORD_ITERATIONS
    elif len(parts) == 4:
        prefix, iterations_raw, salt, expected = parts
        try:
            iterations = int(iterations_raw)
        except ValueError:
            return False
    else:
        return False

    if prefix != PASSWORD_PREFIX:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), expected)


def create_access_token(*, user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + settings.JWT_EXPIRE_MINUTES * 60,
    }
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> TokenPayload:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise StoryForgeError("invalid token", status_code=401) from exc

    expected = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise StoryForgeError("invalid token", status_code=401)

    try:
        payload = json.loads(_b64decode(encoded_payload))
        exp = int(payload["exp"])
        user_id = int(payload["sub"])
        username = str(payload.get("username") or "")
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise StoryForgeError("invalid token", status_code=401) from exc

    if exp < int(time.time()):
        raise StoryForgeError("token expired", status_code=401)
    return TokenPayload(user_id=user_id, username=username, exp=exp)
