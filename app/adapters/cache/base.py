from typing import Protocol, Optional, Any,  Dict, List

class CacheInterface(Protocol):
    """Protocol for cache client classes."""

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache by key."""

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store value in cache with optional TTL (seconds)."""

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

    async def close(self) -> None:
        """Close cache connection."""


class StreamInterface(Protocol):
    """Protocol for stream/queue client classes."""

    async def add_to_stream(
        self,
        stream_name: str,
        data: Dict[str, Any],
        max_len: Optional[int] = None
    ) -> str:
        """Add message to stream. Returns message ID."""

    async def read_from_stream(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        count: int = 1,
        block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read messages from stream as part of consumer group."""

    async def create_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """Create consumer group for stream."""

    async def ack_message(
        self,
        stream_name: str,
        group_name: str,
        message_id: str
    ) -> bool:
        """Acknowledge message processing."""
