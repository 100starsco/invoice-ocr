"""
Authentication Middleware for OCR Service

Provides API key authentication for service-to-service communication.
"""

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key header configuration
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

# Get API key from environment
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")

def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key for service authentication.

    Args:
        api_key: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If authentication fails
    """
    if not SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service API key not configured"
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": f"{API_KEY_HEADER}"}
        )

    if api_key != SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": f"{API_KEY_HEADER}"}
        )

    return api_key

def optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key verification for endpoints that can work with or without auth.

    Args:
        api_key: API key from request header

    Returns:
        API key if valid, None otherwise
    """
    if not SERVICE_API_KEY or not api_key:
        return None

    if api_key == SERVICE_API_KEY:
        return api_key

    return None