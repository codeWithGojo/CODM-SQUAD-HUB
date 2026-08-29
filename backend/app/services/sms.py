"""OTP delivery adapter. Provider wiring stays server-side."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("codm.sms")


def send_otp_sms(phone: str, code: str) -> bool:
    if not settings.sms_api_key:
        logger.info("OTP delivery simulated for phone ending %s", phone[-4:])
        return True
    if settings.sms_provider.lower() != "termii":
        logger.error("Unsupported SMS provider: %s", settings.sms_provider)
        return False
    try:
        response = httpx.post(
            f"{settings.sms_base_url.rstrip('/')}/api/sms/send",
            json={
                "api_key": settings.sms_api_key,
                "to": phone,
                "from": settings.sms_sender_id,
                "sms": f"Your CoDM Squad Hub verification code is {code}. It expires soon.",
                "type": "plain",
                "channel": "generic",
            },
            timeout=15.0,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        # Never log the message payload, code, phone number, or provider key.
        logger.error("SMS provider request failed: %s", type(exc).__name__)
        return False
