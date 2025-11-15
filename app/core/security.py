"""Security utilities for authentication and hashing"""

import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def hash_identifier(identifier: str) -> str:
    """
    Create a privacy-preserving hash of sensitive identifiers (BVN, phone, device ID).
    Uses SHA-256 for one-way hashing to protect customer PII.

    Args:
        identifier: The sensitive identifier to hash (BVN, phone, device ID, etc.)

    Returns:
        SHA-256 hash of the identifier
    """
    if not identifier:
        return ""

    # Add a salt to make rainbow table attacks harder
    salted = f"{identifier}:{settings.SECRET_KEY}"
    return hashlib.sha256(salted.encode()).hexdigest()


def hash_device_id(device_id: str) -> str:
    """Hash a device ID for consortium intelligence"""
    return hash_identifier(device_id)


def hash_bvn(bvn: str) -> str:
    """Hash a BVN (Bank Verification Number) for consortium intelligence"""
    return hash_identifier(bvn)


def hash_phone(phone: str) -> str:
    """Hash a phone number for consortium intelligence"""
    # Normalize phone number (remove spaces, dashes, etc.)
    normalized = "".join(filter(str.isdigit, phone))
    return hash_identifier(normalized)


def hash_email(email: str) -> str:
    """Hash an email address for consortium intelligence"""
    # Normalize email (lowercase)
    normalized = email.lower().strip()
    return hash_identifier(normalized)
