import json
from typing import Dict, List, Optional, Any
import redis.asyncio as redis
from app.core.config import config
from app.core.exceptions import CacheError


class RedisStream:
    """Redis Streams implementation for async job processing."""

    def __init__(self):
        """Initialize Redis Stream client."""
        if not config.CACHE_HOST:
            raise CacheError("CACHE_HOST not configured")

        # For streams, decode_responses must handle binary data
        self.redis = redis.from_url(
            f"redis://{config.CACHE_HOST}",
            encoding="utf-8",
            decode_responses=True
        )

    async def add_to_stream(
        self,
        stream_name: str,
        data: Dict[str, Any],
        max_len: Optional[int] = 10000  # Prevent unlimited growth. TODO: fetch this from env later
    ) -> str:
        """
        Add message to stream.

        Args:
            stream_name: Stream key (e.g., "report:processing")
            data: Message data as dict
            max_len: Max stream length (FIFO, old messages dropped)

        Returns:
            str: Message ID (e.g., "1234567890123-0")
        """
        try:
            # Serialize complex objects
            serialized = {k: json.dumps(v) if isinstance(v, (dict, list)) else v
                         for k, v in data.items()}

            message_id = await self.redis.xadd(
                stream_name,
                serialized,
                maxlen=max_len,
                approximate=True  # More efficient trimming
            )
            return message_id
        except Exception as e:
            raise CacheError(f"Failed to add to stream {stream_name}: {str(e)}") from e

    async def create_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group. Safe to call multiple times.

        Args:
            stream_name: Stream key
            group_name: Consumer group name
            start_id: Start from ("0" = beginning, "$" = new messages only)
        """
        try:
            await self.redis.xgroup_create(
                stream_name,
                group_name,
                start_id,
                mkstream=True  # Create stream if doesn't exist
            )
            return True
        except redis.ResponseError as e:
            # Group already exists - this is fine
            if "BUSYGROUP" in str(e):
                return True
            raise CacheError(f"Failed to create consumer group: {str(e)}") from e

    async def read_from_stream(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        count: int = 1,
        block: Optional[int] = 5000  # 5 seconds default
    ) -> List[Dict[str, Any]]:
        """
        Read messages from stream as consumer.

        Args:
            stream_name: Stream key
            consumer_group: Consumer group name
            consumer_name: Unique consumer ID (e.g., "worker-1")
            count: Max messages to read
            block: Block for milliseconds (None = no blocking)

        Returns:
            List of messages with 'id', 'stream', and 'data' keys
        """
        try:
            # Read new messages for this consumer group
            messages = await self.redis.xreadgroup(
                consumer_group,
                consumer_name,
                {stream_name: ">"},  # ">" = only new messages
                count=count,
                block=block
            )

            result = []
            for stream, msgs in messages:
                for msg_id, data in msgs:
                    # Deserialize data
                    deserialized = {}
                    for k, v in data.items():
                        try:
                            deserialized[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            deserialized[k] = v

                    result.append({
                        "id": msg_id,
                        "stream": stream,
                        "data": deserialized
                    })

            return result
        except Exception as e:
            raise CacheError(f"Failed to read from stream: {str(e)}") from e

    async def ack_message(
        self,
        stream_name: str,
        group_name: str,
        message_id: str
    ) -> bool:
        """Acknowledge successful message processing."""
        try:
            await self.redis.xack(stream_name, group_name, message_id)
            return True
        except Exception as e:
            raise CacheError(f"Failed to ack message: {str(e)}") from e

    async def get_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get messages that were delivered but not acknowledged."""
        try:
            # Claim messages idle for 60+ seconds
            messages = await self.redis.xautoclaim(
                stream_name,
                group_name,
                consumer_name,
                min_idle_time=60000,  # 60 seconds
                start_id="0-0",
                count=count
            )

            # Parse claimed messages
            result = []
            if len(messages) > 1:
                for msg_id, data in messages[1]:
                    result.append({
                        "id": msg_id,
                        "data": data
                    })
            return result
        except Exception as e:
            raise CacheError(f"Failed to claim pending messages: {str(e)}") from e

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
