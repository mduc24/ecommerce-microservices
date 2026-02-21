from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "user-service"
    app_env: str = "development"
    debug: bool = True

    # Database (async PostgreSQL)
    database_url: str  # postgresql+asyncpg://...

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    frontend_url: str = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
