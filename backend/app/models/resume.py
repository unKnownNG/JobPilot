# =============================================================================
# resume.py — Resume Database Models
# =============================================================================
# Two models here:
#
# 1. MasterResume — Your "original" resume stored as structured JSON.
#    This is the source of truth that the Tailor Agent rewrites from.
#
# 2. TailoredResume — A job-specific version created by the Tailor Agent.
#    Links to both the master resume and a specific job posting.
# =============================================================================

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MasterResume(Base):
    """
    The master resume — your "base" resume that gets customized per job.
    
    Stored as structured JSON (not PDF) so the AI can easily read and modify it.
    The JSON follows a schema like:
    {
        "name": "Mo",
        "title": "Software Engineer",
        "summary": "...",
        "experience": [
            {"company": "Google", "role": "SWE", "bullets": ["Built X", "Led Y"]}
        ],
        "skills": ["Python", "FastAPI", "React"],
        "education": [...],
        "projects": [...]
    }
    """
    
    __tablename__ = "master_resumes"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Foreign Key — links this resume to a specific user
    # "users.id" means "the id column in the users table"
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # Delete resumes if user is deleted
        nullable=False,
    )
    
    # The structured resume data as JSON
    resume_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    
    # Raw text version (for full-text search and LLM context)
    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Only one resume can be "active" at a time
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    tailored_versions: Mapped[list["TailoredResume"]] = relationship(
        "TailoredResume", back_populates="master_resume", lazy="selectin"
    )
    
    def __repr__(self):
        return f"<MasterResume {self.id[:8]}... for user {self.user_id[:8]}...>"


class TailoredResume(Base):
    """
    A job-specific resume created by the Tailor Agent.
    
    Each tailored resume links to:
    - A master resume (the original it was based on)
    - A job posting (the job it was customized for)
    
    Stores both the modified JSON and file paths for the generated PDFs.
    """
    
    __tablename__ = "tailored_resumes"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    master_resume_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("master_resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    job_posting_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # The tailored resume content
    resume_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # What changed from the master? Stored as a JSON diff for the UI to display.
    diff_from_master: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # File paths (local filesystem)
    resume_pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_letter_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    master_resume: Mapped["MasterResume"] = relationship(
        "MasterResume", back_populates="tailored_versions"
    )
    
    def __repr__(self):
        return f"<TailoredResume {self.id[:8]}... for job {self.job_posting_id[:8]}...>"
