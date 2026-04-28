# =============================================================================
# api/auth.py — Authentication Endpoints
# =============================================================================
# WHAT IS A ROUTER?
# A router is a group of related API endpoints. Instead of putting every
# endpoint in main.py, we organize them by feature (auth, jobs, resumes, etc.)
# 
# WHAT IS AN ENDPOINT?
# An endpoint is a URL that your API responds to. For example:
#   POST /api/auth/register  →  Creates a new user account
#   POST /api/auth/login     →  Returns a JWT token
#   GET  /api/auth/me        →  Returns the current user's profile
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
)

# Create a router with a prefix — all endpoints here will start with "/auth"
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegister,           # FastAPI auto-validates the request body
    db: AsyncSession = Depends(get_db),  # DI: get a database session
):
    """
    Register a new user account.
    
    Steps:
    1. Check if email already exists
    2. Hash the password (NEVER store plain text!)
    3. Create the user in the database
    4. Generate a JWT token
    5. Return the token + user data
    """
    
    # Step 1: Check for existing email
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Step 2: Hash the password
    hashed_pw = hash_password(data.password)
    
    # Step 3: Create user object and add to database
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hashed_pw,
    )
    db.add(user)
    await db.flush()  # flush = write to DB but don't commit yet (gets the auto-generated ID)
    
    # Step 4: Create JWT token
    access_token = create_access_token(data={"sub": user.id})
    
    # Step 5: Return response
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get an access token",
)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user and return a JWT token.
    
    The token should be included in subsequent requests:
        Authorization: Bearer <token>
    """
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # Verify user exists AND password matches
    # We use the same error for both cases to prevent email enumeration attacks
    # (don't tell attackers whether an email exists or not)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
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
    current_user: User = Depends(get_current_user),  # DI: requires authentication
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
