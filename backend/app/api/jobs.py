# =============================================================================
# api/jobs.py — Job Posting Endpoints
# =============================================================================

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.llm import llm_provider
from app.dependencies import get_current_user
from app.models.user import User
from app.models.job_posting import JobPosting
from app.models.resume import MasterResume
from app.schemas.job import JobCreate, JobResponse, JobStatusUpdate
from app.agents.scout import (
    build_resume_summary,
    score_single_job,
    strip_html,
    normalize_url,
)

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


# ─── Import Job from URL ────────────────────────────────────────────────────

class ImportUrlRequest(BaseModel):
    """Request body for importing a job from a URL the user found."""
    url: str = Field(..., description="URL of the job posting to import")
    auto_approve: bool = Field(True, description="Auto-approve so Tailor/Applier agents work on it immediately")


# System prompt for extracting job details from raw HTML/text
_EXTRACT_SYSTEM = """You are an expert at parsing job postings from web pages.
You receive raw page text (HTML stripped to text) and must extract structured job data.
Return ONLY valid JSON — no markdown, no explanation."""

_EXTRACT_PROMPT = """Extract job posting details from this web page text.

PAGE URL: {url}

PAGE CONTENT:
{content}

Return ONLY a JSON object with these fields (use empty string "" if not found):
{{
  "title": "<job title>",
  "company": "<company name>",
  "location": "<job location>",
  "description": "<full job description text>",
  "work_type": "<remote|hybrid|onsite>",
  "salary_min": <number or null>,
  "salary_max": <number or null>
}}"""


async def _scrape_and_extract(url: str) -> dict:
    """
    Fetch a job URL and use LLM to extract structured job data.

    This approach (LLM-based extraction) is more robust than per-site
    CSS selectors — it works on any job board.
    """
    import re
    from html import unescape

    # 1. Fetch the page
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            raw_html = resp.text
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not fetch URL (HTTP {e.response.status_code}). The site may be blocking automated access.",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {str(e)}")

    # 2. Strip HTML to plain text and truncate for LLM context
    text = re.sub(r"<script[^>]*>.*?</script>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    page_text = text[:6000]  # Keep enough context for the LLM

    # 3. Use LLM to extract structured job data
    prompt = _EXTRACT_PROMPT.format(url=url, content=page_text)
    result = await llm_provider.generate_json(
        prompt=prompt,
        system_prompt=_EXTRACT_SYSTEM,
        model="openai-large",
    )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=422,
            detail="Could not extract job details from this page. Try adding the job manually instead.",
        )

    # Ensure required fields
    title = result.get("title", "").strip()
    company = result.get("company", "").strip()
    if not title or not company:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract job title or company from the page. Got title='{title}', company='{company}'. Try adding manually.",
        )

    return {
        "title": title,
        "company": company,
        "location": result.get("location", "") or "",
        "description": result.get("description", "") or "",
        "work_type": result.get("work_type", "onsite") or "onsite",
        "salary_min": result.get("salary_min"),
        "salary_max": result.get("salary_max"),
    }


@router.post(
    "/import-url",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a job from a URL (scrape + score + save)",
)
async def import_job_from_url(
    data: ImportUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import a job posting by pasting a URL. The system will:
    1. Fetch the page and extract job details using AI
    2. Score it against your resume
    3. Save it (auto-approved by default so Tailor/Applier agents work on it)
    """
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    # Check for duplicate
    existing = await db.execute(
        select(JobPosting).where(
            JobPosting.user_id == current_user.id,
            JobPosting.url == url,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This job URL has already been imported.")

    # 1. Scrape and extract job details
    job_data = await _scrape_and_extract(url)

    # 2. Score against resume (if available)
    relevance_score = None
    try:
        res = await db.execute(
            select(MasterResume).where(
                MasterResume.user_id == current_user.id,
                MasterResume.is_active == True,
            )
        )
        resume = res.scalar_one_or_none()
        if resume and resume.resume_data:
            resume_text = build_resume_summary(resume.resume_data)
            score_result = await score_single_job(
                title=job_data["title"],
                desc=job_data["description"][:800],
                resume=resume_text,
            )
            relevance_score = score_result.get("score", 0)
    except Exception as e:
        print(f"[IMPORT-URL] Scoring failed (non-fatal): {e}")

    # 3. Save the job posting
    job_status = "approved" if data.auto_approve else "discovered"
    job = JobPosting(
        user_id=current_user.id,
        title=job_data["title"],
        company=job_data["company"],
        location=job_data["location"],
        url=url,
        description=job_data["description"],
        source="user_link",
        work_type=job_data["work_type"],
        salary_min=job_data["salary_min"],
        salary_max=job_data["salary_max"],
        relevance_score=round(relevance_score, 1) if relevance_score else None,
        status=job_status,
    )
    db.add(job)
    await db.flush()

    print(f"[IMPORT-URL] Imported: '{job_data['title']}' @ {job_data['company']} | score={relevance_score} | status={job_status}")
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


# ─── Tailor Resume Prompt ───────────────────────────────────────────────────

_TAILOR_SYSTEM = """You are a world-class technical career coach and LaTeX resume expert.
Your task is to write an extremely detailed, job-specific prompt that a user can paste — along with their LaTeX resume — into Claude to get a perfectly tailored resume.

The prompt you produce should:
1. Analyse the job posting's requirements, tech stack, seniority, and culture signals
2. Give Claude precise, actionable instructions on what to emphasise, reword, reorder, or add
3. List the specific keywords and skills from the JD that must appear naturally in the resume
4. Specify any structural changes (e.g. move skills section higher, expand or condense bullet points)
5. Remind Claude to preserve LaTeX formatting and never invent fake experience
Write the prompt in second-person, as if you are instructing Claude directly.
Output ONLY the prompt text — no preamble, no markdown headers."""

_TAILOR_USER = """Generate a resume-tailoring prompt for this job posting.

JOB TITLE: {title}
COMPANY: {company}
LOCATION: {location}
WORK TYPE: {work_type}
RELEVANCE SCORE AGAINST MY CURRENT RESUME: {score}%

JOB DESCRIPTION:
{description}

PARSED REQUIREMENTS (if available):
{requirements}

Remember: your output is a prompt that will be pasted into Claude along with my LaTeX resume.
Make it specific, detailed, and actionable."""


class TailorPromptResponse(BaseModel):
    """Response containing the AI-generated resume tailoring prompt."""
    prompt: str
    job_title: str
    company: str


@router.post(
    "/{job_id}/tailor-prompt",
    response_model=TailorPromptResponse,
    summary="Generate a Claude resume-tailoring prompt for a specific job",
)
async def generate_tailor_prompt(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Use Claude Sonnet (via Pollinations AI) to generate a rich, job-specific
    resume-tailoring prompt. The user copies this prompt and pastes it into
    Claude.ai alongside their LaTeX resume to get a perfectly tailored version.
    """
    # Fetch the job
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build the user message for Claude Sonnet
    requirements_text = "Not parsed yet."
    if job.requirements:
        req = job.requirements
        parts = []
        if req.get("required_skills"):
            parts.append("Required skills: " + ", ".join(req["required_skills"]))
        if req.get("nice_to_have"):
            parts.append("Nice-to-have: " + ", ".join(req["nice_to_have"]))
        if req.get("experience_years"):
            parts.append(f"Experience: {req['experience_years']} years")
        if parts:
            requirements_text = "\n".join(parts)

    user_msg = _TAILOR_USER.format(
        title=job.title,
        company=job.company,
        location=job.location or "Not specified",
        work_type=job.work_type or "Not specified",
        score=round(job.relevance_score, 1) if job.relevance_score else "N/A",
        description=(job.description or "No description available.")[:4000],
        requirements=requirements_text,
    )

    try:
        generated_prompt = await llm_provider.generate(
            prompt=user_msg,
            system_prompt=_TAILOR_SYSTEM,
            model="claude-sonnet",  # Claude Sonnet via Pollinations AI
            temperature=0.6,
        )
    except Exception as e:
        print(f"[TAILOR-PROMPT] Claude Sonnet failed, falling back: {e}")
        # Fallback to openai-large if claude-sonnet is unavailable
        try:
            generated_prompt = await llm_provider.generate(
                prompt=user_msg,
                system_prompt=_TAILOR_SYSTEM,
                model="openai-large",
                temperature=0.6,
            )
        except Exception as e2:
            raise HTTPException(
                status_code=503,
                detail=f"AI model unavailable. Please try again shortly. ({e2})",
            )

    print(f"[TAILOR-PROMPT] Generated prompt for '{job.title}' @ {job.company} (len={len(generated_prompt)})")

    return TailorPromptResponse(
        prompt=generated_prompt.strip(),
        job_title=job.title,
        company=job.company,
    )


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
