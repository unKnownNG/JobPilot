# =============================================================================
# database.py — Database Connection & Session Management
# =============================================================================
# WHAT IS THIS?
# This file sets up the connection to our SQLite database using SQLAlchemy.
#
# KEY CONCEPTS FOR BEGINNERS:
#
# 1. ENGINE — The "connection factory". It knows how to talk to your database.
#    Think of it as the phone line between Python and SQLite.
#
# 2. SESSION — A "conversation" with the database. You open a session, do your
#    work (read/write data), and close it. Like opening a tab at a bar — order
#    drinks, pay, close the tab.
#
# 3. BASE — The parent class for all your database models (tables). Every table
#    you create (User, JobPosting, etc.) inherits from this.
#
# 4. ASYNC — We use async/await so the server can handle other requests while
#    waiting for database operations. SQLite is fast, but this pattern scales.
# =============================================================================

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path

from app.config import settings


# Ensure the data directory exists (SQLite needs the directory to exist)
db_path = Path("./data")
db_path.mkdir(parents=True, exist_ok=True)


# --- Step 1: Create the Engine ---
# The engine is the starting point for all SQLAlchemy operations.
# `echo=True` prints all SQL queries to the console — great for learning!
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Print SQL queries when DEBUG=true
    
    # SQLite-specific: allow multiple threads to share a connection
    # (SQLite is single-writer by default, this is safe for local use)
    connect_args={"check_same_thread": False},
)


# --- Step 2: Create the Session Factory ---
# This creates a "factory" that produces database sessions.
# Every API request will get its own session (via dependency injection).
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,       # Use async sessions
    expire_on_commit=False,    # Don't expire objects after commit
    # ^ Without this, accessing user.name after commit would require
    #   another database query. We want the data to stay available.
)


# --- Step 3: Create the Base Class ---
# All your database models (User, JobPosting, etc.) inherit from this.
# It gives them the ability to be mapped to database tables.
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# --- Step 4: Dependency Injection Function ---
# FastAPI will call this function for every request that needs a database.
# It opens a session, lets the endpoint use it, then closes it.
#
# The `yield` keyword makes this a "generator" — it pauses, gives the session
# to the endpoint, waits for the endpoint to finish, then runs cleanup.
async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session to API endpoints.
    
    Usage in FastAPI:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # use db here
            pass
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()   # Save changes if everything went well
        except Exception:
            await session.rollback()  # Undo changes if something broke
            raise
        finally:
            await session.close()    # Always close the session


# --- Step 5: Create All Tables ---
# This function creates all tables in the database.
# Called once at startup.
async def init_db():
    """Create all database tables if they don't exist."""
    async with engine.begin() as conn:
        # Import all models so SQLAlchemy knows about them
        from app.models import user, job_posting, resume, application, agent_run  # noqa: F401
        
        # Create tables — this is safe to call multiple times,
        # it only creates tables that don't already exist.
        await conn.run_sync(Base.metadata.create_all)
