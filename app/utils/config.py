"""
Configuration management for ResQ AI application.
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


# Create a singleton instance
config = Config()
