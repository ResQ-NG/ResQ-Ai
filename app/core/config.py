"""
Configuration management for application.
Loads and validates environment variables.
"""

import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables."""

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME: Optional[str] = os.getenv("AWS_BUCKET_NAME")

    CACHE_HOST: str = os.getenv("REDIS_HOST", "localhost")
    CACHE_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    CACHE_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")  # ⚠️ Required for production
    CACHE_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_USE_SSL: bool = os.getenv("REDIS_USE_SSL", "false").lower() == "true"


    # Application Configuration
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Server Configuration
    HOST: str = os.getenv("HOST", "")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate_aws_credentials(cls) -> bool:
        """
        Validate that required AWS credentials are present.

        Returns:
            bool: True if all AWS credentials are configured, False otherwise
        """
        required_vars = [
            cls.AWS_REGION,
            cls.AWS_ACCESS_KEY_ID,
            cls.AWS_SECRET_ACCESS_KEY,
        ]
        return all(required_vars)

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode."""
        return cls.APP_ENV.lower() == "development"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return cls.APP_ENV.lower() == "production"



    @classmethod
    def get_redis_url(cls) -> str:
        """
        Build Redis connection URL with authentication.

        Returns:
            str: Complete Redis URL (e.g., "redis://:password@host:port/db")
        """
        scheme = "rediss" if cls.CACHE_USE_SSL else "redis"

        if cls.CACHE_PASSWORD:
            # Format: redis://:password@host:port/db
            return f"{scheme}://:{cls.CACHE_PASSWORD}@{cls.CACHE_HOST}:{cls.CACHE_PORT}/{cls.CACHE_DB}"
        else:
            # Format: redis://host:port/db (no auth)
            return f"{scheme}://{cls.CACHE_HOST}:{cls.CACHE_PORT}/{cls.CACHE_DB}"

    @classmethod
    def validate_cache_config(cls) -> bool:
        """Validate cache configuration is complete."""
        if cls.is_production() and not cls.CACHE_PASSWORD:
            raise ValueError("REDIS_PASSWORD is required in production")
        return True
        
# Create a singleton instance
config = Config()
