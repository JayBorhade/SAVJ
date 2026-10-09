import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./savj.db"
    jwt_secret: str = "local-development-secret-change-before-deploy-000000"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_runtime(self) -> "Settings":
        if not 5 <= self.access_token_expire_minutes <= 1440:
            raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 5 and 1440.")
        if self.app_env.lower() in {"production", "prod"}:
            weak_values = {"change_me", "changeme", "your-secret", "secret"}
            if len(self.jwt_secret) < 32 or self.jwt_secret.startswith("local-development") or self.jwt_secret.lower() in weak_values:
                raise RuntimeError("Production requires a unique JWT_SECRET of at least 32 characters.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Production must use PostgreSQL or another managed database, not SQLite.")
            origins = self.cors_origin_list
            if not origins or "*" in origins:
                raise RuntimeError("Production CORS_ORIGINS must list explicit trusted origins; wildcards are forbidden.")
            if any(origin.endswith("://") or " " in origin for origin in origins):
                raise RuntimeError("CORS_ORIGINS contains an invalid origin.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings().validate_runtime()
