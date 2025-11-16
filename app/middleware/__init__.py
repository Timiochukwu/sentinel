"""
Middleware Package

Middleware are components that process requests BEFORE they reach your API endpoints
and AFTER the endpoint sends a response.

Think of middleware as checkpoints:
Request → Middleware 1 → Middleware 2 → Your API → Middleware 2 → Middleware 1 → Response

Common uses:
- Rate limiting (prevent abuse)
- Authentication (check API keys)
- Logging (track all requests)
- CORS (allow cross-origin requests)
- Request caching (speed up responses)
"""

from app.middleware.rate_limit import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
