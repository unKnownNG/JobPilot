# =============================================================================
# config.py — Application Settings
# =============================================================================
# WHAT IS THIS?
# This file defines ALL configuration for the app in one place.
# It reads values from the .env file automatically.
#
# WHY USE THIS PATTERN?
# Instead of scattering `os.getenv("SOME_KEY")` calls everywhere in your code,
# you define a single Settings class. Any file can import `settings` and access
# any config value with autocomplete: `settings.DATABASE_URL`
#
# HOW IT WORKS:
# Pydantic Settings reads your .env file and validates every value.
# If a required value is missing, you get a clear error at startup — not a
# mysterious crash at 2 AM when some random function tries to read an env var.
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings. Values are read from .env file automatically.
    
    Each field here maps to an environment variable:
        APP_NAME in .env  →  self.APP_NAME in Python
    """
    
    # --- App ---
    APP_NAME: str = "JobAgent"
    DEBUG: bool = True
    
    # --- Database ---
    # This URL tells SQLAlchemy WHERE the database is and HOW to connect.
    # Format: "dialect+driver:///path"
    # - sqlite+aiosqlite = use SQLite with async driver
    # - ///./data/job_agent.db = relative path to the database file
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/job_agent.db"
    
    # --- JWT Auth ---
    # JWT (JSON Web Token) is like a "signed ticket" that proves who you are.
    # The server creates it on login, and the client sends it with every request.
    JWT_SECRET_KEY: str = "super-secret-dev-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"  # The signing algorithm
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # --- Pollinations API ---
    POLLINATIONS_BASE_URL: str = "https://text.pollinations.ai"
    
    # --- File Storage ---
    STORAGE_DIR: str = "./data/storage"
    
    # Tell Pydantic where to find the .env file
    model_config = SettingsConfigDict(
        env_file=".env",        # Read from .env in the current directory
        env_file_encoding="utf-8",
        case_sensitive=True,     # APP_NAME ≠ app_name
        extra="ignore",          # Don't crash if .env has extra variables
    )


# Create a single instance — import this everywhere
# Usage: from app.config import settings
settings = Settings()
