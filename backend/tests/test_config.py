from app.config import Settings


def test_production_rejects_default_secret():
    settings = Settings(app_env="production", database_url="postgresql+psycopg://user:pass@db:5432/savj")
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        assert "JWT_SECRET" in str(exc)
    else:
        raise AssertionError("Weak production secret should be rejected")


def test_production_rejects_sqlite_and_wildcard_cors():
    strong_secret = "a-unique-production-secret-value-with-more-than-32-chars"
    sqlite_settings = Settings(app_env="production", jwt_secret=strong_secret, cors_origins="https://savj.example")
    try:
        sqlite_settings.validate_runtime()
    except RuntimeError as exc:
        assert "SQLite" in str(exc)
    else:
        raise AssertionError("SQLite should be rejected in production")

    wildcard_settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://user:pass@db:5432/savj",
        jwt_secret=strong_secret,
        cors_origins="*",
    )
    try:
        wildcard_settings.validate_runtime()
    except RuntimeError as exc:
        assert "CORS_ORIGINS" in str(exc)
    else:
        raise AssertionError("Wildcard CORS should be rejected in production")


def test_production_accepts_explicit_secure_configuration():
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://user:pass@db:5432/savj",
        jwt_secret="a-unique-production-secret-value-with-more-than-32-chars",
        access_token_expire_minutes=60,
        cors_origins="https://savj.example,https://www.savj.example",
    )
    assert settings.validate_runtime() is settings
    assert settings.cors_origin_list == ["https://savj.example", "https://www.savj.example"]


def test_token_lifetime_must_be_bounded():
    settings = Settings(access_token_expire_minutes=0)
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        assert "ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc)
    else:
        raise AssertionError("Invalid token lifetime should be rejected")
