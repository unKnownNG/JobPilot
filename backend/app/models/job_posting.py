# =============================================================================
# job_posting.py — Job Posting Database Model
# =============================================================================
# This table stores every job discovered by the Scout Agent.
# Each job goes through a lifecycle: discovered → approved/rejected → applied
# =============================================================================

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobPosting(Base):
    """
    A job posting discovered by the Scout Agent.
    
    Status lifecycle:
        "discovered" → Job found by scout, pending user review
        "approved"   → User wants to apply to this job
        "rejected"   → User doesn't want this job (hidden from feed)
        "applied"    → Application has been submitted
        "expired"    → Job listing is no longer active
    """
    
    __tablename__ = "job_postings"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # --- Job Details ---
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Structured requirements extracted by the Tailor Agent's JD parser
    # {"required_skills": ["Python", "SQL"], "nice_to_have": ["Docker"], "experience_years": 3}
    requirements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # How relevant this job is to the user (0-100, scored by LLM)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Where did we find this job? "linkedin", "indeed", "glassdoor", etc.
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    
    # Lifecycle status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="discovered",
        index=True,  # Index for fast filtering by status
    )
    
    # Salary info (if available)
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Job type: "remote", "hybrid", "onsite"
    work_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    def __repr__(self):
        return f"<JobPosting '{self.title}' at {self.company}>"
