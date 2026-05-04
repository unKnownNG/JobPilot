# =============================================================================
# models/__init__.py — Import all models so SQLAlchemy can resolve relationships
# =============================================================================
# This file MUST import every model class. Without this, SQLAlchemy's
# relationship() calls fail with "failed to locate a name" errors because
# the target model class hasn't been registered yet.
# =============================================================================

from app.models.user import User  # noqa: F401
from app.models.job_posting import JobPosting  # noqa: F401
from app.models.resume import MasterResume, TailoredResume  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.agent_run import AgentRun  # noqa: F401
