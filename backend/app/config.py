from urllib.parse import urlsplit
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
            secret = self.jwt_secret.strip()
            weak_prefixes = ("local-development", "change_me", "changeme", "your-secret", "secret", "placeholder", "example")
            if len(secret) < 32 or secret != self.jwt_secret or secret.lower().startswith(weak_prefixes):
                raise RuntimeError("Production requires a unique, non-placeholder JWT_SECRET of at least 32 characters.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Production must use PostgreSQL or another managed database, not SQLite.")
            origins = self.cors_origin_list
            if not origins or "*" in origins:
                raise RuntimeError("Production CORS_ORIGINS must list explicit trusted origins; wildcards are forbidden.")
            for origin in origins:
                parsed = urlsplit(origin)
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or parsed.path not in {"", "/"}
                    or parsed.query
                    or parsed.fragment
                    or parsed.username
                    or parsed.password
                    or " " in origin
                ):
                    raise RuntimeError("Production CORS_ORIGINS must contain HTTPS origins without paths, credentials, queries, or fragments.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings().validate_runtime()
