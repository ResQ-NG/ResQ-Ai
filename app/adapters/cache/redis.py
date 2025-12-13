
import redis.asyncio as redis
from app.core.config import config
from app.core.exceptions import CacheError


class RedisCache:
    """Redis implementation with authentication support."""

    def __init__(self) -> None:
        """Initialize Redis client with authentication."""
        if not config.CACHE_HOST:
            raise CacheError("CACHE_HOST not configured")

        # Validate production requirements
        if config.is_production():
            config.validate_cache_config()

        try:
            # Use the complete Redis URL with auth
            self.redis = redis.from_url(
                config.get_redis_url(),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
        except Exception as exc:
            raise CacheError(f"Failed to initialize Redis client: {str(exc)}") from exc

    async def ping(self) -> bool:
        """Test Redis connection and authentication."""
        try:
            return await self.redis.ping()
        except redis.AuthenticationError as exc:
            raise CacheError("Redis authentication failed. Check REDIS_PASSWORD.") from exc
        except redis.ConnectionError as exc:
            raise CacheError("Cannot connect to Redis. Check REDIS_HOST and REDIS_PORT.") from exc
        except Exception as exc:
            raise CacheError(f"Redis connection error: {str(exc)}") from exc
