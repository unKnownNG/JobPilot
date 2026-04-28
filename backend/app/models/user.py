# =============================================================================
# user.py — User Database Model
# =============================================================================
# WHAT IS A MODEL?
# A model is a Python class that maps to a database table. Each instance of
# the class represents one row in the table.
#
# Example:
#   User class     →  "users" table in SQLite
#   User(name="Mo")  →  One row: | id | name | email | ... |
#                                 | 1  | Mo   | ...   | ... |
#
# WHY USE AN ORM (Object-Relational Mapper)?
# Instead of writing raw SQL like:
#   INSERT INTO users (name, email) VALUES ('Mo', 'mo@email.com')
# You write Python:
#   user = User(name="Mo", email="mo@email.com")
#   db.add(user)
#
# The ORM translates Python → SQL for you. Less error-prone, more readable.
# =============================================================================

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """
    The users table. Stores account information for each user.
    
    Mapped columns:
        id          — Unique identifier (UUID string)
        email       — Login email (must be unique)
        name        — Display name
        hashed_password — Bcrypt hash of the password (NEVER the plain password!)
        preferences — JSON blob for job search preferences (role, location, etc.)
        is_active   — Soft delete flag (deactivate without deleting data)
        created_at  — When the account was created
        updated_at  — Last modification timestamp
    """
    
    # This tells SQLAlchemy what the table is called in the database
    __tablename__ = "users"
    
    # --- Columns ---
    # Mapped[str] = this column holds a string value
    # mapped_column() = defines how the column behaves in the database
    
    id: Mapped[str] = mapped_column(
        String(36),               # 36-char string to hold a UUID
        primary_key=True,         # This is the primary key (unique identifier)
        default=lambda: str(uuid.uuid4()),  # Auto-generate a UUID for new users
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,    # No two users can have the same email
        index=True,     # Create an index for fast lookups by email
        nullable=False, # This field is required (can't be NULL)
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # JSON column — stores flexible, schema-less data
    # Perfect for user preferences that might change over time:
    # {"target_role": "Backend Engineer", "location": "Remote", "min_salary": 80000}
    preferences: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,   # Default to empty dict {}
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),  # Auto-update on changes
    )
    
    # --- Relationships ---
    # These define connections to other tables. SQLAlchemy handles the JOINs.
    # "back_populates" creates a two-way link: user.resumes ↔ resume.user
    resumes: Mapped[list["MasterResume"]] = relationship(
        "MasterResume", back_populates="user", lazy="selectin"
    )
    
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="user", lazy="selectin"
    )
    
    def __repr__(self):
        """How this object looks when printed (for debugging)."""
        return f"<User {self.name} ({self.email})>"
