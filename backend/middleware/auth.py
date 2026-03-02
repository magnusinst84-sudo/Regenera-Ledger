"""
Authentication Middleware
JWT verification and role-based access control for FastAPI.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv

from db import get_document

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # In production, crash hard so you notice immediately. In dev, warn and use a temp secret.
    import sys
    if os.getenv("ENVIRONMENT", "development") == "production":
        print("FATAL: JWT_SECRET env var is not set. Cannot start in production without it.")
        sys.exit(1)
    else:
        print("WARNING: JWT_SECRET is not set. Using insecure dev default. Set it in .env before deploying.")
        JWT_SECRET = "dev-insecure-secret-CHANGE-BEFORE-DEPLOY"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()


# ════════════════════════════════════════════
# Token Utilities
# ════════════════════════════════════════════

def create_access_token(user_id: str, role: str, email: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ════════════════════════════════════════════
# FastAPI Dependencies
# ════════════════════════════════════════════

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI dependency: extracts and validates JWT from Authorization header.
    Returns the user dict from Firestore with id, email, role, etc.
    """
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = get_document("users", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory: restricts access to specific roles.
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(user = Depends(require_role("company"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",
            )
        return user
    return role_checker
