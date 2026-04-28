# =============================================================================
# schemas/user.py — Request/Response Schemas for User Endpoints
# =============================================================================
# WHAT ARE SCHEMAS (vs MODELS)?
#
# MODELS (app/models/) = define the DATABASE structure (what's stored in SQLite)
# SCHEMAS (app/schemas/) = define the API structure (what the client sends/receives)
#
# Why have both? Because they serve different purposes:
# - You NEVER want to expose the hashed_password in an API response
# - The client sends a plain password during registration, but the DB stores a hash
# - Some fields are auto-generated (id, created_at) and shouldn't be in the request
#
# Pydantic validates all incoming data — if someone sends a number where a string
# is expected, they get a clear error message instead of a database crash.
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# --- Request Schemas (what the client SENDS) ---

class UserRegister(BaseModel):
    """Schema for user registration request."""
    email: str = Field(
        ...,                      # ... means "required"
        description="User's email address",
        examples=["user@example.com"],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's display name",
        examples=["Mohammed"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters)",
        examples=["securepassword123"],
    )


class UserLogin(BaseModel):
    """Schema for login request."""
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., examples=["securepassword123"])


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    preferences: Optional[dict] = Field(
        None,
        description="Job search preferences",
        examples=[{
            "target_role": "Backend Engineer",
            "location": "Remote",
            "min_salary": 80000,
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        }],
    )


# --- Response Schemas (what the server RETURNS) ---

class UserResponse(BaseModel):
    """Schema for user data in API responses. Note: NO password field!"""
    id: str
    email: str
    name: str
    preferences: Optional[dict] = None
    is_active: bool
    created_at: datetime
    
    # This tells Pydantic to read data from ORM objects (SQLAlchemy models)
    # Without this, Pydantic can't convert a User model to a UserResponse
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for the login response — contains the JWT token."""
    access_token: str
    token_type: str = "bearer"  # Always "bearer" for JWT
    user: UserResponse
