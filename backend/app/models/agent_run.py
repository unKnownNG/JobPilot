# =============================================================================
# agent_run.py — Agent Run Log Model
# =============================================================================
# Every time an agent runs (Scout searches, Tailor rewrites, etc.), we log it.
# This gives you a complete audit trail of what the AI did and when.
# =============================================================================

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentRun(Base):
    """
    Log of every agent execution.
    
    This is your "black box" recorder — if something goes wrong, you can
    see exactly what happened, when, and what the agent was thinking.
    
    agent_type values: "scout", "tailor", "applier", "sentinel"
    status values: "running", "completed", "failed"
    """
    
    __tablename__ = "agent_runs"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Which agent ran? "scout", "tailor", "applier", "sentinel"
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Current run status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="running",
    )
    
    # Configuration the agent used for this run
    # {"search_query": "Python developer", "sources": ["linkedin", "indeed"]}
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Results summary
    # {"jobs_found": 15, "jobs_scored": 15, "above_threshold": 8}
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error details if the run failed
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    def __repr__(self):
        return f"<AgentRun {self.agent_type} status={self.status}>"
