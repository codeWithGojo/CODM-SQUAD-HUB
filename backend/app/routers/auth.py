from __future__ import annotations

import random
import string

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token, hash_otp, verify_otp_hash
from app.core.time import as_utc, utcnow
from app.models.user import OTPCode, Region, User
from app.schemas.auth import CompleteSignupIn, MeOut, OTPRequestOut, RequestOTPIn, TokenOut, VerifyOTPIn
from app.services.anti_abuse import record_security_event
from app.services.sms import send_otp_sms

router = APIRouter(prefix="/auth", tags=["auth"])
signup_bearer = HTTPBearer(auto_error=True)


def _generate_code(length: int) -> str:
    return "".join(random.SystemRandom().choices(string.digits, k=length))


@router.post("/request-otp", response_model=OTPRequestOut, status_code=status.HTTP_202_ACCEPTED)
def request_otp(payload: RequestOTPIn, request: Request, db: Session = Depends(get_db)):
    latest = (
        db.query(OTPCode)
        .filter(OTPCode.phone == payload.phone, OTPCode.used.is_(False))
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    if latest:
        age = (utcnow() - as_utc(latest.created_at)).total_seconds()
        if age < settings.otp_min_request_interval_seconds:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Wait {int(settings.otp_min_request_interval_seconds - age) + 1}s before requesting another code.",
            )

    db.query(OTPCode).filter(OTPCode.phone == payload.phone, OTPCode.used.is_(False)).update({"used": True})
    code = _generate_code(settings.otp_length)
    otp = OTPCode(
        phone=payload.phone,
        code_hash=hash_otp(payload.phone, code),
        expires_at=OTPCode.new_expiry(settings.otp_expire_minutes),
    )
    db.add(otp)
    record_security_event(db, request=request, event_type="otp_requested", phone=payload.phone)
    db.commit()

    if not send_otp_sms(payload.phone, code):
        otp.used = True
        record_security_event(db, request=request, event_type="otp_delivery_failed", phone=payload.phone)
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OTP delivery is not configured.")
    return OTPRequestOut(
        expires_in_seconds=settings.otp_expire_minutes * 60,
        dev_code=code if settings.expose_dev_otp and not settings.is_production else None,
    )


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: VerifyOTPIn, request: Request, db: Session = Depends(get_db)):
    otp = (
        db.query(OTPCode)
        .filter(OTPCode.phone == payload.phone, OTPCode.used.is_(False))
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    if not otp or as_utc(otp.expires_at) < utcnow():
        record_security_event(
            db, request=request, event_type="otp_failed", phone=payload.phone, risk_score=15, details="missing_or_expired"
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code.")

    otp.attempts += 1
    if otp.attempts > settings.otp_max_attempts:
        otp.used = True
        record_security_event(
            db, request=request, event_type="otp_locked", phone=payload.phone, risk_score=50, details="too_many_attempts"
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Request a new code.")

    if not verify_otp_hash(payload.phone, payload.code, otp.code_hash):
        record_security_event(db, request=request, event_type="otp_failed", phone=payload.phone, risk_score=20)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code.")

    otp.used = True
    user = db.query(User).filter(User.phone == payload.phone).first()
    if user:
        record_security_event(db, request=request, event_type="login", user=user, phone=payload.phone)
        db.commit()
        return TokenOut(access_token=create_access_token(str(user.id)), is_new_user=False)

    record_security_event(db, request=request, event_type="phone_verified", phone=payload.phone)
    db.commit()
    return TokenOut(
        access_token=create_access_token(
            f"pending:{payload.phone}", token_type="signup", expires_minutes=settings.signup_token_expire_minutes
        ),
        is_new_user=True,
    )


@router.post("/complete-signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def complete_signup(
    payload: CompleteSignupIn,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(signup_bearer),
    db: Session = Depends(get_db),
):
    token = decode_token(credentials.credentials, expected_type="signup")
    if not token or token.get("sub") != f"pending:{payload.phone}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="A valid verified-phone signup token is required.")
    if db.query(User.id).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this phone.")
    if db.query(User.id).filter(User.gamertag == payload.gamertag).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Gamertag already taken.")
    if payload.email and db.query(User.id).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use.")
    if not db.get(Region, payload.region_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown region_id.")

    user = User(
        phone=payload.phone,
        gamertag=payload.gamertag.strip(),
        email=payload.email.lower().strip() if payload.email else None,
        region_id=payload.region_id,
        preferred_mode=payload.preferred_mode,
        is_adult=payload.is_adult,
        parental_consent_confirmed=payload.parental_consent_confirmed,
        is_platform_admin=payload.phone in settings.admin_phone_set,
    )
    db.add(user)
    db.flush()
    record_security_event(db, request=request, event_type="signup", user=user, phone=payload.phone)
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id)), is_new_user=False)


@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
