from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "Cloud FastAPI Deployment"
    app_version: str = "1.0.0"
    environment: str = Field(default="local", description="local/staging/production")
    debug: bool = False

    # For local smoke tests the app can run with SQLite.
    # For the exam/RDS, set DATABASE_URL to your RDS PostgreSQL connection string.
    database_url: str = "sqlite:///./local.db"

    # AWS/S3 configuration. boto3 also reads AWS_ACCESS_KEY_ID,
    # AWS_SECRET_ACCESS_KEY and AWS_DEFAULT_REGION automatically.
    aws_region: str = "ap-southeast-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    s3_upload_prefix: str = "uploads"
    presigned_url_expiration_seconds: int = 3600

    # CORS. Use comma-separated origins for production, e.g. https://example.com,https://admin.example.com
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """Normalize PostgreSQL URL for SQLAlchemy."""
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
