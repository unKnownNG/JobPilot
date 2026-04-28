# =============================================================================
# api/jobs.py — Job Posting Endpoints
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.job_posting import JobPosting
from app.schemas.job import JobCreate, JobResponse, JobStatusUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "",
    response_model=list[JobResponse],
    summary="List discovered jobs",
)
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    min_score: Optional[float] = Query(None, description="Minimum relevance score"),
    limit: int = Query(50, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all job postings for the current user.
    
    Supports filtering by status, source, and minimum relevance score.
    Uses pagination (limit/offset) to handle large result sets.
    
    WHAT IS PAGINATION?
    Instead of returning ALL 10,000 jobs at once (slow!), we return them
    in chunks: "give me jobs 0-50", then "give me jobs 50-100", etc.
    """
    
    # Build the query dynamically based on filters
    query = select(JobPosting).where(JobPosting.user_id == current_user.id)
    
    if status_filter:
        query = query.where(JobPosting.status == status_filter)
    if source:
        query = query.where(JobPosting.source == source)
    if min_score is not None:
        query = query.where(JobPosting.relevance_score >= min_score)
    
    query = query.order_by(JobPosting.discovered_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [JobResponse.model_validate(job) for job in jobs]


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a job posting",
)
async def create_job(
    data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually add a job posting (useful for jobs you found yourself)."""
    
    job = JobPosting(
        user_id=current_user.id,
        title=data.title,
        company=data.company,
        location=data.location,
        url=data.url,
        description=data.description,
        source=data.source,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        work_type=data.work_type,
    )
    db.add(job)
    await db.flush()
    
    return JobResponse.model_validate(job)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a specific job posting."""
    
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.user_id == current_user.id,  # Security: only your own jobs
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)


@router.put(
    "/{job_id}/status",
    response_model=JobResponse,
    summary="Update job status (approve/reject)",
)
async def update_job_status(
    job_id: str,
    data: JobStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject a discovered job.
    
    When you approve a job, the orchestrator will queue it for:
    1. Resume tailoring (Tailor Agent)
    2. Application submission (Applier Agent)
    """
    
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    valid_statuses = ["discovered", "approved", "rejected", "applied", "expired"]
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    
    job.status = data.status
    db.add(job)
    await db.flush()
    
    return JobResponse.model_validate(job)


@router.get(
    "/stats/summary",
    summary="Get job discovery statistics",
)
async def get_job_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary statistics about discovered jobs."""
    
    # Count jobs by status
    result = await db.execute(
        select(JobPosting.status, func.count(JobPosting.id))
        .where(JobPosting.user_id == current_user.id)
        .group_by(JobPosting.status)
    )
    
    stats = {row[0]: row[1] for row in result.all()}
    total = sum(stats.values())
    
    return {
        "total": total,
        "by_status": stats,
    }
