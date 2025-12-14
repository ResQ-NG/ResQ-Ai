"""
Debug script to check Redis stream contents.
Run with: python debug_stream.py
"""
import asyncio

from app.adapters.cache.redis_stream import RedisStream
from app.domain.constants.stream_constants import REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION






async def main():
    """Read and display all messages from the categorization stream."""
    stream = RedisStream()

    print(f"Reading all messages from stream: {REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION}")
    print("=" * 80)

    try:
        messages = await stream.read_all_messages(REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION)

        if not messages:
            print("No messages found in stream.")
        else:
            print(f"Found {len(messages)} message(s):\n")

            for i, msg in enumerate(messages, 1):
                print(f"Message {i}:")
                print(f"  ID: {msg['id']}")
                print(f"  Stream: {msg['stream']}")
                print("  Data:")
                for key, value in msg['data'].items():
                    print(f"    {key}: {value}")
                print()

        # Also check stream length using Redis command
        length = await stream.redis.xlen(REDIS_STREAM_REPORT_LIGHT_CATEGORIZATION)
        print(f"Stream length (from Redis): {length}")

    except Exception as e:
        print(f"Error reading stream: {e}")
    finally:
        await stream.close()


if __name__ == "__main__":
    asyncio.run(main())
