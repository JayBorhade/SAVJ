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
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env.lower() in {"production", "prod"} and (len(settings.jwt_secret) < 32 or settings.jwt_secret.startswith("local-development")):
        raise RuntimeError("Production requires a strong JWT_SECRET of at least 32 characters.")
    return settings
