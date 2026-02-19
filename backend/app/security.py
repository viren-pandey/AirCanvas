from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional runtime dependency
    bcrypt = None  # type: ignore[assignment]
    BCRYPT_AVAILABLE = False

try:
    from jose import JWTError, jwt

    JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional runtime dependency
    JWTError = Exception  # type: ignore[assignment]
    jwt = None  # type: ignore[assignment]
    JOSE_AVAILABLE = False

from .config import settings


BCRYPT_MAX_PASSWORD_BYTES = 72
PBKDF2_ITERATIONS = 300_000


def _password_to_bytes(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long for bcrypt (max 72 UTF-8 bytes).",
        )
    return password_bytes


def hash_password(password: str) -> str:
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(_password_to_bytes(password), bcrypt.gensalt()).decode("utf-8")
    return _hash_password_pbkdf2(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        return _verify_password_pbkdf2(password, password_hash)

    if not BCRYPT_AVAILABLE:
        return False

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, is_admin: bool) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {
        "sub": subject,
        "is_admin": is_admin,
        "exp": expires_at,
    }
    if JOSE_AVAILABLE:
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    compact_payload = {
        "sub": subject,
        "is_admin": bool(is_admin),
        "exp": int(expires_at.timestamp()),
    }
    payload_bytes = json.dumps(compact_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"local.{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    if JOSE_AVAILABLE:
        try:
            return jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            ) from exc

    return _decode_local_token(token)


def _hash_password_pbkdf2(password: str) -> str:
    salt = os.urandom(16)
    password_bytes = password.encode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, PBKDF2_ITERATIONS)
    return (
        "pbkdf2_sha256$"
        f"{PBKDF2_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii')}"
    )


def _verify_password_pbkdf2(password: str, encoded_hash: str) -> bool:
    try:
        _, rounds_text, salt_text, digest_text = encoded_hash.split("$", 3)
        rounds = int(rounds_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return hmac.compare_digest(candidate, expected_digest)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _decode_local_token(token: str) -> dict:
    try:
        prefix, payload_text, signature_text = token.split(".", 2)
        if prefix != "local":
            raise ValueError("Unsupported token prefix")
        payload_bytes = _b64url_decode(payload_text)
        signature = _b64url_decode(signature_text)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    expected_signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    exp_raw = payload.get("exp")
    try:
        exp_ts = float(exp_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    if datetime.now(timezone.utc).timestamp() > exp_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    return payload
