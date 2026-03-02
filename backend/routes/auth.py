"""
Authentication Routes
Register and login endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import bcrypt

from db import create_document, get_collection
from middleware.auth import create_access_token
from utils.audit_logger import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Request / Response Models ──

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str  # "company" or "farmer"
    company_name: str = None
    sector: str = None

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    user: dict


# ════════════════════════════════════════════
# POST /api/auth/register
# ════════════════════════════════════════════

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user (company or farmer)."""
    
    # Validate role
    if req.role not in ("company", "farmer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'company' or 'farmer'",
        )
    
    # Check if email already exists
    existing = get_collection("users").where("email", "==", req.email).limit(1).stream()
    if any(existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    # Hash password
    password_hash = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    # Create user document
    user_data = {
        "email": req.email,
        "password_hash": password_hash,
        "name": req.name,
        "role": req.role,
        "company_name": req.company_name,
        "sector": req.sector,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    user_id = create_document("users", user_data)
    
    # Generate JWT
    token = create_access_token(user_id, req.role, req.email)
    
    # Audit log
    log_action(
        user_id=user_id,
        action="user_registered",
        entity_type="user",
        entity_id=user_id,
        details={"email": req.email, "role": req.role},
    )
    
    user_data["id"] = user_id
    del user_data["password_hash"]
    
    return AuthResponse(access_token=token, user=user_data)


# ════════════════════════════════════════════
# POST /api/auth/login
# ════════════════════════════════════════════

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login with email and password."""
    
    # Find user by email
    users_query = get_collection("users").where("email", "==", req.email).limit(1).stream()
    user_doc = None
    for doc in users_query:
        user_doc = doc
        break
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    user_data = user_doc.to_dict()
    user_id = user_doc.id
    
    # Verify password
    if not bcrypt.checkpw(req.password.encode("utf-8"), user_data["password_hash"].encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Generate JWT
    token = create_access_token(user_id, user_data["role"], user_data["email"])
    
    # Audit log
    log_action(
        user_id=user_id,
        action="user_login",
        entity_type="user",
        entity_id=user_id,
        details={"email": req.email},
    )
    
    user_data["id"] = user_id
    del user_data["password_hash"]
    
    return AuthResponse(access_token=token, user=user_data)


# ════════════════════════════════════════════
# GET /api/auth/me
# ════════════════════════════════════════════

from fastapi import Depends
from middleware.auth import get_current_user

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user
