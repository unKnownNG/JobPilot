# =============================================================================
# schemas/resume.py — Resume Schemas
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResumeDataSchema(BaseModel):
    """
    The structured resume format. This is the JSON schema for master resumes.
    
    Using structured JSON instead of PDF because:
    1. The AI can read/modify it directly (no OCR or PDF parsing)
    2. Each section can be rewritten independently
    3. Easy to generate diffs (what changed in tailored version)
    """
    name: str = Field(..., examples=["Mohammed"])
    title: str = Field(..., examples=["Full Stack Developer"])
    summary: Optional[str] = Field(None, examples=["Passionate developer with 3 years..."])
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    
    skills: list[str] = Field(
        default_factory=list,
        examples=[["Python", "JavaScript", "React", "FastAPI", "SQL"]],
    )
    
    experience: list[dict] = Field(
        default_factory=list,
        examples=[[{
            "company": "TechCorp",
            "role": "Software Engineer",
            "start_date": "2022-01",
            "end_date": "present",
            "bullets": [
                "Built REST API serving 10K requests/day using FastAPI",
                "Reduced deployment time by 40% with CI/CD pipeline",
            ]
        }]],
    )
    
    education: list[dict] = Field(
        default_factory=list,
        examples=[[{
            "institution": "MIT",
            "degree": "B.S. Computer Science",
            "year": "2022",
        }]],
    )
    
    projects: list[dict] = Field(
        default_factory=list,
        examples=[[{
            "name": "Job Agent",
            "description": "AI-powered job application automation",
            "tech_stack": ["Python", "FastAPI", "React"],
            "url": "https://github.com/user/job-agent",
        }]],
    )
    
    certifications: list[str] = Field(default_factory=list)


class ResumeCreate(BaseModel):
    """Request schema for creating a new master resume."""
    resume_data: ResumeDataSchema
    raw_text: Optional[str] = Field(
        None,
        description="Optional raw text version of the resume",
    )


class ResumeResponse(BaseModel):
    """Response schema for resume data."""
    id: str
    user_id: str
    resume_data: dict
    raw_text: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
