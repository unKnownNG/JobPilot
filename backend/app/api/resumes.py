# =============================================================================
# api/resumes.py — Resume Management Endpoints
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.resume_parser import extract_text_from_file, parse_resume_with_llm
from app.dependencies import get_current_user
from app.models.user import User
from app.models.resume import MasterResume
from app.schemas.resume import ResumeCreate, ResumeResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])


async def _deactivate_existing(user_id: str, db: AsyncSession):
    """Deactivate all existing active resumes for a user."""
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.user_id == user_id,
            MasterResume.is_active == True,  # noqa: E712
        )
    )
    for r in result.scalars().all():
        r.is_active = False
        db.add(r)


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume file (PDF, DOCX, TXT)",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file: PDF, DOCX, or TXT"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file. The system will:
    1. Extract all text from the file (PDF, DOCX, or TXT)
    2. Send the text to the LLM to parse into structured data
    3. Save as the new active master resume

    The previous active resume (if any) will be deactivated.
    """
    # Validate file type
    filename = file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in [".pdf", ".docx", ".txt", ".md"]):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file.",
        )

    # Validate file size (max 10MB)
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Step 1: Extract raw text
    try:
        raw_text = extract_text_from_file(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if len(raw_text.strip()) < 100:
        raise HTTPException(
            status_code=422,
            detail="Could not extract enough text from the file. Make sure the PDF is not image-only.",
        )

    # Step 2: Parse with LLM
    try:
        parsed_data = await parse_resume_with_llm(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

    # Step 3: Save to database
    await _deactivate_existing(current_user.id, db)

    resume = MasterResume(
        user_id=current_user.id,
        resume_data=parsed_data,
        raw_text=raw_text[:10000],  # Store first 10k chars of raw text
        is_active=True,
    )
    db.add(resume)
    await db.flush()

    return ResumeResponse.model_validate(resume)




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
