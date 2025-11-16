"""
API Rate Limiting Middleware

This module provides protection against API abuse and DoS attacks by limiting
the number of requests a client can make within a time window.

How it works:
1. Each API key gets a "bucket" in Redis that tracks request count
2. When a request comes in, we increment the counter
3. If counter exceeds limit, return 429 Too Many Requests
4. Counter resets after the time window (default: 1 minute)

Example:
- Starter plan: 100 requests/minute
- Pro plan: 1,000 requests/minute
- Enterprise plan: 10,000 requests/minute
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on API requests

    This prevents abuse by limiting how many requests a client can make
    per minute. Uses Redis for distributed rate limiting across multiple servers.
    """

    def __init__(self, app, redis_service=None):
        """
        Initialize rate limiter

        Args:
            app: FastAPI application instance
            redis_service: Redis service for storing rate limit counters
        """
        super().__init__(app)
        self.redis = redis_service

        # Rate limit tiers (requests per minute)
        # These can be customized based on client's subscription plan
        self.rate_limits: Dict[str, int] = {
            "starter": 100,      # Free/Starter tier: 100 req/min
            "pro": 1000,         # Pro tier: 1,000 req/min
            "enterprise": 10000, # Enterprise: 10,000 req/min
            "default": 100       # Default limit if no tier specified
        }

        # Time window in seconds (60 seconds = 1 minute)
        self.window_seconds = 60

    async def dispatch(self, request: Request, call_next):
        """
        Process each request and enforce rate limits

        Flow:
        1. Extract API key from request headers
        2. Check current request count in Redis
        3. If under limit: allow request and increment counter
        4. If over limit: return 429 error

        Args:
            request: Incoming HTTP request
            call_next: Function to call next middleware or endpoint

        Returns:
            HTTP response (either from endpoint or 429 error)
        """

        # Skip rate limiting for health check and documentation endpoints
        # These should always be accessible
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Extract API key from request headers
        # Clients send this as "X-API-Key: their_api_key_here"
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")

        # If no API key provided, block the request
        # All API endpoints (except health checks) require authentication
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Missing API key",
                    "message": "Please provide X-API-Key header"
                }
            )

        # Check if Redis is available
        # If Redis is down, we allow requests through (fail-open)
        # This prevents rate limiter from breaking the entire API
        if not self.redis or not self.redis.redis:
            # Redis not available, allow request through
            return await call_next(request)

        try:
            # Check rate limit for this API key
            # Returns True if allowed, False if rate limit exceeded
            allowed, remaining, reset_time = await self._check_rate_limit(api_key)

            if not allowed:
                # Rate limit exceeded - return 429 error
                return JSONResponse(
                    status_code=status.HTTP_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"You have exceeded your rate limit. Try again in {reset_time} seconds.",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(self._get_limit_for_key(api_key)),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                        "Retry-After": str(reset_time)
                    }
                )

            # Process the request
            response = await call_next(request)

            # Add rate limit info to response headers
            # Clients can use these to track their usage
            response.headers["X-RateLimit-Limit"] = str(self._get_limit_for_key(api_key))
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)

            return response

        except Exception as e:
            # If rate limiting fails for any reason, allow the request through
            # This ensures rate limiter doesn't break the API
            print(f"Rate limiting error: {e}")
            return await call_next(request)

    async def _check_rate_limit(self, api_key: str) -> tuple[bool, int, int]:
        """
        Check if API key has exceeded rate limit

        Uses Redis sliding window algorithm:
        1. Key format: "rate_limit:{api_key}"
        2. Value: current request count
        3. TTL: 60 seconds (resets every minute)

        Args:
            api_key: Client's API key

        Returns:
            Tuple of (allowed, remaining_requests, seconds_until_reset)

        Example:
            allowed, remaining, reset = await _check_rate_limit("key_123")
            if allowed:
                print(f"Request allowed. {remaining} requests remaining.")
            else:
                print(f"Rate limited. Try again in {reset} seconds.")
        """

        # Get rate limit for this API key
        # Different tiers have different limits
        limit = self._get_limit_for_key(api_key)

        # Redis key format: "rate_limit:api_key_here"
        # This groups all rate limit data under "rate_limit:" prefix
        redis_key = f"rate_limit:{api_key}"

        try:
            # Get current request count from Redis
            # Returns None if key doesn't exist (first request)
            current = await self.redis.get(redis_key)
            current_count = int(current) if current else 0

            # Check if limit exceeded
            if current_count >= limit:
                # Get remaining TTL (time until reset)
                ttl = await self.redis.redis.ttl(redis_key)
                reset_time = ttl if ttl > 0 else self.window_seconds

                # Return: not allowed, 0 remaining, seconds until reset
                return False, 0, reset_time

            # Increment counter
            # If key doesn't exist, this creates it with value 1
            new_count = await self.redis.redis.incr(redis_key)

            # Set expiration on first request
            # After 60 seconds, counter resets to 0
            if new_count == 1:
                await self.redis.redis.expire(redis_key, self.window_seconds)

            # Calculate remaining requests
            remaining = limit - new_count

            # Get TTL for reset time
            ttl = await self.redis.redis.ttl(redis_key)
            reset_time = ttl if ttl > 0 else self.window_seconds

            # Return: allowed, remaining requests, seconds until reset
            return True, remaining, reset_time

        except Exception as e:
            # If Redis operation fails, allow request through
            print(f"Redis rate limit error: {e}")
            return True, limit, self.window_seconds

    def _get_limit_for_key(self, api_key: str) -> int:
        """
        Get rate limit for specific API key

        In production, you would:
        1. Look up client's subscription tier in database
        2. Return appropriate limit based on their plan

        For now, we parse tier from API key format:
        - "starter_xxx" -> 100/min
        - "pro_xxx" -> 1,000/min
        - "enterprise_xxx" -> 10,000/min
        - Everything else -> 100/min (default)

        Args:
            api_key: Client's API key

        Returns:
            Requests per minute limit

        Example:
            limit = _get_limit_for_key("pro_abc123")
            # Returns: 1000
        """

        # In production, look up tier from database
        # For now, parse from API key prefix

        if api_key.startswith("enterprise_"):
            return self.rate_limits["enterprise"]
        elif api_key.startswith("pro_"):
            return self.rate_limits["pro"]
        elif api_key.startswith("starter_"):
            return self.rate_limits["starter"]
        else:
            # Default limit for unknown keys
            return self.rate_limits["default"]
