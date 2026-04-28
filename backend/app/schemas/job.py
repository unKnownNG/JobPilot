# =============================================================================
# schemas/job.py — Job Posting Schemas
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Request schema for manually adding a job posting."""
    title: str = Field(..., examples=["Senior Python Developer"])
    company: str = Field(..., examples=["Google"])
    location: Optional[str] = Field(None, examples=["Remote"])
    url: str = Field(..., examples=["https://careers.google.com/jobs/123"])
    description: Optional[str] = None
    source: str = Field("manual", examples=["manual", "linkedin", "indeed"])
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    work_type: Optional[str] = Field(None, examples=["remote", "hybrid", "onsite"])


class JobResponse(BaseModel):
    """Response schema for job postings."""
    id: str
    user_id: str
    title: str
    company: str
    location: Optional[str] = None
    url: str
    description: Optional[str] = None
    requirements: Optional[dict] = None
    relevance_score: Optional[float] = None
    source: str
    status: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    work_type: Optional[str] = None
    discovered_at: datetime
    
    model_config = {"from_attributes": True}


class JobStatusUpdate(BaseModel):
    """Request schema for updating a job's status (approve/reject)."""
    status: str = Field(
        ...,
        description="New status for the job",
        examples=["approved", "rejected"],
    )
