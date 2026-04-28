# =============================================================================
# api/router.py — Root API Router
# =============================================================================
# This file combines all the individual routers (auth, jobs, resumes, etc.)
# into a single root router that gets mounted on the FastAPI app.
#
# Think of it as the "table of contents" for your API.
# =============================================================================

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router
from app.api.applications import router as applications_router

# Create the root router — all endpoints will be prefixed with "/api"
api_router = APIRouter(prefix="/api")

# Include all feature routers
api_router.include_router(auth_router)       # /api/auth/...
api_router.include_router(jobs_router)        # /api/jobs/...
api_router.include_router(resumes_router)     # /api/resumes/...
api_router.include_router(applications_router)  # /api/applications/...
