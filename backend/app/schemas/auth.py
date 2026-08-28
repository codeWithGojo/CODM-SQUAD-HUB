from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import Mode


PHONE_PATTERN = re.compile(r"^\+\d{10,15}$")


class RequestOTPIn(BaseModel):
    phone: str = Field(examples=["+2348012345678"])

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not PHONE_PATTERN.match(value):
            raise ValueError("Phone must use E.164 format, e.g. +2348012345678")
        return value


class OTPRequestOut(BaseModel):
    expires_in_seconds: int
    dev_code: str | None = None


class VerifyOTPIn(RequestOTPIn):
    code: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


class CompleteSignupIn(BaseModel):
    phone: str
    gamertag: str = Field(min_length=3, max_length=50, pattern=r"^[^\s].*[^\s]$|^[^\s]{3}$")
    email: str | None = Field(default=None, max_length=255)
    region_id: uuid.UUID
    preferred_mode: Mode | None = None
    is_adult: bool
    parental_consent_confirmed: bool = False

    @model_validator(mode="after")
    def require_consent_if_minor(self):
        if not self.is_adult and not self.parental_consent_confirmed:
            raise ValueError("Parental consent must be confirmed for players under 18.")
        return self


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool


class MeOut(BaseModel):
    id: uuid.UUID
    shid: str
    phone: str
    email: str | None
    gamertag: str
    preferred_mode: Mode | None
    region_id: uuid.UUID | None
    is_platform_admin: bool
    reputation_score: int

    model_config = {"from_attributes": True}
