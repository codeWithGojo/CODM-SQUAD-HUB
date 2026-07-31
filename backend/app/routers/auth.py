import random
import string
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User, OTPCode
from app.schemas.auth import RequestOTPIn, VerifyOTPIn, CompleteSignupIn, TokenOut
from app.services.sms import send_otp_sms

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_code(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/request-otp", status_code=status.HTTP_204_NO_CONTENT)
def request_otp(payload: RequestOTPIn, db: Session = Depends(get_db)):
    """
    Step 1 of login/signup: send a one-time code to the given phone number.
    Same endpoint works whether the number is new (signup) or existing
    (login) — we don't leak which, to avoid enumerating registered users.
    """
    code = _generate_code(settings.otp_length)
    otp = OTPCode(
        phone=payload.phone,
        code=code,
        expires_at=OTPCode.new_expiry(settings.otp_expire_minutes),
    )
    db.add(otp)
    db.commit()

    send_otp_sms(payload.phone, code)
    return None


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp(payload: VerifyOTPIn, db: Session = Depends(get_db)):
    """
    Step 2: verify the code. If the phone belongs to an existing user,
    log them straight in. If not, return is_new_user=True so the app
    knows to route to the CompleteSignup screen next.
    """
    otp = (
        db.query(OTPCode)
        .filter(OTPCode.phone == payload.phone, OTPCode.code == payload.code, OTPCode.used == False)  # noqa: E712
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid code.")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired, request a new one.")

    otp.used = True
    db.commit()

    user = db.query(User).filter(User.phone == payload.phone).first()
    if user:
        user.last_active = datetime.utcnow()
        db.commit()
        return TokenOut(access_token=create_access_token(str(user.id)), is_new_user=False)

    # Phone verified but no account yet — issue a short-lived "pre-auth"
    # token scoped to completing signup. Reusing the same token mechanism
    # keeps this simple; a real build might scope this token more tightly.
    return TokenOut(access_token=create_access_token(f"pending:{payload.phone}"), is_new_user=True)


@router.post("/complete-signup", response_model=TokenOut)
def complete_signup(payload: CompleteSignupIn, db: Session = Depends(get_db)):
    """
    Step 3 (new users only): set gamertag, region, and the age/consent
    checkbox required before a minor can touch transfer-market features.
    """
    existing = db.query(User).filter(User.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists for this phone.")

    gamertag_taken = db.query(User).filter(User.gamertag == payload.gamertag).first()
    if gamertag_taken:
        raise HTTPException(status_code=400, detail="Gamertag already taken.")

    try:
        region_uuid = uuid.UUID(payload.region_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid region_id — must be a UUID.")

    user = User(
        phone=payload.phone,
        gamertag=payload.gamertag,
        region_id=region_uuid,
        is_adult=payload.is_adult,
        parental_consent_confirmed=payload.parental_consent_confirmed,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenOut(access_token=create_access_token(str(user.id)), is_new_user=False)
