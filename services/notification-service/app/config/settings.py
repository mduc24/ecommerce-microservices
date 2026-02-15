from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "notification-service"
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

    # RabbitMQ
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "admin"
    rabbitmq_pass: str = "admin123"
    rabbitmq_exchange: str = "ecommerce_events"
    rabbitmq_queue: str = "notification_queue"

    # SMTP (MailHog)
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_from: str = "noreply@ecommerce.com"

    # Server
    host: str = "0.0.0.0"
    port: int = 8004

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
