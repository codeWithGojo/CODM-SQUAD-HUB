"""JWT, OTP hashing, and privacy-preserving anti-abuse helpers."""

from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from jose import JWTError, jwt

from app.core.config import settings
from app.core.time import utcnow


def create_access_token(subject: str, *, token_type: str = "access", expires_minutes: int | None = None) -> str:
    lifetime = expires_minutes or settings.access_token_expire_minutes
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": utcnow(),
        "exp": utcnow() + timedelta(minutes=lifetime),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, expected_type: str | None = None) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if expected_type and payload.get("type") != expected_type:
        return None
    return payload


def decode_access_token(token: str) -> str | None:
    payload = decode_token(token, expected_type="access")
    return str(payload.get("sub")) if payload and payload.get("sub") else None


def hash_otp(phone: str, code: str) -> str:
    message = f"{phone}:{code}".encode()
    return hmac.new(settings.jwt_secret_key.encode(), message, hashlib.sha256).hexdigest()


def verify_otp_hash(phone: str, code: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(phone, code), expected_hash)


def privacy_hash(value: str | None) -> str | None:
    if not value:
        return None
    return hmac.new(settings.anti_abuse_secret.encode(), value.strip().encode(), hashlib.sha256).hexdigest()
