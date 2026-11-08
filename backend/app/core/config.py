from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FashionStore API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    reservation_expiration_hours: int = 24
    frontend_url: str = "http://localhost:4200"
    media_dir: str = "media"
    seed_admin_email: str = "admin@fashionstore.local"
    seed_admin_password: str = ""
    sandbox_payment_webhook_secret: str = "sandbox-webhook-secret"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_vton_model: str = "gemini-3.1-flash-lite-image"
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_currency: str = "bob"
    brevo_api_key: str | None = None
    brevo_sender_email: str | None = None
    brevo_sender_name: str | None = None
    email_worker_batch_size: int = 20

    # The shared Docker env file also contains infrastructure variables that
    # are not application settings. Keep those variables available to the
    # containers without making API startup fail on local test runs.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
