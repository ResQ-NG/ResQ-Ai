
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

    async def get(self, key: str):
        """Retrieve value from cache by key."""
        try:
            return await self.redis.get(key)
        except Exception as exc:
            raise CacheError(f"Failed to get key '{key}': {str(exc)}") from exc

    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Store value in cache with optional TTL (seconds)."""
        try:
            if ttl:
                return await self.redis.setex(key, ttl, value)
            else:
                return await self.redis.set(key, value)
        except Exception as exc:
            raise CacheError(f"Failed to set key '{key}': {str(exc)}") from exc

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as exc:
            raise CacheError(f"Failed to delete key '{key}': {str(exc)}") from exc

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as exc:
            raise CacheError(f"Failed to check existence of key '{key}': {str(exc)}") from exc

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            try:
                await self.redis.close()
            except Exception as exc:
                raise CacheError(f"Failed to close Redis connection: {str(exc)}") from exc
