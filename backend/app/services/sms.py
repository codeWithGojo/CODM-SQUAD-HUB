"""
SMS delivery for OTP codes.

Real Nigerian-market providers worth checking when you're ready to wire
this up for real: Termii, Africa's Talking, or Twilio (more expensive,
less local support). All follow roughly the same "send message to phone"
API shape, so swapping providers later should only mean changing this file.

For now this stub logs the code instead of sending a real SMS, so auth
can be built and tested end-to-end before a provider account exists.
"""
import logging

logger = logging.getLogger("sms")


def send_otp_sms(phone: str, code: str) -> bool:
    # TODO: replace with a real provider call, e.g.:
    #   response = httpx.post("https://api.ng.termii.com/api/sms/send", json={...})
    #   return response.status_code == 200
    logger.info(f"[DEV MODE] Would send OTP {code} to {phone}")
    return True
