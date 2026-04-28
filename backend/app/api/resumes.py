# =============================================================================
# api/resumes.py — Resume Management Endpoints
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.resume import MasterResume
from app.schemas.resume import ResumeCreate, ResumeResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a master resume",
)
async def create_resume(
    data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new master resume from structured JSON data.
    
    This is the "source of truth" resume that the Tailor Agent will customize
    for each job posting. Store your complete experience here — the AI will
    select and reword the most relevant parts per job.
    
    The previous active resume (if any) will be deactivated.
    """
    
    # Deactivate any existing active resumes
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.user_id == current_user.id,
            MasterResume.is_active == True,  # noqa: E712
        )
    )
    existing_resumes = result.scalars().all()
    for r in existing_resumes:
        r.is_active = False
        db.add(r)
    
    # Create new resume
    resume = MasterResume(
        user_id=current_user.id,
        resume_data=data.resume_data.model_dump(),
        raw_text=data.raw_text,
        is_active=True,
    )
    db.add(resume)
    await db.flush()
    
    return ResumeResponse.model_validate(resume)


@router.get(
    "",
    response_model=list[ResumeResponse],
    summary="List all resumes",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all master resumes for the current user."""
    
    result = await db.execute(
        select(MasterResume)
        .where(MasterResume.user_id == current_user.id)
        .order_by(MasterResume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get(
    "/active",
    response_model=ResumeResponse,
    summary="Get the active resume",
)
async def get_active_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the currently active master resume."""
    
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.user_id == current_user.id,
            MasterResume.is_active == True,  # noqa: E712
        )
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No active resume found. Create one first.",
        )
    
    return ResumeResponse.model_validate(resume)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume by ID",
)
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific resume by ID."""
    
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return ResumeResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a master resume."""
    
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    await db.delete(resume)
