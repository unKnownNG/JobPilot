# =============================================================================
# api/auth.py — Authentication Endpoints (Simplified)
# =============================================================================
# JobPilot uses a simple name-based setup instead of email/password login.
# Since this is a local-first app that runs on your own machine, there's no
# need for traditional authentication. On first launch, you enter your name
# and a local user is auto-created with a JWT token.
#
# Endpoints:
#   GET  /api/auth/status  →  Check if a user has been set up yet
#   POST /api/auth/setup   →  Create or return the local user (just needs a name)
#   GET  /api/auth/me      →  Returns the current user's profile
#   PUT  /api/auth/me      →  Update the current user's name/preferences
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, create_access_token
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserSetup,
    UserUpdate,
    UserResponse,
    TokenResponse,
    StatusResponse,
)

# Create a router with a prefix — all endpoints here will start with "/auth"
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Check if a user has been set up",
)
async def get_status(db: AsyncSession = Depends(get_db)):
    """
    Check whether a local user exists.
    The frontend uses this to decide whether to show the setup screen
    or go straight to the dashboard.
    """
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    return StatusResponse(is_setup=user is not None)


@router.post(
    "/setup",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Set up the local user (first-time) or get a new token",
)
async def setup(
    data: UserSetup,
    db: AsyncSession = Depends(get_db),
):
    """
    Create the local user on first launch, or return a new token if already set up.
    
    This replaces the old register/login flow. Since JobPilot runs locally,
    we just need a name — no email or password required.
    """
    
    # Check if a user already exists
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if user:
        # User exists — update name if provided and return a fresh token
        if data.name and data.name != user.name:
            user.name = data.name
            db.add(user)
            await db.flush()
    else:
        # First-time setup — create the local user
        user = User(
            email=f"local@jobpilot.local",
            name=data.name,
            hashed_password=hash_password("jobpilot-local"),  # Dummy, never checked
        )
        db.add(user)
        await db.flush()
    
    # Generate token
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get the currently authenticated user's profile.
    
    The `get_current_user` dependency:
    1. Extracts the JWT from the Authorization header
    2. Verifies the token
    3. Loads the user from the database
    4. Passes the user object to this function
    
    If any step fails, the client gets a 401 response automatically.
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile (name, preferences)."""
    
    if data.name is not None:
        current_user.name = data.name
    
    if data.preferences is not None:
        current_user.preferences = data.preferences
    
    db.add(current_user)
    await db.flush()
    
    return UserResponse.model_validate(current_user)
