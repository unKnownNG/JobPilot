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
from app.agents.tailor import run_tailor
from app.agents.applier import run_applier

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post(
    "/scout/run",
    summary="Run the Scout Agent to discover new jobs",
)
async def trigger_scout(
    min_score: float = Query(60.0, description="Minimum relevance score (0-100)"),
    search_term: Optional[str] = Query("", description="Job search query (e.g. 'Python developer'). Leave empty to use your resume title."),
    max_jobs: int = Query(25, le=100, description="Max jobs to fetch per source"),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the Scout Agent. It scrapes LinkedIn, Indeed, Glassdoor, and
    ZipRecruiter using your resume's title and location, then uses AI to
    score each job and saves the best matches.
    """
    try:
        result = await run_scout(
            user_id=current_user.id,
            min_score=min_score,
            search_term=search_term or "",
            max_jobs=max_jobs,
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scout agent failed: {str(e)}")


@router.post(
    "/tailor/run",
    summary="Run the Tailor Agent to customize resumes for approved jobs",
)
async def trigger_tailor(
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger the Tailor Agent.
    It finds all jobs you've approved, rewrites your resume bullets using AI
    to match each job description, and saves tailored versions.
    """
    try:
        result = await run_tailor(user_id=current_user.id)
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tailor agent failed: {str(e)}")


@router.post(
    "/applier/run",
    summary="Run the Applier Agent to auto-apply to jobs",
)
async def trigger_applier(
    max_applications: int = Query(5, le=20, description="Max applications to submit in one run"),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the Applier Agent. Opens job URLs in a headless browser,
    finds Apply buttons, fills forms, and takes screenshots.
    Only processes applications with status 'resume_ready'.
    """
    try:
        result = await run_applier(user_id=current_user.id, max_applications=max_applications)
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Applier agent failed: {str(e)}")


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
