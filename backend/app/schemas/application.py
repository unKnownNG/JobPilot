# =============================================================================
# schemas/application.py — Application Tracking Schemas
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationResponse(BaseModel):
    """Response schema for application data."""
    id: str
    user_id: str
    job_posting_id: str
    tailored_resume_id: Optional[str] = None
    status: str
    status_history: list = []
    platform: Optional[str] = None
    notes: Optional[str] = None
    screenshots: list = []
    applied_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    """Request schema for manually updating an application."""
    status: Optional[str] = Field(None, examples=["interview_scheduled", "rejected"])
    notes: Optional[str] = Field(None, examples=["Phone screen scheduled for Friday"])
    platform: Optional[str] = None
