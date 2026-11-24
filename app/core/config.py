"""Application settings loaded from environment variables."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for database, Redis cache, and API."""

    app_name: str = os.getenv("APP_NAME", "FastAPI Redis Booking Template")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./booking.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "60"))


settings = Settings()
