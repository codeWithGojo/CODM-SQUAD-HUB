from pydantic import BaseModel, Field, field_validator
import re


class RequestOTPIn(BaseModel):
    phone: str = Field(..., examples=["+2348012345678"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+\d{10,15}$", v):
            raise ValueError("Phone must be in E.164 format, e.g. +2348012345678")
        return v


class VerifyOTPIn(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=8)


class CompleteSignupIn(BaseModel):
    phone: str
    gamertag: str = Field(..., min_length=3, max_length=50)
    region_id: str
    # Self-declared — see User.is_adult / parental_consent_confirmed.
    is_adult: bool
    parental_consent_confirmed: bool = False

    @field_validator("parental_consent_confirmed")
    @classmethod
    def require_consent_if_minor(cls, v: bool, info) -> bool:
        is_adult = info.data.get("is_adult")
        if is_adult is False and not v:
            raise ValueError(
                "Parental consent must be confirmed for players under 18 "
                "before they can use transfer-market / real-money features."
            )
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
