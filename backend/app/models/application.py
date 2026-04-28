# =============================================================================
# application.py — Application Tracking Model
# =============================================================================
# This is the heart of the tracking system. Each row represents one job
# application and tracks its entire lifecycle from submission to offer/rejection.
# =============================================================================

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Application(Base):
    """
    Tracks a job application through its entire lifecycle.
    
    Status values (the state machine):
        "queued"              → Approved, waiting for resume tailoring
        "resume_ready"        → Tailored resume generated, ready to apply
        "applying"            → Applier agent is submitting the application
        "applied"             → Application submitted successfully
        "failed_to_apply"     → Submission failed (will retry)
        "under_review"        → Company is reviewing (detected from email/portal)
        "interview_scheduled" → Interview invite received
        "rejected"            → Rejection received
        "offer_received"      → Job offer extended
        "accepted"            → User accepted the offer
        "declined"            → User declined the offer
    """
    
    __tablename__ = "applications"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    job_posting_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    tailored_resume_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tailored_resumes.id", ondelete="SET NULL"),
        nullable=True,  # Might not have a tailored resume yet
    )
    
    # Current status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
        index=True,
    )
    
    # Full history of status changes — invaluable for debugging and analytics
    # [{"status": "queued", "at": "2024-01-15T10:30:00Z", "note": "User approved"},
    #  {"status": "applied", "at": "2024-01-15T11:00:00Z", "note": "Auto-applied via LinkedIn"}]
    status_history: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )
    
    # Which platform was this applied through? "linkedin", "greenhouse", "lever", etc.
    platform: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # User notes (personal comments about this application)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Screenshot file paths from the Applier agent (audit trail)
    # ["./data/storage/screenshots/app_123_step1.png", "...step2.png"]
    screenshots: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    last_status_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    job_posting: Mapped["JobPosting"] = relationship("JobPosting")
    
    def __repr__(self):
        return f"<Application {self.id[:8]}... status={self.status}>"
