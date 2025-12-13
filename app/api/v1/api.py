"""API v1 router - combines all endpoint routers"""

from fastapi import APIRouter
from app.api.v1.endpoints import fraud_detection, feedback, dashboard, consortium, vertical

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    fraud_detection.router,
    tags=["fraud-detection"]
)

api_router.include_router(
    feedback.router,
    tags=["feedback"]
)

api_router.include_router(
    dashboard.router,
    tags=["dashboard"]
)

api_router.include_router(
    consortium.router,
    tags=["consortium"]
)

api_router.include_router(
    vertical.router,
    prefix="/verticals",
    tags=["verticals"]
)
