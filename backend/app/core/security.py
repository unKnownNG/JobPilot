# =============================================================================
# security.py — Authentication & Password Hashing
# =============================================================================
# WHAT IS THIS?
# This file handles two critical security operations:
#
# 1. PASSWORD HASHING — Never store passwords as plain text! We use bcrypt
#    to turn "mypassword123" into "$2b$12$LJ3m4ys..." which is irreversible.
#    Even if someone steals the database, they can't recover passwords.
#
# 2. JWT TOKENS — After login, we give the user a "signed ticket" (JWT) that
#    they send with every request. The server can verify the signature without
#    checking the database — it's fast and stateless.
#
# HOW JWT WORKS:
#    Login → Server creates JWT with user_id + expiry → Client stores it
#    Every request → Client sends JWT in header → Server verifies signature
#    Expired? → Client must login again
# =============================================================================

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# --- Password Hashing ---
# CryptContext manages the hashing algorithm (bcrypt) and handles:
# - Hashing passwords for storage
# - Verifying passwords during login
# - Auto-upgrading old hashes if you change algorithms later
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password for safe storage.
    
    Example:
        hash_password("mypassword123")
        → "$2b$12$LJ3m4ysF6K3z..." (60 characters, irreversible)
    
    The same password produces DIFFERENT hashes each time (due to random salt).
    This means even if two users have the same password, their hashes differ.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain-text password matches a hashed password.
    Used during login to verify the user's password.
    
    Example:
        verify_password("mypassword123", "$2b$12$LJ3m4ys...")  → True
        verify_password("wrongpassword", "$2b$12$LJ3m4ys...")  → False
    """
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Token Creation ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The payload to encode. Usually {"sub": user_id}
              "sub" is JWT standard for "subject" (who this token is for).
        expires_delta: How long until the token expires.
    
    Returns:
        A signed JWT string like "eyJhbGciOiJIUzI1NiIs..."
    
    The token contains:
        - Your data (user_id)
        - Expiration time
        - A cryptographic signature (so nobody can tamper with it)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})  # Add expiration to the payload
    
    # Sign the token with our secret key
    # Anyone can READ a JWT (it's just base64), but only we can CREATE valid ones
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and extract the user_id.
    
    Returns:
        The user_id (sub) if the token is valid, None otherwise.
    
    This fails if:
        - The token has been tampered with (signature doesn't match)
        - The token has expired
        - The token is malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
