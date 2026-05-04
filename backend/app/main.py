# =============================================================================
# main.py — FastAPI Application Entry Point
# =============================================================================
# WHAT IS FastAPI?
# FastAPI is a modern Python web framework for building APIs. It:
#   1. Handles HTTP requests (GET, POST, PUT, DELETE)
#   2. Auto-validates request data using Pydantic schemas
#   3. Auto-generates interactive API docs at /docs (Swagger UI)
#   4. Supports async/await for high performance
#
# HOW TO RUN:
#   cd backend
#   uvicorn app.main:app --reload --port 8000
#
# Then open http://localhost:8000/docs to see your API!
# =============================================================================

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import init_db
from app.api.router import api_router


# --- Lifespan Events ---
# This runs startup/shutdown code for the app.
# `yield` separates startup (before) from shutdown (after).
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    
    Startup: Create database tables, ensure directories exist
    Shutdown: (cleanup would go after yield)
    """
    # === STARTUP ===
    print(">> Starting Job Agent API...")
    
    # Create storage directories
    storage_dir = Path(settings.STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / "resumes").mkdir(exist_ok=True)
    (storage_dir / "cover_letters").mkdir(exist_ok=True)
    (storage_dir / "screenshots").mkdir(exist_ok=True)
    
    # Create database tables
    await init_db()
    print("[OK] Database initialized")
    print("[>>] API docs available at http://localhost:8000/docs")
    
    yield  # App is running here
    
    # === SHUTDOWN ===
    print("[--] Shutting down Job Agent API...")


# --- Create the FastAPI App ---
app = FastAPI(
    title="Job Agent API",
    description=(
        "AI-powered autonomous job application system. "
        "Discovers jobs, tailors resumes, submits applications, and tracks everything."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# --- CORS Middleware ---
# CORS (Cross-Origin Resource Sharing) controls which websites can call your API.
# Without this, your Next.js frontend (running on port 3000) can't call the
# FastAPI backend (running on port 8000) — browsers block it by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)


from fastapi.staticfiles import StaticFiles

# --- Mount API Router ---
app.include_router(api_router)

# --- Mount Static Files for Screenshots ---
storage_dir = Path(settings.STORAGE_DIR)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")


# --- Root Endpoint ---
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint. Returns basic app info."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "sqlite",
        "llm_provider": "pollinations",
    }
