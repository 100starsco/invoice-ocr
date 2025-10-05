"""
Redis Client

Redis client for caching, session management, and queue operations.
"""

from typing import Any, Optional, Dict, List, Union
import json
from datetime import timedelta
import redis.asyncio as aioredis
import redis


class RedisClient:
    """
    Redis client for OCR service.

    Provides caching, session management, and queue-related operations.
    """

    def __init__(self, connection_url: str):
        """
        Initialize Redis client.

        Args:
            connection_url: Redis connection URL
        """
        self.connection_url = connection_url
        self._async_client: Optional[aioredis.Redis] = None
        self._sync_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """
        Establish connection to Redis.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._async_client = aioredis.from_url(
                self.connection_url,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self._async_client.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None

    # Cache Operations
    async def set_cache(
        self,
        key: str,
        value: Any,
        expire: Optional[timedelta] = None
    ) -> bool:
        """
        Set cache value.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire: Optional expiration time

        Returns:
            True if successful
        """
        try:
            serialized_value = self._serialize_value(value)
            if expire:
                await self._async_client.setex(key, int(expire.total_seconds()), serialized_value)
            else:
                await self._async_client.set(key, serialized_value)
            return True
        except Exception:
            return False

    async def get_cache(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get cache value.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            cached_value = await self._async_client.get(key)
            if cached_value is None:
                return default
            return self._deserialize_value(cached_value)
        except Exception:
            return default

    async def delete_cache(self, key: str) -> bool:
        """
        Delete cache entry.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        try:
            result = await self._async_client.delete(key)
            return result > 0
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            result = await self._async_client.exists(key)
            return result > 0
        except Exception:
            return False

    # Session Management
    async def create_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        expire: timedelta = timedelta(hours=24)
    ) -> bool:
        """
        Create user session.

        Args:
            session_id: Session identifier
            session_data: Session data to store
            expire: Session expiration time

        Returns:
            True if session created
        """
        # TODO: Implement session creation
        pass

    async def get_session(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        # TODO: Implement session retrieval
        pass

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            updates: Data to update

        Returns:
            True if successful
        """
        # TODO: Implement session update
        pass

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session identifier

        Returns:
            True if session deleted
        """
        # TODO: Implement session deletion
        pass

    # Job Status Tracking
    async def set_job_status(
        self,
        job_id: str,
        status_data: Dict[str, Any],
        expire: Optional[timedelta] = None
    ) -> bool:
        """
        Set job status in Redis.

        Args:
            job_id: Job identifier
            status_data: Status information
            expire: Optional expiration time

        Returns:
            True if successful
        """
        key = f"job_status:{job_id}"
        return await self.set_cache(key, status_data, expire)

    async def get_job_status(
        self,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get job status from Redis.

        Args:
            job_id: Job identifier

        Returns:
            Job status data or None
        """
        key = f"job_status:{job_id}"
        return await self.get_cache(key)

    # Queue Operations
    async def enqueue_job(
        self,
        queue_name: str,
        job_data: Dict[str, Any]
    ) -> bool:
        """
        Add job to queue.

        Args:
            queue_name: Queue name
            job_data: Job data to enqueue

        Returns:
            True if job enqueued
        """
        # TODO: Implement job enqueuing
        pass

    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get queue length.

        Args:
            queue_name: Queue name

        Returns:
            Number of jobs in queue
        """
        # TODO: Implement queue length check
        pass

    async def get_queue_stats(
        self,
        queue_name: str
    ) -> Dict[str, Any]:
        """
        Get queue statistics.

        Args:
            queue_name: Queue name

        Returns:
            Queue statistics
        """
        # TODO: Implement queue statistics
        pass

    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health.

        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            await self._async_client.ping()
            ping_time = (time.time() - start_time) * 1000  # Convert to ms

            info = await self._async_client.info()

            return {
                "status": "healthy",
                "ping_ms": round(ping_time, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Redis."""
        return self._async_client is not None

    # Utility Methods
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        return json.dumps(value, default=str)

    def _deserialize_value(self, data: str) -> Any:
        """Deserialize stored value."""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data


# Simple function for RQ workers to get Redis connection
def get_redis_connection() -> redis.Redis:
    """
    Get a simple Redis connection for RQ workers.

    Returns:
        Redis connection instance
    """
    import os

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

    try:
        connection = redis.from_url(redis_url)
        # Test connection
        connection.ping()
        return connection
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        # Fallback to default connection
        return redis.Redis(host='localhost', port=6379, db=0)