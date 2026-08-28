"""Environment-backed application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CoDM Squad Hub API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+pysqlite:///./codm_squad_hub.db"
    auto_create_tables: bool = True
    cors_origins: str = "http://localhost:8081,http://localhost:19006"

    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    signup_token_expire_minutes: int = 15

    otp_expire_minutes: int = 10
    otp_length: int = 6
    otp_max_attempts: int = 5
    otp_min_request_interval_seconds: int = 60
    expose_dev_otp: bool = False

    sms_api_key: str = ""
    sms_provider: str = "termii"
    sms_base_url: str = "https://api.ng.termii.com"
    sms_sender_id: str = "SquadHub"
    firebase_credentials_path: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ai_allow_rules_fallback: bool = True

    paystack_secret_key: str = ""
    paystack_public_key: str = ""
    paystack_callback_url: str = ""

    anti_abuse_secret: str = "CHANGE_ME_ANTI_ABUSE"
    admin_phone_numbers: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def admin_phone_set(self) -> set[str]:
        return {value.strip() for value in self.admin_phone_numbers.split(",") if value.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
