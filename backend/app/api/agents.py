# =============================================================================
# api/agents.py — Agent Control Endpoints
# =============================================================================
# Endpoints to manually trigger AI agents and check their run history.
# The Applier Agent uses an extension-based architecture with 3 endpoints:
#   - /applier/autofill-data  → Get resume data for form filling
#   - /applier/analyze-form   → LLM analyzes form HTML and maps fields
#   - /applier/log            → Extension reports back what it applied to
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.agent_run import AgentRun
from app.agents.scout import run_scout
from app.agents.tailor import run_tailor
from app.agents.applier import (
    analyze_form_fields,
    get_autofill_data,
    log_application_from_extension,
)

router = APIRouter(prefix="/agents", tags=["Agents"])


# ─── Scout Agent ─────────────────────────────────────────────────────────────

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


# ─── Tailor Agent ────────────────────────────────────────────────────────────

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


# ─── Applier Agent (Extension-Based) ────────────────────────────────────────

class FormField(BaseModel):
    """A single form field scraped by the Chrome Extension."""
    selector: str = Field(..., description="CSS selector to target this field")
    field_type: str = Field("text", description="input, select, textarea, radio, checkbox, file")
    name: str = Field("", description="The field's name attribute")
    label: str = Field("", description="Associated label text")
    placeholder: str = Field("", description="Placeholder text")
    required: bool = Field(False)
    options: Optional[list[dict]] = Field(None, description="For select/radio: [{value, label}]")


class AnalyzeFormRequest(BaseModel):
    """Request body for the form analysis endpoint."""
    form_fields: list[FormField]
    job_url: str = Field("", description="URL of the job page")
    job_title: str = Field("", description="Title of the job")
    company: str = Field("", description="Company name")
    job_description: str = Field("", description="Job description text (first ~500 chars)")


class LogApplicationRequest(BaseModel):
    """Request body for logging a completed application."""
    job_url: str
    job_title: str = ""
    company: str = ""
    status: str = Field("applied", description="applied, failed_to_apply, partially_filled")
    fields_filled: list[str] = Field(default_factory=list)
    notes: str = ""


@router.get(
    "/applier/autofill-data",
    summary="Get resume data for form autofill (used by Chrome Extension)",
)
async def get_autofill(
    job_id: Optional[str] = Query(None, description="Job posting ID (uses tailored resume if available)"),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the user's resume data in a flat, autofill-friendly format.
    The Chrome Extension calls this to get the data it needs to fill forms.

    If a job_id is provided and a tailored resume exists for that job,
    the tailored version is used instead of the master resume.
    """
    result = await get_autofill_data(
        user_id=current_user.id,
        job_id=job_id,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post(
    "/applier/analyze-form",
    summary="Analyze a job application form using AI (used by Chrome Extension)",
)
async def analyze_form(
    data: AnalyzeFormRequest,
    current_user: User = Depends(get_current_user),
):
    """
    The Chrome Extension sends the scraped form fields from a job application page.
    The backend uses an LLM to intelligently map the user's resume data to each
    form field and returns fill instructions.

    Flow:
    1. Extension scrapes all <input>, <select>, <textarea> from the page
    2. Sends them here as a list of FormField objects
    3. Backend fetches the user's resume and calls the LLM
    4. Returns a mapping: {selector → value} for the extension to fill
    """
    # Get resume data
    autofill = await get_autofill_data(user_id=current_user.id)
    if "error" in autofill:
        raise HTTPException(status_code=404, detail=autofill["error"])

    # Convert FormField objects to dicts for the LLM
    fields_for_llm = [f.model_dump() for f in data.form_fields]

    result = await analyze_form_fields(
        form_fields=fields_for_llm,
        resume_data=autofill,
        job_title=data.job_title,
        company=data.company,
        job_description=data.job_description,
    )

    return result


@router.post(
    "/applier/log",
    summary="Log a completed application (used by Chrome Extension)",
)
async def log_application(
    data: LogApplicationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    After the Chrome Extension fills out and/or submits a form,
    it calls this endpoint to log the application in the dashboard.

    This creates/updates both a JobPosting (if new) and an Application record.
    """
    result = await log_application_from_extension(
        user_id=current_user.id,
        job_url=data.job_url,
        job_title=data.job_title,
        company=data.company,
        status=data.status,
        fields_filled=data.fields_filled,
        notes=data.notes,
    )
    return result


# ─── Agent Run History ───────────────────────────────────────────────────────

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
