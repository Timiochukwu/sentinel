"""API dependencies - authentication, database sessions, etc."""

from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Client
from app.core.config import settings


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias=settings.API_KEY_HEADER)
) -> str:
    """
    Validate API key from request header

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        API key if valid

    Raises:
        HTTPException if API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


async def get_current_client(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
) -> Client:
    """
    Get current client from API key

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Client object

    Raises:
        HTTPException if API key is invalid or client is inactive
    """
    client = db.query(Client).filter(Client.api_key == api_key).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if client.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {client.status}. Please contact support.",
        )

    return client


def check_rate_limit(client: Client = Depends(get_current_client)) -> Client:
    """
    Check rate limit for client

    In production, this would use Redis to track request counts.
    For MVP, we'll implement a simple check.

    Args:
        client: Current client

    Returns:
        Client object

    Raises:
        HTTPException if rate limit exceeded
    """
    # In production, implement Redis-based rate limiting
    # For now, just return the client
    return client
