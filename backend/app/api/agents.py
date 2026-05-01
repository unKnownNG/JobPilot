# =============================================================================
# api/agents.py — Agent Control Endpoints
# =============================================================================
# Endpoints to manually trigger AI agents and check their run history.
# =============================================================================

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.agent_run import AgentRun
from app.agents.scout import run_scout

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post(
    "/scout/run",
    summary="Run the Scout Agent to discover new jobs",
)
async def trigger_scout(
    min_score: float = Query(60.0, description="Minimum relevance score (0-100)"),
    categories: Optional[str] = Query(None, description="Comma-separated categories: software-dev,data,devops"),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger the Scout Agent.
    It will fetch jobs from remote job boards, score them against your resume
    using AI, and save matching jobs to your dashboard.
    """
    cats = categories.split(",") if categories else None

    try:
        result = await run_scout(
            user_id=current_user.id,
            categories=cats,
            min_score=min_score,
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scout agent failed: {str(e)}")


@router.get(
    "/runs",
    summary="List agent run history",
)
async def list_agent_runs(
    agent_type: Optional[str] = Query(None, description="Filter by agent type: scout, tailor, applier, sentinel"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the history of all agent runs for the current user."""
    query = select(AgentRun).where(AgentRun.user_id == current_user.id)
    if agent_type:
        query = query.where(AgentRun.agent_type == agent_type)
    query = query.order_by(AgentRun.started_at.desc()).limit(limit)

    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "agent_type": r.agent_type,
            "status": r.status,
            "config": r.config,
            "result": r.result,
            "started_at": str(r.started_at) if r.started_at else None,
            "completed_at": str(r.completed_at) if r.completed_at else None,
        }
        for r in runs
    ]
