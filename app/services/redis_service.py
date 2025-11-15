"""Redis service for caching, velocity tracking, and rate limiting"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings


class RedisService:
    """
    Redis service for high-performance caching and real-time operations

    Features:
    - Velocity tracking (transaction counts in time windows)
    - Rate limiting (API request throttling)
    - Caching (frequently accessed data)
    - Session management
    """

    def __init__(self):
        """Initialize Redis connection"""
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )

    # ==================== VELOCITY TRACKING ====================

    def track_transaction_velocity(
        self,
        user_id: str,
        client_id: str,
        amount: float
    ) -> Dict[str, int]:
        """
        Track transaction velocity for fraud detection

        Returns count of transactions in various time windows
        """
        now = datetime.utcnow()
        timestamp = int(now.timestamp())

        # Keys for different time windows
        keys = {
            "1min": f"velocity:{client_id}:{user_id}:1min",
            "10min": f"velocity:{client_id}:{user_id}:10min",
            "1hour": f"velocity:{client_id}:{user_id}:1hour",
            "24hour": f"velocity:{client_id}:{user_id}:24hour"
        }

        # Amount tracking keys
        amount_keys = {
            "1hour": f"velocity_amount:{client_id}:{user_id}:1hour",
            "24hour": f"velocity_amount:{client_id}:{user_id}:24hour"
        }

        pipe = self.client.pipeline()

        # Add transaction to sorted sets (score = timestamp)
        for key in keys.values():
            pipe.zadd(key, {timestamp: timestamp})

        # Track amounts
        for key in amount_keys.values():
            pipe.zadd(key, {f"{timestamp}:{amount}": timestamp})

        # Set expiration (cleanup old data)
        for key in keys.values():
            pipe.expire(key, 86400)  # 24 hours

        for key in amount_keys.values():
            pipe.expire(key, 86400)

        pipe.execute()

        # Get counts for each window
        cutoffs = {
            "1min": timestamp - 60,
            "10min": timestamp - 600,
            "1hour": timestamp - 3600,
            "24hour": timestamp - 86400
        }

        counts = {}
        for window, key in keys.items():
            cutoff = cutoffs[window]
            count = self.client.zcount(key, cutoff, timestamp)
            counts[f"transaction_count_{window}"] = count

        # Get amount totals
        for window, key in amount_keys.items():
            cutoff = cutoffs[window]
            members = self.client.zrangebyscore(key, cutoff, timestamp)
            total_amount = sum(float(m.split(':')[1]) for m in members)
            counts[f"total_amount_{window}"] = total_amount

        return counts

    def get_velocity_data(self, user_id: str, client_id: str) -> Dict[str, Any]:
        """Get current velocity data for a user"""
        now = int(datetime.utcnow().timestamp())

        keys = {
            "1min": f"velocity:{client_id}:{user_id}:1min",
            "10min": f"velocity:{client_id}:{user_id}:10min",
            "1hour": f"velocity:{client_id}:{user_id}:1hour",
            "24hour": f"velocity:{client_id}:{user_id}:24hour"
        }

        cutoffs = {
            "1min": now - 60,
            "10min": now - 600,
            "1hour": now - 3600,
            "24hour": now - 86400
        }

        data = {}
        for window, key in keys.items():
            cutoff = cutoffs[window]
            count = self.client.zcount(key, cutoff, now)
            data[f"transaction_count_{window}"] = count

        return data

    # ==================== RATE LIMITING ====================

    def check_rate_limit(
        self,
        client_id: str,
        limit: int = 10000,
        window: int = 3600
    ) -> Dict[str, Any]:
        """
        Check if client has exceeded rate limit

        Args:
            client_id: Client identifier
            limit: Maximum requests allowed
            window: Time window in seconds (default: 1 hour)

        Returns:
            Dict with allowed status and remaining count
        """
        key = f"ratelimit:{client_id}"

        # Use sliding window rate limiting
        now = int(datetime.utcnow().timestamp())
        window_start = now - window

        # Remove old entries
        self.client.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        current_count = self.client.zcard(key)

        if current_count >= limit:
            # Get oldest request timestamp
            oldest = self.client.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1]) + window - now if oldest else window

            return {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "retry_after": retry_after,
                "reset_at": now + retry_after
            }

        # Add current request
        self.client.zadd(key, {f"{now}:{client_id}": now})
        self.client.expire(key, window)

        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset_at": now + window
        }

    # ==================== CACHING ====================

    def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> bool:
        """
        Cache a value with TTL

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)
        """
        try:
            serialized = json.dumps(value)
            return self.client.setex(f"cache:{key}", ttl, serialized)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            value = self.client.get(f"cache:{key}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        return self.client.delete(f"cache:{key}") > 0

    def cache_clear_pattern(self, pattern: str) -> int:
        """Clear all cache keys matching pattern"""
        keys = self.client.keys(f"cache:{pattern}")
        if keys:
            return self.client.delete(*keys)
        return 0

    # ==================== DEVICE TRACKING ====================

    def track_device_usage(
        self,
        device_id: str,
        user_id: str,
        client_id: str
    ) -> int:
        """
        Track device usage across users

        Returns: Number of unique users for this device
        """
        key = f"device:{client_id}:{device_id}:users"
        self.client.sadd(key, user_id)
        self.client.expire(key, 2592000)  # 30 days
        return self.client.scard(key)

    def get_device_user_count(
        self,
        device_id: str,
        client_id: str
    ) -> int:
        """Get number of users for a device"""
        key = f"device:{client_id}:{device_id}:users"
        return self.client.scard(key)

    # ==================== SESSION MANAGEMENT ====================

    def create_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Create a session"""
        key = f"session:{session_id}"
        serialized = json.dumps(data)
        return self.client.setex(key, ttl, serialized)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = f"session:{session_id}"
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = f"session:{session_id}"
        return self.client.delete(key) > 0

    # ==================== FRAUD PATTERN CACHING ====================

    def cache_consortium_data(
        self,
        identifier_hash: str,
        data: Dict[str, Any],
        ttl: int = 300
    ) -> bool:
        """Cache consortium intelligence data"""
        key = f"consortium:{identifier_hash}"
        serialized = json.dumps(data)
        return self.client.setex(key, ttl, serialized)

    def get_consortium_data(
        self,
        identifier_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached consortium data"""
        key = f"consortium:{identifier_hash}"
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    # ==================== STATISTICS ====================

    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        return self.client.incrby(f"counter:{key}", amount)

    def get_counter(self, key: str) -> int:
        """Get counter value"""
        value = self.client.get(f"counter:{key}")
        return int(value) if value else 0

    def reset_counter(self, key: str) -> bool:
        """Reset counter to 0"""
        return self.client.delete(f"counter:{key}") > 0

    # ==================== HEALTH CHECK ====================

    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "version": info.get("redis_version")
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get Redis service singleton"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
