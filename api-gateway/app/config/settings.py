"""
API Gateway - Configuration Settings with Enhanced Validation
"""
from typing import Optional
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Gateway configuration settings loaded from environment variables.
    All validation rules are enforced on initialization.
    """

    # ==================== JWT Configuration ====================
    jwt_secret_key: str = Field(
        default="default-secret-key-change-in-production",
        description="JWT secret key for token verification"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )

    # ==================== Service URLs ====================
    user_service_url: str = Field(
        default="http://user-service:8000",
        description="User Service endpoint (required)"
    )
    product_service_url: Optional[str] = Field(
        default=None,
        description="Product Service endpoint (optional)"
    )
    order_service_url: Optional[str] = Field(
        default=None,
        description="Order Service endpoint (optional)"
    )
    notification_service_url: Optional[str] = Field(
        default=None,
        description="Notification Service endpoint (optional)"
    )

    # ==================== Gateway Configuration ====================
    gateway_port: int = Field(
        default=3000,
        ge=1024,
        le=65535,
        description="Gateway listening port (1024-65535)"
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds (1-300)"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum retry attempts (0-5)"
    )

    # ==================== Environment ====================
    environment: str = Field(
        default="development",
        description="Application environment (development/staging/production)"
    )
    api_version: str = Field(
        default="v1",
        description="API version"
    )

    # ==================== CORS Configuration ====================
    cors_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated string, will be parsed to list)"
    )

    # ==================== Logging ====================
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR)"
    )
    debug_mode: bool = Field(
        default=True,
        description="Enable debug mode"
    )

    # ==================== Model Configuration ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # ==================== Field Validators ====================

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """
        Validate JWT secret key length based on environment.
        Development: minimum 16 characters
        Production: minimum 32 characters
        """
        # Get environment from values (if available)
        environment = info.data.get('environment', 'development')

        if environment == 'production':
            if len(v) < 32:
                raise ValueError(
                    'JWT secret key must be at least 32 characters in production'
                )
        else:  # development or staging
            if len(v) < 16:
                raise ValueError(
                    'JWT secret key must be at least 16 characters'
                )

        return v

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment is one of: development, staging, production
        """
        allowed = ['development', 'staging', 'production']
        v_lower = v.lower()

        if v_lower not in allowed:
            raise ValueError(
                f'Environment must be one of {allowed}, got: {v}'
            )

        return v_lower

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate log level is one of: DEBUG, INFO, WARNING, ERROR
        """
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        v_upper = v.upper()

        if v_upper not in allowed:
            raise ValueError(
                f'Log level must be one of {allowed}, got: {v}'
            )

        return v_upper

    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """
        Validate CORS origins format (stays as string, parsed via get_cors_origins_list())
        """
        # Just validate format, don't transform yet
        return v

    # ==================== Helper Methods ====================

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'production'

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == 'development'

    def get_cors_origins_list(self) -> list[str]:
        """
        Get CORS origins as list parsed from comma-separated string.
        If empty or "*", returns ["*"].
        """
        v = self.cors_origins

        if not v or v.strip() == "":
            return ["*"]

        if v.strip() == "*":
            return ["*"]

        # Split by comma and strip whitespace
        origins = [origin.strip() for origin in v.split(',')]
        # Filter out empty strings
        origins = [origin for origin in origins if origin]

        return origins if origins else ["*"]


# ==================== Singleton Instance ====================
settings = Settings()
