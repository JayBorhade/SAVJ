from urllib.parse import urlsplit
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./savj.db"
    jwt_secret: str = "local-development-secret-change-before-deploy-000000"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True
    public_app_url: str | None = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_runtime(self) -> "Settings":
        if not 5 <= self.access_token_expire_minutes <= 1440:
            raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 5 and 1440.")
        if not 1 <= self.smtp_port <= 65535:
            raise RuntimeError("SMTP_PORT must be between 1 and 65535.")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise RuntimeError("SMTP_USERNAME and SMTP_PASSWORD must be set together.")
        if self.app_env.lower() in {"production", "prod"}:
            secret = self.jwt_secret.strip()
            weak_prefixes = ("local-development", "change_me", "changeme", "your-secret", "secret", "placeholder", "example")
            if len(secret) < 32 or secret != self.jwt_secret or secret.lower().startswith(weak_prefixes):
                raise RuntimeError("Production requires a unique, non-placeholder JWT_SECRET of at least 32 characters.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Production must use PostgreSQL or another managed database, not SQLite.")
            if not self.smtp_host or not self.smtp_from or not self.public_app_url:
                raise RuntimeError("Production requires SMTP_HOST, SMTP_FROM, and PUBLIC_APP_URL for email verification and account recovery.")
            public_url = urlsplit(self.public_app_url)
            if public_url.scheme != "https" or not public_url.hostname or public_url.username or public_url.password or public_url.query or public_url.fragment:
                raise RuntimeError("PUBLIC_APP_URL must be an HTTPS URL without credentials, query, or fragment.")
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
