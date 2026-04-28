# =============================================================================
# dependencies.py — Dependency Injection
# =============================================================================
# WHAT IS DEPENDENCY INJECTION (DI)?
# Instead of creating objects inside your functions, you DECLARE what you need
# and FastAPI gives it to you. This makes your code:
#   1. Testable — swap real database for a mock in tests
#   2. Clean — no boilerplate setup code in every endpoint
#   3. Secure — auth check runs BEFORE your endpoint code
#
# Example:
#   async def my_endpoint(db: AsyncSession = Depends(get_db)):
#       # FastAPI calls get_db() and passes the result as `db`
#       # You just use it — the framework handles lifecycle
# =============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

# This tells FastAPI to look for "Authorization: Bearer <token>" in headers
# It automatically returns 401 if the header is missing
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the current user from the JWT token.
    
    Flow:
    1. FastAPI extracts the token from "Authorization: Bearer <token>" header
    2. We verify the token's signature and extract the user_id
    3. We look up the user in the database
    4. If anything fails, we return 401 Unauthorized
    
    Usage:
        @router.get("/profile")
        async def get_profile(user: User = Depends(get_current_user)):
            return user  # This is the authenticated user object
    """
    
    # Step 1: Verify the JWT token
    token = credentials.credentials
    user_id = verify_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 2: Look up the user in the database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    return user
