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
    frontend_url: str = "http://localhost:4200"
    seed_admin_email: str = "admin@fashionstore.local"
    seed_admin_password: str = ""

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
