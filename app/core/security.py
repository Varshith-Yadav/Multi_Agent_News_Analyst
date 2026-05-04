import base64
import hashlib
import hmac
import json
import secrets
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - optional dependency fallback
    Fernet = None
    InvalidToken = Exception


class TokenData(BaseModel):
    sub: str
    roles: list[str]
    exp: int
    iat: int


_runtime_users: dict[str, dict[str, Any]] = {}
_users_lock = threading.Lock()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def _sign(message: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def create_access_token(subject: str, roles: list[str], expires_minutes: int | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = expires_minutes or settings.auth_token_expire_minutes
    exp = int((now + timedelta(minutes=ttl)).timestamp())

    header = {"alg": settings.auth_algorithm, "typ": "JWT"}
    payload = {
        "sub": subject,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": exp,
        "jti": secrets.token_hex(8),
    }

    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    signature_part = _sign(signing_input, settings.auth_secret_key)
    return f"{header_part}.{payload_part}.{signature_part}"


def decode_access_token(token: str) -> TokenData:
    settings = get_settings()

    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format.",
        ) from exc

    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    expected_signature = _sign(signing_input, settings.auth_secret_key)
    if not hmac.compare_digest(expected_signature, signature_part):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
        )

    try:
        payload_raw = _b64url_decode(payload_part)
        payload = json.loads(payload_raw.decode("utf-8"))
        token_data = TokenData.model_validate(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
        ) from exc

    now_ts = int(datetime.now(UTC).timestamp())
    if token_data.exp < now_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
        )

    return token_data


def authenticate_user(username: str, password: str) -> tuple[str, list[str]] | None:
    settings = get_settings()
    normalized_username = username.strip().lower()
    users = {key.strip().lower(): value for key, value in settings.seed_users().items()}
    with _users_lock:
        users.update(_runtime_users)
    user_record = users.get(normalized_username)
    if not user_record:
        return None

    expected_password = str(user_record.get("password", ""))
    if not secrets.compare_digest(expected_password, password):
        return None

    roles = user_record.get("roles", ["viewer"])
    return normalized_username, [str(role) for role in roles]


def register_user(username: str, password: str) -> tuple[str, list[str]]:
    normalized_username = username.strip().lower()
    if len(normalized_username) < 3 or len(normalized_username) > 40:
        raise ValueError("Username must be between 3 and 40 characters.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    settings = get_settings()
    seeded_users = {key.strip().lower() for key in settings.seed_users().keys()}
    with _users_lock:
        if normalized_username in seeded_users or normalized_username in _runtime_users:
            raise ValueError("Username already exists.")

        roles = ["analyst", "viewer"]
        _runtime_users[normalized_username] = {"password": password, "roles": roles}

    return normalized_username, roles


def _build_fernet():
    settings = get_settings()
    raw_key = settings.encryption_key
    if not raw_key or Fernet is None:
        return None

    key_material = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_material))


def encrypt_json(payload: dict[str, Any]) -> str:
    settings = get_settings()
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    fernet = _build_fernet()
    if fernet is None:
        if settings.enforce_encryption:
            raise RuntimeError("Encryption is enforced, but encryption key/provider is unavailable.")
        return serialized

    token = fernet.encrypt(serialized.encode("utf-8"))
    return f"enc:{token.decode('utf-8')}"


def decrypt_json(payload: str) -> dict[str, Any]:
    if not payload:
        return {}

    if not payload.startswith("enc:"):
        return json.loads(payload)

    encrypted = payload.removeprefix("enc:")
    fernet = _build_fernet()
    if fernet is None:
        raise RuntimeError("Encrypted payload exists, but encryption key/provider is unavailable.")

    try:
        plaintext = fernet.decrypt(encrypted.encode("utf-8"))
    except InvalidToken as exc:
        raise RuntimeError("Unable to decrypt payload with configured encryption key.") from exc

    return json.loads(plaintext.decode("utf-8"))
