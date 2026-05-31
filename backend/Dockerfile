# =============================================================================
# Backend Dockerfile — FastAPI + Python
# =============================================================================
# This builds a lightweight Python container that runs the JobPilot backend.
#
# HOW IT WORKS:
#   1. Starts from a slim Python base image (small download, ~150 MB)
#   2. Installs system-level libraries needed by some Python packages
#   3. Copies and installs Python dependencies (pip install)
#   4. Copies your application code
#   5. Starts the FastAPI server using Uvicorn
#
# The database file (SQLite) is NOT baked into the image — it lives on
# your computer and is "mounted" into the container at runtime via
# docker-compose.yml. This means your data persists even when the
# container is deleted.
# =============================================================================

# --- Stage 1: Base Image ---
# python:3.11-slim is a minimal Debian-based Python image (~150 MB).
# "slim" means it has just enough to run Python — no bloat.
FROM python:3.11-slim

# --- System Dependencies ---
# Some Python packages (like pdfplumber, bcrypt, lxml) need C compilers
# and system libraries to install. We install them here.
# 
# What each package does:
#   build-essential  → C/C++ compiler (needed by bcrypt, lxml)
#   libffi-dev       → Foreign Function Interface (needed by cryptography)
#   curl             → For health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Working Directory ---
# All subsequent commands run inside /app
WORKDIR /app

# --- Install Python Dependencies ---
# We copy requirements.txt FIRST (before the rest of the code) because
# Docker caches each step. If requirements.txt hasn't changed, Docker
# skips the slow "pip install" step on subsequent builds.
# This is called "layer caching" and makes rebuilds 10x faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Install the project in editable mode ---
# Some imports (like `from app.config import settings`) require the
# package to be installed. We copy pyproject.toml and install it.
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# --- Copy Application Code ---
# Now we copy the actual Python source code into the container.
# This step is LAST so that code changes don't invalidate the
# dependency cache above.
COPY app/ app/

# --- Create Data Directory ---
# This directory will be overridden by the volume mount in docker-compose,
# but we create it here as a fallback for standalone runs.
RUN mkdir -p data/storage/resumes data/storage/cover_letters data/storage/screenshots

# --- Expose Port ---
# This tells Docker (and humans reading this file) that the app
# listens on port 8000. It doesn't actually open the port — that's
# done in docker-compose.yml.
EXPOSE 8000

# --- Health Check ---
# Docker will periodically hit this endpoint to check if the container
# is healthy. If it fails 3 times in a row, Docker marks it as unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# --- Start Command ---
# This is what runs when the container starts.
# --host 0.0.0.0 means "accept connections from anywhere" (not just localhost).
# This is required inside Docker because the container has its own network.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
