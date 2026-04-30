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
import bcrypt

from app.config import settings


# --- Password Hashing ---
# We use bcrypt directly (not passlib) because passlib has a known
# compatibility bug with bcrypt>=4.1. Using bcrypt directly is simpler
# and avoids the issue entirely.


def hash_password(password: str) -> str:
    """
    Hash a plain-text password for safe storage using bcrypt.
    
    How it works:
    1. Generate a random "salt" (random bytes mixed into the hash)
    2. Hash the password + salt together
    3. Return the hash (which includes the salt, so we can verify later)
    
    The same password produces DIFFERENT hashes each time (due to random salt).
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain-text password matches a stored bcrypt hash.
    Used during login to verify the user's password.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


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
