from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "product-service"
    app_env: str = "development"
    debug: bool = True
    api_version: str = "v1"

    # Database (async PostgreSQL)
    database_url: str  # postgresql+asyncpg://...

    # Connection Pool
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    db_pool_recycle: int = 3600

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
