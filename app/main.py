"""Main FastAPI application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from app.core.config import settings
from app.api.v1.api import api_router
from app.models.schemas import HealthCheck

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# Sentinel - Nigerian Fraud Detection Platform

## Overview

Sentinel is Africa's leading fraud detection platform for financial institutions.
Prevent fraud losses through real-time risk intelligence and consortium-based
fraud pattern sharing.

## Key Features

- **Real-Time Detection**: <100ms response time
- **15+ Detection Rules**: Comprehensive fraud detection
- **Consortium Intelligence**: Cross-lender fraud pattern detection
- **Privacy-Preserving**: SHA-256 hashing protects customer PII
- **Continuous Learning**: Improves accuracy over time

## Authentication

All API endpoints require authentication via API key.

Add your API key to the request header:
```
X-API-Key: your-api-key-here
```

## Rate Limits

- **Starter**: 50,000 requests/month
- **Growth**: 200,000 requests/month
- **Enterprise**: Unlimited requests

## Support

For support, contact: support@sentinel-fraud.com
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """
    Health check endpoint

    Returns the current health status of the API and its dependencies.
    """
    # In production, check database and Redis connectivity
    database_status = "ok"
    redis_status = "ok"

    try:
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        database_status = f"error: {str(e)}"

    # Redis check would go here
    # For now, assume ok

    overall_status = "ok" if database_status == "ok" and redis_status == "ok" else "degraded"

    return HealthCheck(
        status=overall_status,
        version=settings.APP_VERSION,
        database=database_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint

    Returns basic API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }


# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    print(f"📚 API documentation: http://localhost:8000/docs")
    print(f"🏥 Health check: http://localhost:8000/health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print(f"👋 {settings.APP_NAME} shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
