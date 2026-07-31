"""
App-wide settings, loaded from environment variables.
Copy .env.example to .env and fill in real values before running.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://user:password@localhost:5432/codm_squad_hub"

    # --- Auth / JWT ---
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- OTP ---
    otp_expire_minutes: int = 10
    otp_length: int = 6

    # --- SMS provider (Termii / Africa's Talking style) ---
    sms_api_key: str = ""
    sms_sender_id: str = "SquadHub"

    # --- Push notifications (FCM) ---
    firebase_credentials_path: str = "./firebase-service-account.json"

    # --- AI ---
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
